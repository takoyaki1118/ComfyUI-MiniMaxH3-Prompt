try:
    from .common import collect_shots, resolve_music, clean_prompt
except ImportError:
    from common import collect_shots, resolve_music, clean_prompt


class MinimaxH3CharRefPromptGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "summary_action": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【動画全体の動き】動画全体でキャラクターが何をするかを一文で。\n例: 街並みを背景に、こちらを向いて優しく手を振る"
                }),
                "camera_style": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【カメラ・画作り】撮影方法・光・質感など。\n例: シネマティックな照明、浅い被写界深度、高品質なアニメ調"
                }),
                "soundscape": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【環境音・効果音】画面内で鳴っている音。\n例: 通行人のざわめき、穏やかな風の音"
                }),

                # キャラクターリファレンス用の衣服制御スイッチ
                "include_clothing": ("BOOLEAN", {
                    "default": True,
                    "label_on": "clothing enabled",
                    "label_off": "clothing ignored"
                }),

                # Character Reference 特記事項
                "character_extra": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【キャラクターの補足（任意）】リファレンス画像（全身・顔アップ）の補足。\n例: 髪型はツインテールで、笑顔が特徴的"
                }),

                # BGM 設定
                "enable_music": ("BOOLEAN", {"default": False}),
                "music_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【BGM】enable_music ON のとき使用。\n例: 明るく爽やかなアップテンポの曲"
                }),

                # Shot 1 ~ Shot 4 設定
                "shot1_enable": ("BOOLEAN", {"default": True}),
                "shot1_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 1】最初のカット。\n人物は <Subject 1> と書くとリファレンス画像のキャラになります。\n例: <Subject 1>がカメラの正面に立ち、明るい笑顔を見せる"
                }),

                "shot2_enable": ("BOOLEAN", {"default": False}),
                "shot2_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 2】2カット目。\n例: カメラが少し引きの画角になり、<Subject 1>が歩き出す"
                }),

                "shot3_enable": ("BOOLEAN", {"default": False}),
                "shot3_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 3】3カット目。\n例: クローズアップに切り替わり、<Subject 1>が微笑む"
                }),

                "shot4_enable": ("BOOLEAN", {"default": False}),
                "shot4_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 4】4カット目。\n例: 別アングルから。<Subject 1>が振り返って手を振る"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "MiniMaxH3"

    def generate_prompt(
        self, summary_action, camera_style, soundscape,
        include_clothing, character_extra, enable_music, music_text,
        shot1_enable, shot1_text, shot2_enable, shot2_text,
        shot3_enable, shot3_text, shot4_enable, shot4_text
    ):
        # 1. 有効な Shot を連番化して整形
        formatted_shots, active_shot_names = collect_shots([
            (shot1_enable, shot1_text),
            (shot2_enable, shot2_text),
            (shot3_enable, shot3_text),
            (shot4_enable, shot4_text),
        ])

        if not formatted_shots:
            formatted_shots = ["[Shot 1] <Subject 1> appears in the scene."]
            active_shot_names = ["[Shot 1]"]

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(active_shot_names)

        # 2. 衣服情報の有無
        clothing_part = ", clothing" if include_clothing else ""

        # 3. Character 補足
        extra = character_extra.strip()
        char_extra_formatted = f" {extra}" if extra else ""

        # 4. Music
        final_music = resolve_music(enable_music, music_text)

        # 5. 各種テキスト
        action = summary_action.strip()
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"

        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""

        sound = soundscape.strip() or "N/A"

        # 6. テンプレート
        prompt = f"""subject_definitions:
<Subject 1> is the character depicted in the character reference images (<Picture 1>, showing full-body and close-up face views), maintaining the exact face, hair{clothing_part}, skin tone, and body proportions of the reference.{char_extra_formatted}
The reference images provide the definitive character design sheet for <Subject 1>.

summary: [character consistency generation] The target video generates a sequence featuring <Subject 1> based on the character reference images{action_str}. The appearance, facial features, and styling of <Subject 1> are strictly locked to the character reference.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - the exact face, hair{clothing_part}, and body proportions from the character reference images remain entirely consistent across all active shots; only expressions, poses, and movements change as described.

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt),)
