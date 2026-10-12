try:
    from .common import collect_shots, resolve_music, clean_prompt
except ImportError:
    from common import collect_shots, resolve_music, clean_prompt

VIDEO_REF_SUFFIX = "(following the motion and timing of <Video 1>)"


class MinimaxH3CharRefMotionPromptGenerator:
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

                # 衣服情報の有無スイッチ
                "include_clothing": ("BOOLEAN", {
                    "default": True,
                    "label_on": "clothing enabled",
                    "label_off": "clothing ignored"
                }),

                # 参照動画（モーションビデオ）のスイッチと設定
                "use_motion_video": ("BOOLEAN", {
                    "default": False,
                    "label_on": "motion video enabled",
                    "label_off": "no motion video"
                }),
                "motion_video_desc": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【参照動画の動き（任意）】use_motion_video ON のとき使用。空でも <Video 1> は有効です。\n例: 手を振る動作とカメラのゆっくりとしたパン"
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
                    "placeholder": "【Shot 1】最初のカット。\n例: <Subject 1>がカメラの正面に立ち、明るい笑顔を見せる"
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
            },
            "optional": {
                "auto_append_video_ref": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "ON: <Video 1> への言及がない各Shotの末尾に、参照動画に従う旨の英文を自動追記します"
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "MiniMaxH3"

    def generate_prompt(
        self, summary_action, camera_style, soundscape,
        include_clothing, use_motion_video, motion_video_desc,
        character_extra, enable_music, music_text,
        shot1_enable, shot1_text, shot2_enable, shot2_text,
        shot3_enable, shot3_text, shot4_enable, shot4_text,
        auto_append_video_ref=True,
    ):
        # 参照動画の有効判定はスイッチのみ（説明文は任意）
        use_video = bool(use_motion_video)

        # 1. 有効な Shot を連番化して整形
        formatted_shots, active_shot_names = collect_shots(
            [
                (shot1_enable, shot1_text),
                (shot2_enable, shot2_text),
                (shot3_enable, shot3_text),
                (shot4_enable, shot4_text),
            ],
            append_suffix=VIDEO_REF_SUFFIX if (use_video and auto_append_video_ref) else None,
            skip_if_contains="<Video 1>",
        )

        if not formatted_shots:
            fallback = "[Shot 1] <Subject 1> appears in the scene."
            if use_video:
                fallback += " The movement follows <Video 1>."
            formatted_shots = [fallback]
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

        # 5. 参照動画の有無に応じた分岐
        if use_video:
            desc = motion_video_desc.strip()
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

        # 6. 各種テキスト
        action = summary_action.strip()
        action_str = f" of <Subject 1> {action}" if action else " of <Subject 1>"

        camera = camera_style.strip()
        camera_line = f"The target video is filmed in {camera}.\n" if camera else ""

        sound = soundscape.strip() or "N/A"

        # 7. テンプレート
        prompt = f"""subject_definitions:
<Subject 1> is the character depicted in the character reference images (<Picture 1>, showing full-body and close-up face views), maintaining the exact face, hair{clothing_part}, skin tone, and body proportions of the reference.{char_extra_formatted}
The reference images provide the definitive character design sheet for <Subject 1>.{video_def}

summary: {task_type} The target video features <Subject 1> performing the actions{action_str} based on the character reference images, strictly locking the appearance, face, hair{clothing_part}, and body to the reference{summary_extra}.

retention_analysis:
<Subject 1> (appears in {shot_list_str}): fully_preserved - the exact face, hair{clothing_part}, and body proportions from the character reference images remain entirely consistent across all active shots; only expressions, poses, and movements change as described.{retention_video}

detailed_description:
{camera_line}{shots_content}

overall_soundscape: {sound}
non_diegetic_music: {final_music}"""

        return (clean_prompt(prompt),)
