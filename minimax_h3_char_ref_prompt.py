try:
    from .common import (
        collect_shots, collect_dialogues, resolve_music, clean_prompt,
        normalize_tags, SUBJECT_TYPES
    )
except ImportError:
    from common import (
        collect_shots, collect_dialogues, resolve_music, clean_prompt,
        normalize_tags, SUBJECT_TYPES
    )


class MinimaxH3CharRefPromptGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "summary_action": ("STRING", {"multiline": True, "default": "", "placeholder": "【動画全体の動き】"}),
                "camera_style": ("STRING", {"multiline": True, "default": "", "placeholder": "【カメラ・画作り】"}),
                "soundscape": ("STRING", {"multiline": True, "default": "", "placeholder": "【環境音・効果音】"}),
                "include_clothing": ("BOOLEAN", {"default": True, "label_on": "clothing enabled", "label_off": "clothing ignored"}),
                "character_extra": ("STRING", {"multiline": True, "default": "", "placeholder": "【キャラクターの補足】"}),
                "enable_music": ("BOOLEAN", {"default": False}),
                "music_text": ("STRING", {"multiline": True, "default": "", "placeholder": "【BGM】"}),

                "shot1_enable": ("BOOLEAN", {"default": True}),
                "shot1_text": ("STRING", {"multiline": True, "default": "", "placeholder": "【Shot 1】本文"}),
                "shot1_dialogue": ("STRING", {"multiline": False, "default": "", "placeholder": "【Shot 1】セリフ"}),

                "shot2_enable": ("BOOLEAN", {"default": False}),
                "shot2_text": ("STRING", {"multiline": True, "default": "", "placeholder": "【Shot 2】本文"}),
                "shot2_dialogue": ("STRING", {"multiline": False, "default": "", "placeholder": "【Shot 2】セリフ"}),

                "shot3_enable": ("BOOLEAN", {"default": False}),
                "shot3_text": ("STRING", {"multiline": True, "default": "", "placeholder": "【Shot 3】本文"}),
                "shot3_dialogue": ("STRING", {"multiline": False, "default": "", "placeholder": "【Shot 3】セリフ"}),

                "shot4_enable": ("BOOLEAN", {"default": False}),
                "shot4_text": ("STRING", {"multiline": True, "default": "", "placeholder": "【Shot 4】本文"}),
                "shot4_dialogue": ("STRING", {"multiline": False, "default": "", "placeholder": "【Shot 4】セリフ"}),
            },
            "optional": {
                "auto_speech_cue": ("BOOLEAN", {"default": True}),
                "subject_type": (SUBJECT_TYPES, {"default": "woman"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "dialogue")
    FUNCTION = "generate_prompt"
    CATEGORY = "MiniMaxH3"

    def generate_prompt(
        self, summary_action, camera_style, soundscape,
        include_clothing, character_extra, enable_music, music_text,
        shot1_enable, shot1_text, shot1_dialogue,
        shot2_enable, shot2_text, shot2_dialogue,
        shot3_enable, shot3_text, shot3_dialogue,
        shot4_enable, shot4_text, shot4_dialogue,
        auto_speech_cue=True, subject_type="woman"
    ):
        shot_inputs = [
            (shot1_enable, shot1_text), (shot2_enable, shot2_text),
            (shot3_enable, shot3_text), (shot4_enable, shot4_text)
        ]
        dialogue_inputs = [
            (shot1_enable, shot1_dialogue), (shot2_enable, shot2_dialogue),
            (shot3_enable, shot3_dialogue), (shot4_enable, shot4_dialogue)
        ]

        formatted_shots, active_shot_names = collect_shots(shot_inputs)
        formatted_dialogues = collect_dialogues(dialogue_inputs, shot_inputs)
        dialogue_output = "\n".join([d for d in formatted_dialogues if d.strip()])

        if not formatted_shots:
            formatted_shots = ["[Shot 1] <Subject 1> appears in the scene."]
            active_shot_names = ["[Shot 1]"]

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(active_shot_names)

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

        return (clean_prompt(prompt), dialogue_output)