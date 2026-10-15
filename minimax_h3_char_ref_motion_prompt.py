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

VIDEO_REF_SUFFIX = "(following the motion and timing of <Video 1>)"


class MinimaxH3CharRefMotionPromptGenerator:
    """キャラクターリファレンス + 参照動画（モーション）型。"""

    @classmethod
    def INPUT_TYPES(s):
        required = {
            "summary_action": ("STRING", {"multiline": True, "default": "", "placeholder": "【動画全体の動き】"}),
            "camera_style": ("STRING", {"multiline": True, "default": "", "placeholder": "【カメラ・画作り】"}),
            "soundscape": ("STRING", {"multiline": True, "default": "", "placeholder": "【環境音・効果音】"}),
            "include_clothing": ("BOOLEAN", {"default": True, "label_on": "clothing enabled", "label_off": "clothing ignored"}),
            "use_motion_video": ("BOOLEAN", {"default": False, "label_on": "motion video enabled", "label_off": "no motion video"}),
            "motion_video_desc": ("STRING", {"multiline": True, "default": "", "placeholder": "【参照動画の動き】"}),
            "character_extra": ("STRING", {"multiline": True, "default": "", "placeholder": "【キャラクターの補足】"}),
            "enable_music": ("BOOLEAN", {"default": False}),
            "music_text": ("STRING", {"multiline": True, "default": "", "placeholder": "【BGM】"}),
        }
        required.update(build_shot_inputs())
        return {
            "required": required,
            "optional": {
                "auto_append_video_ref": ("BOOLEAN", {"default": True}),
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
        include_clothing, use_motion_video, motion_video_desc,
        character_extra, enable_music, music_text,
        auto_append_video_ref=True, auto_speech_cue=True, subject_type="woman", **kw
    ):
        use_video = bool(use_motion_video)
        formatted_shots, names, fdialogues, total, warns = collect_from_kwargs(
            kw, auto_speech_cue,
            append_suffix=VIDEO_REF_SUFFIX if (use_video and auto_append_video_ref) else None,
            skip_if_contains="<Video 1>",
        )
        dialogue_output = dialogue_lines_only(fdialogues)

        if not formatted_shots:
            fallback = "[Shot 1] <Subject 1> appears in the scene."
            if use_video:
                fallback += " The movement follows <Video 1>."
            formatted_shots = [fallback]
            names = ["[Shot 1]"]
            warns.append("有効なShotがないためフォールバック文を使用")

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(names)

        clothing_part = ", clothing" if include_clothing else ""
        extra = normalize_tags(character_extra.strip())
        char_extra_formatted = f" {extra}" if extra else ""
        final_music = resolve_music(enable_music, music_text)

        if use_video:
            desc = normalize_tags(motion_video_desc.strip())
            desc_part = f" {desc}" if desc else ""
            video_def = (
                "\n<Video 1> is the motion reference video that provides the body movement, "
                "timing, camera movement, and action rhythm to be followed by <Subject 1>."
                f"{desc_part}"
            )
            task_type = "[character consistency generation + reference generation]"
            summary_extra = ", while the movements, timing, and camera work are guided by <Video 1>"
            retention_video = (
                "\n<Video 1> (motion, timing, and camera structure): partially_preserved - "
                "the body movements, action timing, and overall rhythm of <Video 1> are followed "
                "as closely as possible, while the character appearance is replaced by <Subject 1>."
            )
        else:
            video_def = ""
            task_type = "[character consistency generation]"
            summary_extra = ""
            retention_video = ""

        action = normalize_tags(summary_action.strip())
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"
        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""
        sound = soundscape.strip() or "N/A"

        prompt = f"""subject_definitions:
<Subject 1> is the {subject_type} depicted in the character reference images (<Picture 1>, showing full-body and close-up face views), maintaining the exact face, hair{clothing_part}, skin tone, and body proportions of the reference.{char_extra_formatted}
The reference images provide the definitive character design sheet for <Subject 1>.{video_def}

summary: {task_type} The target video features <Subject 1> performing the actions{action_str} based on the character reference images, strictly locking the appearance, face, hair{clothing_part}, and body to the reference{summary_extra}.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - the exact face, hair{clothing_part}, and body proportions from the character reference images remain entirely consistent across all active shots; only expressions, poses, and movements change as described.{retention_video}

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt), dialogue_output, build_status(total, warns))
