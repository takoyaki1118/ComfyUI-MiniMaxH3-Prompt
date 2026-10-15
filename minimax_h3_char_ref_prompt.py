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


class MinimaxH3CharRefPromptGenerator:
    """キャラクターリファレンス参照型。"""

    @classmethod
    def INPUT_TYPES(s):
        required = {
            "summary_action": ("STRING", {"multiline": True, "default": "", "placeholder": "【動画全体の動き】"}),
            "camera_style": ("STRING", {"multiline": True, "default": "", "placeholder": "【カメラ・画作り】"}),
            "soundscape": ("STRING", {"multiline": True, "default": "", "placeholder": "【環境音・効果音】"}),
            "include_clothing": ("BOOLEAN", {"default": True, "label_on": "clothing enabled", "label_off": "clothing ignored"}),
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
        include_clothing, character_extra, enable_music, music_text,
        auto_speech_cue=True, subject_type="woman", **kw
    ):
        formatted_shots, names, fdialogues, total, warns = collect_from_kwargs(kw, auto_speech_cue)
        dialogue_output = dialogue_lines_only(fdialogues)

        if not formatted_shots:
            formatted_shots = ["[Shot 1] <Subject 1> appears in the scene."]
            names = ["[Shot 1]"]
            warns.append("有効なShotがないためフォールバック文を使用")

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(names)

        clothing_part = ", clothing" if include_clothing else ""
        extra = normalize_tags(character_extra.strip())
        char_extra_formatted = f" {extra}" if extra else ""

        final_music = resolve_music(enable_music, music_text)
        action = normalize_tags(summary_action.strip())
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"
        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""
        sound = soundscape.strip() or "N/A"

        prompt = f"""subject_definitions:
<Subject 1> is the {subject_type} depicted in the character reference images (<Picture 1>, showing full-body and close-up face views), maintaining the exact face, hair{clothing_part}, skin tone, and body proportions of the reference.{char_extra_formatted}
The reference images provide the definitive character design sheet for <Subject 1>.

summary: [character consistency generation] The target video generates a sequence featuring <Subject 1> based on the character reference images{action_str}. The appearance, facial features, and styling of <Subject 1> are strictly locked to the character reference.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - the exact face, hair{clothing_part}, and body proportions from the character reference images remain entirely consistent across all active shots; only expressions, poses, and movements change as described.

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt), dialogue_output, build_status(total, warns))
