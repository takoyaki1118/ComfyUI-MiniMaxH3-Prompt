import re


class MinimaxH3PromptGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "summary_action": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【動画全体の動き】動画全体で人物が何をするかを一文で。\n例: ゆっくり前に歩いてきて、優しく微笑みながらベンチに座る"
                }),
                "camera_style": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【カメラ・画作り】撮影方法・光・質感など。\n例: シネマティックな照明、35mm手持ちカメラ、自然なボケ味"
                }),
                "soundscape": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【環境音・効果音】画面内で鳴っている音。\n例: 風の音、遠くの波の音、砂利を踏む足音"
                }),

                # Subject 1 特記事項
                "subject1_extra": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【人物の補足（任意）】参照画像だけでは足りない特徴があれば。\n例: 右手に小さな革のバッグを持っている"
                }),

                # 男性（Subject 2）フラグ＆設定
                "has_male": ("BOOLEAN", {"default": False}),
                "male_role": ("STRING", {
                    "default": "",
                    "placeholder": "【男性の役割】has_male ON のとき使用。空なら「男性の主観視点の手」になります。\n例: 向かいに座る男性の腕"
                }),
                "male_retention_desc": ("STRING", {
                    "default": "",
                    "placeholder": "【男性の保持設定】空なら「手が自然に絡む（部分保持）」になります。\n例: 手のみ映る。顔は映さない"
                }),

                # BGM 設定
                "enable_music": ("BOOLEAN", {"default": False}),
                "music_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【BGM】enable_music ON のとき使用。\n例: 穏やかなアコースティックギターのBGM"
                }),

                # Shot 1 ~ Shot 4 設定
                "shot1_enable": ("BOOLEAN", {"default": True}),
                "shot1_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 1】最初のカット。冒頭は参照画像(<Picture 1>)から始まります。\n人物は <Subject 1> と書くと参照画像の人物として扱われます。\n例: <Picture 1>から始まる。<Subject 1>がカメラの方に軽く顔を向け、ゆっくり3歩前に進んで微笑む"
                }),

                "shot2_enable": ("BOOLEAN", {"default": False}),
                "shot2_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 2】2カット目（カメラ切り替え後）。\n例: ミディアムクローズアップに切り替わる。<Subject 1>は歩き続け、周囲を見回す"
                }),

                "shot3_enable": ("BOOLEAN", {"default": False}),
                "shot3_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 3】3カット目。\n例: カメラが滑らかにパンする。<Subject 1>が木のベンチに近づき、優雅に座る"
                }),

                "shot4_enable": ("BOOLEAN", {"default": False}),
                "shot4_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【Shot 4】4カット目。\n例: 引きの画角。<Subject 1>がベンチで遠くの海を眺める"
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

        # 3. 男性（Subject 2）定義・保持設定（空欄時は英語の既定文を使用）
        if has_male:
            role = male_role.strip() or "male POV hands visible in frame"
            retention = male_retention_desc.strip() or \
                "partially_preserved - hands interacting naturally with Subject 1"
            male_def_str = f"\n<Subject 2> is the {role} visible in <Picture 1> (or introduced from the image)."
            male_ret_str = f"\n<Subject 2> (appears in {shot_list_str}): {retention}"
        else:
            male_def_str = ""
            male_ret_str = ""

        # 4. Music 設定
        if enable_music and music_text.strip():
            final_music = music_text.strip()
        else:
            final_music = "N/A"

        # 5. 空欄の項目は文ごと省略
        action = summary_action.strip()
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"

        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""

        sound = soundscape.strip() or "N/A"

        # 6. プロンプトテンプレートの組み立て
        prompt = f"""subject_definitions:
<Subject 1> is the woman in <Picture 1>, with the exact face, the exact hair, the exact clothing, skin tone, and body proportions of <Picture 1>.{sub1_extra_formatted}
<Picture 1> is the first frame of [Shot 1], showing <Subject 1> in the exact pose, framing, and composition of the reference image.{male_def_str}

summary: [keyframe completion + reference generation] The target video starts from the exact first frame of <Picture 1> and continues forward as a continuous video{action_str}. The appearance, pose, and framing of <Subject 1> at the beginning are locked to <Picture 1>.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - her face, hair, clothing, skin tone, and body from <Picture 1> remain constant throughout; only expression, pose, and movement change as described.
<Picture 1> ([Shot 1] first frame): fully_preserved - the target video opens on the exact composition, pose, framing, lighting, and subject appearance of <Picture 1>.{male_ret_str}

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        # 連続した空行を整形
        clean_prompt = re.sub(r'\n{3,}', '\n\n', prompt).strip()

        return (clean_prompt,)