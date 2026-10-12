import json
import re

# ---------------------------------------------------------------------------
# スタイルプリセット（LLMに渡す英語の指針）
# ---------------------------------------------------------------------------
STYLE_PRESETS = {
    "auto (infer from action)": "",
    "photorealistic live-action": (
        "photorealistic live-action footage with natural skin texture, realistic lighting "
        "and real lens behavior (depth of field, subtle motion blur)"
    ),
    "cinematic live-action": (
        "cinematic live-action film look with dramatic lighting, shallow depth of field, "
        "color grading and deliberate camera movement"
    ),
    "anime (2D)": (
        "high-quality 2D Japanese anime with clean line art, cel shading, vivid colors "
        "and expressive, stylized motion"
    ),
    "3D CG animation": (
        "polished 3D CG animation with soft global illumination, smooth rigged motion "
        "and clean stylized materials"
    ),
    "illustration / painterly": (
        "painterly illustrated look with visible brush texture, soft edges and a "
        "hand-crafted color palette"
    ),
    "claymation / stop-motion": (
        "tactile stop-motion / claymation look with handmade textures and slightly "
        "stepped, charming motion"
    ),
    "custom (use style_note only)": "",
}

MODES = ["first_frame", "char_ref", "char_ref_motion"]

MODE_RULES = {
    "first_frame": (
        "MODE: first_frame (keyframe completion)\n"
        "- <Picture 1> is the first frame of [Shot 1]. Shot 1 must START from that exact "
        "pose, framing and composition, then continue forward naturally.\n"
        "- Refer to the person only as <Subject 1> (and <Subject 2> if the user mentions another person).\n"
        "- Do NOT describe face, hair, clothing or body of <Subject 1>; they come from <Picture 1>.\n"
        "- Do not contradict what is visible in the first frame (location, lighting, pose)."
    ),
    "char_ref": (
        "MODE: char_ref (character reference generation)\n"
        "- <Subject 1> is a character defined by character reference images (full-body and face close-up). "
        "There is NO first frame, so you may freely choose the scene, location, framing and camera.\n"
        "- Refer to the character only as <Subject 1>.\n"
        "- Do NOT describe face, hair, clothing or body of <Subject 1>; the appearance is locked to the reference.\n"
        "- Describe only: environment, camera, pose, movement, expression, and interaction."
    ),
    "char_ref_motion": (
        "MODE: char_ref_motion (character reference + motion reference video)\n"
        "- <Subject 1> is the character from the reference images. <Video 1> is a motion reference video "
        "that supplies body movement, timing and camera work.\n"
        "- Refer to the character only as <Subject 1> and to the video only as <Video 1>.\n"
        "- Do NOT invent movement that conflicts with <Video 1>. Shots should describe the scene, "
        "expression and context around the motion, and should explicitly say the movement follows <Video 1>.\n"
        "- Do NOT describe face, hair, clothing or body of <Subject 1>.\n"
        "- Also fill 'motion_video_desc': a short English description of what <Video 1> likely contains, "
        "inferred from the user's action."
    ),
}


MEDIA_OPTIONS = ["none", "image", "video", "image+video"]

EXAMPLES = {
    "first_frame": (
        '{"summary_action": "walks slowly toward the camera and sits on a wooden bench",'
        ' "camera_style": "35mm handheld, soft golden-hour light, natural bokeh",'
        ' "soundscape": "gentle wind and distant waves",'
        ' "music": "",'
        ' "shots": ["Starting from the exact first frame, medium shot. <Subject 1> turns slightly toward the camera and takes three slow steps forward with a faint smile.",'
        ' "Camera glides into a medium close-up. <Subject 1> reaches the bench and sits down gracefully, looking out at the sea."]}'
    ),
    "char_ref": (
        '{"summary_action": "stands on a rooftop at dusk, turns around and waves at the camera",'
        ' "camera_style": "high-quality 2D anime, cel shading, warm sunset backlight, shallow depth of field",'
        ' "soundscape": "soft city ambience and a light breeze",'
        ' "music": "",'
        ' "shots": ["Wide shot from the front. <Subject 1> stands on a rooftop railing at sunset, hair and clothes swaying in the wind.",'
        ' "Medium close-up from a low angle. <Subject 1> turns around, smiles brightly and waves at the camera."]}'
    ),
    "char_ref_motion": (
        '{"summary_action": "dances in a neon-lit alley, following the rhythm of the reference video",'
        ' "camera_style": "cinematic live-action, neon lighting, slow handheld push-in",'
        ' "soundscape": "muffled street ambience",'
        ' "music": "",'
        ' "motion_video_desc": "a person performs a short upbeat dance with arm swings while the camera slowly pushes in",'
        ' "shots": ["Medium shot. <Subject 1> dances in the alley, with body movement, timing and camera work following <Video 1>."]}'
    ),
}


def _build_system_prompt(mode, include_music, include_soundscape, max_shots,
                         attached="none", few_shot=False):
    music_rule = (
        "'music': one short sentence describing suitable background music."
        if include_music
        else "'music': must be an empty string \"\"."
    )
    sound_rule = (
        "'soundscape': diegetic sounds audible in the scene (ambience, footsteps, wind, etc.), one sentence."
        if include_soundscape
        else "'soundscape': must be an empty string \"\"."
    )
    motion_key = ',\n  "motion_video_desc": "..."' if mode == "char_ref_motion" else ""

    prompt = f"""You are a professional prompt writer for the MiniMax-H3 video generation model.
The user gives a short idea (action + visual style). Expand it into a complete, production-ready prompt split into fixed fields.

{MODE_RULES[mode]}

GENERAL RULES
- Write ALL field values in English, even if the user writes in another language.
- Each shot = ONE continuous camera setup. State shot size/angle, camera movement, subject action, and expression.
- Make actions concrete and physically plausible for a short clip. Avoid abstract or emotional-only descriptions.
- Keep shots visually and logically continuous (same location/time/lighting unless the user says otherwise).
- Do NOT write "[Shot N]" prefixes inside the shot text. The system adds them.
- Do NOT use markdown, comments, or extra keys.
- Respect the number of shots requested (maximum {max_shots}).
- Apply the requested visual style consistently in 'camera_style' and the shot wording.

FIELDS
- 'summary_action': ONE sentence describing what <Subject 1> does across the whole video. Do not include "<Subject 1>" at the start; it is inserted automatically (write e.g. "walks along the shore and smiles at the camera").
- 'camera_style': camera, lighting, texture and overall look in one sentence or comma-separated phrases (e.g. "35mm handheld, soft golden-hour light, natural bokeh").
- {sound_rule}
- {music_rule}
- 'shots': array of strings, one per shot, in order.

OUTPUT FORMAT
Return ONLY a single valid JSON object, no code fences, no explanation:
{{
  "summary_action": "...",
  "camera_style": "...",
  "soundscape": "...",
  "music": "...",
  "shots": ["...", "..."]{motion_key}
}}"""

    media_lines = []
    if attached in ("image", "image+video"):
        role = ("the first frame <Picture 1>" if mode == "first_frame"
                else "the character reference image (<Picture 1>)")
        media_lines.append(
            f"- An image is attached: it is {role}. Use it ONLY to ground the environment, pose, "
            "framing, lighting and overall style. Never describe the subject's face, hair or clothing."
        )
    if attached in ("video", "image+video"):
        media_lines.append(
            "- A video is attached (sampled at about 1 fps): it is <Video 1>, the motion reference. "
            "Base the action, timing and camera movement of your shots on what actually happens in it."
        )
    if media_lines:
        prompt += "\n\nATTACHED MEDIA\n" + "\n".join(media_lines)

    if few_shot:
        prompt += ("\n\nEXAMPLE OF A VALID OUTPUT (structure and tone only; do not copy the content):\n"
                   + EXAMPLES[mode])

    return prompt


class MinimaxH3SystemPromptBuilder:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (MODES, {"default": "char_ref"}),
                "action_idea": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【動作・アイデア（1〜2行）】\n例: 夕方の海辺を歩きながら、振り返って笑顔で手を振る"
                }),
                "style": (list(STYLE_PRESETS.keys()), {"default": "auto (infer from action)"}),
                "style_note": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "【スタイル補足（任意）】例: フォトリアル、柔らかい逆光 / 3Dアニメ、パステル調"
                }),
                "shot_count": ("INT", {"default": 2, "min": 1, "max": 4, "step": 1}),
                "include_soundscape": ("BOOLEAN", {"default": True}),
                "include_music": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "extra_notes": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "【追加指示（任意）】例: 全体的に静かな雰囲気。カメラは固定寄り。"
                }),
                "duration_sec": ("INT", {"default": 0, "min": 0, "max": 60, "step": 1,
                                         "tooltip": "0 = 指定なし。指定すると各Shotの長さ配分をLLMに考慮させます"}),
                "attached_media": (MEDIA_OPTIONS, {
                    "default": "none",
                    "tooltip": "TextGenerate の image / video 入力に参照素材を接続する場合に合わせて選択"}),
                "few_shot_example": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "出力例をsystem_promptに埋め込む。小さめのモデルで出力形式が崩れる場合にON"}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("system_prompt", "user_prompt")
    FUNCTION = "build"
    CATEGORY = "MiniMaxH3"

    def build(self, mode, action_idea, style, style_note, shot_count,
              include_soundscape, include_music, extra_notes="", duration_sec=0,
              attached_media="none", few_shot_example=False):
        system_prompt = _build_system_prompt(
            mode, include_music, include_soundscape, shot_count,
            attached=attached_media, few_shot=few_shot_example)

        style_desc = STYLE_PRESETS.get(style, "")
        style_lines = []
        if style_desc:
            style_lines.append(f"{style} - {style_desc}")
        if style_note.strip():
            style_lines.append(f"User style note: {style_note.strip()}")
        if not style_lines:
            style_lines.append("Not specified. Infer the most fitting style from the action.")

        lines = [
            f"Action idea: {action_idea.strip() or '(none given - invent a simple, natural action)'}",
            "Visual style: " + " | ".join(style_lines),
            f"Number of shots: exactly {shot_count}",
        ]
        if duration_sec > 0:
            lines.append(f"Approximate total duration: {duration_sec} seconds (distribute action across shots accordingly)")
        if extra_notes.strip():
            lines.append(f"Extra notes: {extra_notes.strip()}")
        lines.append("\nReturn the JSON object now.")

        return (system_prompt, "\n".join(lines))


# ---------------------------------------------------------------------------
# LLM出力パーサー
# ---------------------------------------------------------------------------
def _extract_json(text):
    """思考タグ・コードフェンス・前置きが混ざっていても JSON を取り出す。"""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
    # 開始タグがプロンプト側にあり、閉じタグだけ残るケース
    if "</think>" in text:
        text = text.split("</think>")[-1]
    text = re.sub(r"```(?:json)?", "", text, flags=re.I).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1:
        return None
    candidate = text[start:end + 1] if end > start else text[start:]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # 末尾カンマなどの軽微な崩れを修復
        fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            # max_length 不足などで途中切れの場合、取れる範囲で救出
            return _lenient_parse(candidate)


def _lenient_parse(text):
    data = {}
    for key in ("summary_action", "camera_style", "soundscape", "music", "motion_video_desc"):
        m = re.search(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % key, text, flags=re.S)
        if m:
            data[key] = m.group(1).replace('\\"', '"').replace("\\n", " ")
    m = re.search(r'"shots"\s*:\s*\[(.*)', text, flags=re.S)
    if m:
        data["shots"] = [x.replace('\\"', '"')
                         for x in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))]
    if data:
        data["_lenient"] = True
        return data
    return None


def _normalize_tags(text):
    """表記ゆれ（Subject 1 / Video 1）を <Subject 1> / <Video 1> に統一。"""
    text = re.sub(r"(?<!<)\bSubject\s*1\b(?!>)", "<Subject 1>", text)
    text = re.sub(r"(?<!<)\bVideo\s*1\b(?!>)", "<Video 1>", text)
    text = re.sub(r"(?<!<)\bPicture\s*1\b(?!>)", "<Picture 1>", text)
    return text


def _strip_shot_prefix(text):
    return re.sub(r"^\s*\[?\s*shot\s*\d+\s*\]?\s*[:：]?\s*", "", text, flags=re.I)


class MinimaxH3LLMOutputParser:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "llm_text": ("STRING", {"multiline": True, "default": "", "forceInput": True}),
            }
        }

    RETURN_TYPES = (
        "STRING", "STRING", "STRING", "STRING",
        "STRING", "STRING", "STRING", "STRING",
        "BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN",
        "STRING", "INT", "STRING",
    )
    RETURN_NAMES = (
        "summary_action", "camera_style", "soundscape", "music_text",
        "shot1_text", "shot2_text", "shot3_text", "shot4_text",
        "enable_music", "shot2_enable", "shot3_enable", "shot4_enable",
        "motion_video_desc", "shot_count", "status",
    )
    FUNCTION = "parse"
    CATEGORY = "MiniMaxH3"

    def parse(self, llm_text):
        data = _extract_json(llm_text)
        empty = ("", "", "", "", "", "", "", "", False, False, False, False, "", 0)

        if not isinstance(data, dict):
            return empty + ("ERROR: JSON を解析できませんでした。LLM の出力を確認してください。",)

        def s(key):
            v = data.get(key, "")
            return _normalize_tags(str(v).strip()) if v else ""

        shots_raw = data.get("shots", [])
        if isinstance(shots_raw, str):
            shots_raw = [shots_raw]
        shots = [_normalize_tags(_strip_shot_prefix(str(x).strip()))
                 for x in shots_raw if str(x).strip()][:4]
        count = len(shots)
        shots += [""] * (4 - len(shots))

        warnings = []
        if data.get("_lenient"):
            warnings.append("JSONが不完全です(max_length不足の可能性。最後のShotが欠けているかもしれません)")
        if count == 0:
            warnings.append("shots が空です")
        for i, sh in enumerate(shots[:count], 1):
            if "<Subject 1>" not in sh:
                warnings.append(f"Shot {i} に <Subject 1> がありません")

        music = s("music")
        status = "OK" if not warnings else "WARN: " + " / ".join(warnings)

        return (
            s("summary_action"), s("camera_style"), s("soundscape"), music,
            shots[0], shots[1], shots[2], shots[3],
            bool(music), shots[1] != "", shots[2] != "", shots[3] != "",
            s("motion_video_desc"), count, status,
        )
