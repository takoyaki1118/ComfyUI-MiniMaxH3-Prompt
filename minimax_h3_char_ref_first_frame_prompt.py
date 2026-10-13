try:
    from .common import collect_shots, resolve_music, clean_prompt
except ImportError:
    from common import collect_shots, resolve_music, clean_prompt

SUBJECT_TYPES = ["woman", "man", "girl", "boy", "character", "person"]
_POSSESSIVE = {"woman": "her", "girl": "her", "man": "his", "boy": "his"}


class MinimaxH3CharRefFirstFramePromptGenerator:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "summary_action": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【動画全体の動き】動画全体でキャラクターが何をするかを一文で。\n例: ゆっくり前に歩いてきて、優しく微笑みながらベンチに座る"
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

                # 衣服情報の有無スイッチ
                "include_clothing": ("BOOLEAN", {
                    "default": True,
                    "label_on": "clothing enabled",
                    "label_off": "clothing ignored"
                }),

                # キャラクターリファレンス等の特記事項
                "character_extra": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【キャラクターの補足（任意）】参照画像だけでは足りない特徴があれば。\n例: 右手に小さな革のバッグを持っている"
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
                    "placeholder": "【Shot 1】最初のカット。冒頭はファーストフレーム(<Picture 2>)から始まります。\n例: <Picture 2>から始まる。<Subject 1>がカメラの方に軽く顔を向け、ゆっくり3歩前に進んで微笑む"
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
            },
            "optional": {
                "subject_type": (SUBJECT_TYPES, {
                    "default": "woman",
                    "tooltip": "<Subject 1> の種別。代名詞(her/his/their)も連動します"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "MiniMaxH3"

    def generate_prompt(
        self, summary_action, camera_style, soundscape,
        include_clothing, character_extra, enable_music, music_text,
        shot1_enable, shot1_text, shot2_enable, shot2_text,
        shot3_enable, shot3_text, shot4_enable, shot4_text,
        subject_type="woman",
    ):
        # 1. 有効な Shot を連番化して整形
        formatted_shots, active_shot_names = collect_shots([
            (shot1_enable, shot1_text),
            (shot2_enable, shot2_text),
            (shot3_enable, shot3_text),
            (shot4_enable, shot4_text),
        ])

        if not formatted_shots:
            formatted_shots = ["[Shot 1] The shot begins from <Picture 2>."]
            active_shot_names = ["[Shot 1]"]

        shots_content = "\n\n".join(formatted_shots)
        shot_list_str = ", ".join(active_shot_names)

        # 2. 種別・代名詞
        poss = _POSSESSIVE.get(subject_type, "their")
        clothing_part = ", clothing" if include_clothing else ""

        # 3. 補足情報
        extra = character_extra.strip()
        char_extra_formatted = f" {extra}" if extra else ""

        # 4. Music
        final_music = resolve_music(enable_music, music_text)

        # 5. 各種テキストの整形
        action = summary_action.strip()
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"

        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""

        sound = soundscape.strip() or "N/A"

        # 6. テンプレート組み立て
        prompt = f"""subject_definitions:
<Subject 1> is the {subject_type} depicted in the character reference images (<Picture 1>, showing full-body and close-up face views), maintaining the exact face, hair{clothing_part}, skin tone, and body proportions of the reference.{char_extra_formatted}
<Picture 1> provides the definitive character design sheet for <Subject 1>.
<Picture 2> is the first frame of [Shot 1], showing <Subject 1> (the same person as defined in <Picture 1>) in the exact pose, framing, and composition of the starting reference image.

summary: [character consistency generation + keyframe completion] The target video starts from the exact first frame of <Picture 2> and continues forward as a continuous video{action_str}. The appearance, facial features, and styling of <Subject 1> are strictly locked to the character reference (<Picture 1>), while the initial pose and framing are locked to <Picture 2>.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - the exact face, hair{clothing_part}, and body proportions from the character reference (<Picture 1>) remain entirely consistent across all active shots; only expressions, poses, and movements change as described.
<Picture 2> ([Shot 1] first frame): fully_preserved - the target video opens on the exact composition, pose, framing, lighting, and subject appearance of <Picture 2>.

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt),)