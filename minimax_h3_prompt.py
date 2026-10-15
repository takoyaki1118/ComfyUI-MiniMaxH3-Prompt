try:
    from .common import (
        collect_from_kwargs, dialogue_lines_only, build_status, build_shot_inputs,
        resolve_music, clean_prompt, normalize_tags, SUBJECT_TYPES, POSSESSIVE,
    )
except ImportError:
    from common import (
        collect_from_kwargs, dialogue_lines_only, build_status, build_shot_inputs,
        resolve_music, clean_prompt, normalize_tags, SUBJECT_TYPES, POSSESSIVE,
    )


class MinimaxH3PromptGenerator:
    """ファーストフレーム参照型 (I2V + reference)。"""

    @classmethod
    def INPUT_TYPES(s):
        required = {
            "summary_action": ("STRING", {"multiline": True, "default": "", "placeholder": "【動画全体の動き】"}),
            "camera_style": ("STRING", {"multiline": True, "default": "", "placeholder": "【カメラ・画作り】"}),
            "soundscape": ("STRING", {"multiline": True, "default": "", "placeholder": "【環境音・効果音】"}),
            "subject1_extra": ("STRING", {"multiline": True, "default": "", "placeholder": "【人物の補足（任意）】"}),
            "has_male": ("BOOLEAN", {"default": False}),
            "male_role": ("STRING", {"default": "", "placeholder": "【男性の役割】"}),
            "male_retention_desc": ("STRING", {"default": "", "placeholder": "【男性の保持設定】"}),
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
        subject1_extra, has_male, male_role, male_retention_desc,
        enable_music, music_text,
        auto_speech_cue=True, subject_type="woman", **kw
    ):
        formatted_shots, names, fdialogues, total, warns = collect_from_kwargs(kw, auto_speech_cue)
        dialogue_output = dialogue_lines_only(fdialogues)

        if not formatted_shots:
            formatted_shots = ["[Shot 1] The shot begins from <Picture 1>."]
            names = ["[Shot 1]"]
            warns.append("有効なShotがないためフォールバック文を使用")

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(names)

        poss = POSSESSIVE.get(subject_type, "their")
        extra = normalize_tags(subject1_extra.strip())
        sub1_extra_formatted = f" {extra}" if extra else ""

        if has_male:
            role = male_role.strip() or "male POV hands visible in frame"
            retention = male_retention_desc.strip() or \
                "partially_preserved - hands interacting naturally with <Subject 1>"
            male_def_str = f"\n<Subject 2> is the {role} visible in <Picture 1> (or introduced from the image)."
            male_ret_str = f"\n<Subject 2> (appears in {shot_list_str}): {retention}"
        else:
            male_def_str = ""
            male_ret_str = ""

        final_music = resolve_music(enable_music, music_text)
        action = normalize_tags(summary_action.strip())
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"
        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""
        sound = soundscape.strip() or "N/A"

        prompt = f"""subject_definitions:
<Subject 1> is the {subject_type} in <Picture 1>, with the exact face, the exact hair, the exact clothing, skin tone, and body proportions of <Picture 1>.{sub1_extra_formatted}
<Picture 1> is the first frame of [Shot 1], showing <Subject 1> in the exact pose, framing, and composition of the reference image.{male_def_str}

summary: [keyframe completion + reference generation] The target video starts from the exact first frame of <Picture 1> and continues forward as a continuous video{action_str}. The appearance, pose, and framing of <Subject 1> at the beginning are locked to <Picture 1>.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - {poss} face, hair, clothing, skin tone, and body from <Picture 1> remain constant throughout; only expression, pose, and movement change as described.
<Picture 1> ([Shot 1] first frame): fully_preserved - the target video opens on the exact composition, pose, framing, lighting, and subject appearance of <Picture 1>.{male_ret_str}

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt), dialogue_output, build_status(total, warns))
