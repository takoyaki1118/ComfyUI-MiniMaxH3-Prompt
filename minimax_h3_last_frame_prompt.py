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

LANDING = (
    "The shot ends exactly on the composition, pose, framing, and lighting of <Picture 1>."
)


class MinimaxH3LastFramePromptGenerator:
    """L2VA: ラストフレームのみ指定。妥当な先行状態から始まり、最終ショット末尾で <Picture 1> に着地する。"""

    @classmethod
    def INPUT_TYPES(s):
        required = {
            "summary_action": ("STRING", {
                "multiline": True, "default": "",
                "placeholder": "【動画全体の動き】最終フレームに至るまでの行動を一文で"}),
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
                "auto_speech_cue": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "ON: セリフがあるShotの末尾に発話キューを自動付与"}),
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
            formatted_shots = ["[Shot 1] The scene develops toward the final composition."]
            names = ["[Shot 1]"]
            warns.append("有効なShotがないためフォールバック文を使用")

        # 最終ショットに着地フレーズを自動付与（<Picture 1> が未記載の場合のみ）
        if "<Picture 1>" not in formatted_shots[-1]:
            formatted_shots[-1] = f"{formatted_shots[-1]} {LANDING}"

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(names)
        final_shot_name = names[-1]

        poss = POSSESSIVE.get(subject_type, "their")
        extra = normalize_tags(subject1_extra.strip())
        sub1_extra_formatted = f" {extra}" if extra else ""

        if has_male:
            role = male_role.strip() or "male POV hands visible in frame"
            retention = male_retention_desc.strip() or \
                "partially_preserved - hands interacting naturally with <Subject 1>"
            male_def_str = f"\n<Subject 2> is the {role} visible in <Picture 1> (or introduced earlier)."
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
<Picture 1> is the last frame of {final_shot_name}, showing <Subject 1> in the exact final pose, framing, composition, and lighting of the reference image.{male_def_str}

summary: [keyframe completion] The target video begins from a plausible preceding state and develops continuously{action_str}, gradually converging so that the final moment of {final_shot_name} lands exactly on <Picture 1>. The appearance, pose, and framing of <Subject 1> at the end are locked to <Picture 1>.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - {poss} face, hair, clothing, skin tone, and body from <Picture 1> remain constant throughout; only expression, pose, and movement change as described until the final frame.
<Picture 1> ({final_shot_name} last frame): fully_preserved - the target video ends on the exact composition, pose, framing, lighting, and subject appearance of <Picture 1>.{male_ret_str}

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt), dialogue_output, build_status(total, warns))
