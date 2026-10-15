try:
    from .common import (
        collect_from_kwargs, dialogue_lines_only, build_status, build_shot_inputs,
        resolve_music, clean_prompt, normalize_tags, SUBJECT_TYPES,
    )
except ImportError:
    from common import (
        collect_from_kwargs, dialogue_lines_only, build_status, build_shot_inputs,
        resolve_music, clean_prompt, normalize_tags, SUBJECT_TYPES,
    )

# 保存済みワークフロー互換のため、値は短いキーにしている（説明は tooltip）
CLOTHING_SOURCES = ["character_ref", "first_frame", "ignore"]
CLOTHING_TOOLTIP = (
    "character_ref: 服装も <Picture 1> に合わせる / "
    "first_frame: 服装は <Picture 2>、顔・髪は <Picture 1> / ignore: 服装に言及しない"
)


class MinimaxH3CharRefFirstFramePromptGenerator:
    """キャラクターリファレンス + ファーストフレーム指定型。"""

    @classmethod
    def INPUT_TYPES(s):
        required = {
            "summary_action": ("STRING", {"multiline": True, "default": "", "placeholder": "【動画全体の動き】"}),
            "camera_style": ("STRING", {"multiline": True, "default": "", "placeholder": "【カメラ・画作り】"}),
            "soundscape": ("STRING", {"multiline": True, "default": "", "placeholder": "【環境音・効果音】"}),
            "clothing_source": (CLOTHING_SOURCES, {"default": "character_ref", "tooltip": CLOTHING_TOOLTIP}),
            "character_extra": ("STRING", {"multiline": True, "default": "", "placeholder": "【キャラクターの補足】"}),
            "enable_music": ("BOOLEAN", {"default": False}),
            "music_text": ("STRING", {"multiline": True, "default": "", "placeholder": "【BGM】"}),
        }
        required.update(build_shot_inputs())
        return {
            "required": required,
            "optional": {
                "auto_speech_cue": ("BOOLEAN", {"default": True}),
                "subject_type": (SUBJECT_TYPES, {"default": "woman"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("prompt", "dialogue", "status")
    FUNCTION = "generate_prompt"
    CATEGORY = "MiniMaxH3"

    def generate_prompt(
        self, summary_action, camera_style, soundscape,
        clothing_source, character_extra, enable_music, music_text,
        auto_speech_cue=True, subject_type="woman", **kw
    ):
        formatted_shots, names, fdialogues, total, warns = collect_from_kwargs(kw, auto_speech_cue)
        dialogue_output = dialogue_lines_only(fdialogues)

        if not formatted_shots:
            formatted_shots = ["[Shot 1] The shot begins from <Picture 2>."]
            names = ["[Shot 1]"]
            warns.append("有効なShotがないためフォールバック文を使用")

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(names)

        # 旧表記 ("character_ref (<Picture 1>)" 等) も startswith で受ける
        if clothing_source.startswith("character_ref"):
            clothing_def = "face, hair, clothing, skin tone, and body proportions of the reference character (<Picture 1>)"
            clothing_retention = "face, hair, clothing, skin tone, and body proportions from <Picture 1>"
        elif clothing_source.startswith("first_frame"):
            clothing_def = "face, hair, and skin tone of the reference (<Picture 1>), but the clothing of the starting frame (<Picture 2>)"
            clothing_retention = "face, hair, and body from <Picture 1>, and clothing from <Picture 2>"
        else:
            clothing_def = "face, hair, skin tone, and body proportions of the reference (<Picture 1>)"
            clothing_retention = "face, hair, and body proportions from <Picture 1>"

        extra = normalize_tags(character_extra.strip())
        char_extra_formatted = f" {extra}" if extra else ""

        final_music = resolve_music(enable_music, music_text)
        action = normalize_tags(summary_action.strip())
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"
        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""
        sound = soundscape.strip() or "N/A"

        prompt = f"""subject_definitions:
<Subject 1> is the {subject_type} depicted in the character reference images (<Picture 1>, showing full-body and close-up face views), maintaining the exact {clothing_def}.{char_extra_formatted}
<Picture 1> provides the definitive character design sheet for <Subject 1>.
<Picture 2> is the first frame of [Shot 1], showing <Subject 1> (the same person as defined in <Picture 1>) in the exact pose, framing, and composition of the starting reference image.

summary: [character consistency generation + keyframe completion] The target video starts from the exact first frame of <Picture 2> and continues forward as a continuous video{action_str}. The facial features and styling of <Subject 1> are locked to the character reference (<Picture 1>), while the initial pose, framing, and composition are locked to <Picture 2>.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - the exact {clothing_retention} remain entirely consistent across all active shots; only expressions, poses, and movements change as described.
<Picture 2> ([Shot 1] first frame): fully_preserved - the target video opens on the exact composition, pose, framing, and lighting of <Picture 2> (excluding subject identity mapping).

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt), dialogue_output, build_status(total, warns))
