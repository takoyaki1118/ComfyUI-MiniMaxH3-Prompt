import re

class MinimaxH3PromptGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "summary_action": ("STRING", {
                    "multiline": True, 
                    "default": "walking forward with a gentle smile and taking a seat"
                }),
                "camera_style": ("STRING", {
                    "multiline": True, 
                    "default": "cinematic lighting, handheld 35mm camera, natural bokeh"
                }),
                "soundscape": ("STRING", {
                    "multiline": True, 
                    "default": "ambient wind, distant ocean waves, footsteps on gravel"
                }),
                
                # Subject 1 特記事項
                "subject1_extra": ("STRING", {
                    "multiline": True, 
                    "default": ""
                }),

                # 男性（Subject 2）フラグ＆設定
                "has_male": ("BOOLEAN", {"default": False}),
                "male_role": ("STRING", {
                    "default": "male POV hands visible in frame"
                }),
                "male_retention_desc": ("STRING", {
                    "default": "partially_preserved - hands interacting naturally with Subject 1"
                }),

                # BGM 設定
                "enable_music": ("BOOLEAN", {"default": False}),
                "music_text": ("STRING", {
                    "multiline": True, 
                    "default": "soft acoustic guitar background music"
                }),

                # Shot 1 ~ Shot 4 設定
                "shot1_enable": ("BOOLEAN", {"default": True}),
                "shot1_text": ("STRING", {
                    "multiline": True, 
                    "default": "The shot begins from <Picture 1>. <Subject 1>, the woman with the exact face, hair and clothing of <Picture 1>, turns her head slightly toward the camera, takes three slow steps forward, and smiles softly."
                }),
                
                "shot2_enable": ("BOOLEAN", {"default": False}),
                "shot2_text": ("STRING", {
                    "multiline": True, 
                    "default": "The camera cuts to a medium close-up. <Subject 1> continues walking, taking a look at her surroundings with a warm expression."
                }),

                "shot3_enable": ("BOOLEAN", {"default": False}),
                "shot3_text": ("STRING", {
                    "multiline": True, 
                    "default": "The camera pans smoothly. <Subject 1> approaches a wooden bench and sits down gracefully."
                }),

                "shot4_enable": ("BOOLEAN", {"default": False}),
                "shot4_text": ("STRING", {
                    "multiline": True, 
                    "default": ""
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "MiniMaxH3"

    def generate_prompt(
        self, summary_action, camera_style, soundscape, 
        subject1_extra, has_male, male_role, male_retention_desc,
        enable_music, music_text,
        shot1_enable, shot1_text, shot2_enable, shot2_text,
        shot3_enable, shot3_text, shot4_enable, shot4_text
    ):
        # 1. 有効な Shot の収集とフォーマット化
        active_shots = []
        shot_inputs = [
            (1, shot1_enable, shot1_text),
            (2, shot2_enable, shot2_text),
            (3, shot3_enable, shot3_text),
            (4, shot4_enable, shot4_text),
        ]

        formatted_shots = []
        active_shot_names = []

        for num, enabled, text in shot_inputs:
            clean_text = text.strip()
            if enabled and clean_text:
                active_shot_names.append(f"[Shot {num}]")
                # "[Shot X]" 接頭辞が含まれていない場合は自動付与
                if not clean_text.startswith(f"[Shot {num}]"):
                    clean_text = f"[Shot {num}] {clean_text}"
                formatted_shots.append(clean_text)

        # Shotが何も有効化されていない場合のフォールバック
        if not formatted_shots:
            formatted_shots.append("[Shot 1] The shot begins from <Picture 1>.")
            active_shot_names.append("[Shot 1]")

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(active_shot_names)

        # 2. Subject 1 補足定義
        sub1_extra_formatted = f" {subject1_extra.strip()}" if subject1_extra.strip() else ""

        # 3. 男性（Subject 2）定義・保持設定
        if has_male:
            male_def_str = f"\n<Subject 2> is the {male_role.strip()} visible in <Picture 1> (or introduced from the image)."
            male_ret_str = f"\n<Subject 2> (appears in {shot_list_str}): {male_retention_desc.strip()}"
        else:
            male_def_str = ""
            male_ret_str = ""

        # 4. Music 設定
        if enable_music and music_text.strip():
            final_music = music_text.strip()
        else:
            final_music = "N/A"

        # 5. プロンプトテンプレートの組み立て
        prompt = f"""subject_definitions:
<Subject 1> is the woman in <Picture 1>, with the exact face, the exact hair, the exact clothing, skin tone, and body proportions of <Picture 1>.{sub1_extra_formatted}
<Picture 1> is the first frame of [Shot 1], showing <Subject 1> in the exact pose, framing, and composition of the reference image.{male_def_str}

summary: [keyframe completion + reference generation] The target video starts from the exact first frame of <Picture 1> and continues forward as a continuous video of <Subject 1> {summary_action.strip()}. The appearance, pose, and framing of <Subject 1> at the beginning are locked to <Picture 1>.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - her face, hair, clothing, skin tone, and body from <Picture 1> remain constant throughout; only expression, pose, and movement change as described.
<Picture 1> ([Shot 1] first frame): fully_preserved - the target video opens on the exact composition, pose, framing, lighting, and subject appearance of <Picture 1>.{male_ret_str}

detailed_description:
The target video is filmed in {camera_style.strip()}.
{shots_content}

overall_soundscape: {soundscape.strip()}
non_diegetic_music: {final_music}"""

        # 連続した空行を整形
        clean_prompt = re.sub(r'\n{3,}', '\n\n', prompt).strip()
        
        return (clean_prompt,)