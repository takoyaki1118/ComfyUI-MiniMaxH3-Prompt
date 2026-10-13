import json
import re

try:
    from .common import normalize_tags, strip_shot_prefix
except ImportError:
    from common import normalize_tags, strip_shot_prefix

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

MODES = ["first_frame", "char_ref", "char_ref_motion", "char_ref_first_frame"]

MODE_RULES = {
    "first_frame": (
        "MODE: first_frame (keyframe completion)\n"
        "- <Picture 1> is the first frame of [Shot 1]. Shot 1 must START from that exact "
        "pose, framing and composition, then continue forward naturally.\n"
        "- Refer to the person only as <Subject 1>."
    ),
    "char_ref": (
        "MODE: char_ref (character reference generation)\n"
        "- <Subject 1> is a character defined by character reference images."
    ),
    "char_ref_motion": (
        "MODE: char_ref_motion (character reference + motion reference video)\n"
        "- <Subject 1> is the character from reference. <Video 1> is a motion reference video."
    ),
    "char_ref_first_frame": (
        "MODE: char_ref_first_frame (character reference sheet + first frame composition)\n"
        "- <Picture 1> is character sheet. <Picture 2> is the exact first frame of [Shot 1]."
    ),
}

MEDIA_OPTIONS = ["none", "image", "video", "image+video", "character_ref + first_frame (2 images)"]


class MinimaxH3SystemPromptBuilder:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "mode": (MODES, {"default": "char_ref"}),
                "action_idea": ("STRING", {"multiline": True, "default": "", "placeholder": "【動作・アイデア】"}),
                "style": (list(STYLE_PRESETS.keys()), {"default": "auto (infer from action)"}),
                "style_note": ("STRING", {"multiline": False, "default": "", "placeholder": "【スタイル補足】"}),
                "shot_count": ("INT", {"default": 2, "min": 1, "max": 4, "step": 1}),
                "include_soundscape": ("BOOLEAN", {"default": True}),
                "include_music": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "dialogue_idea": ("STRING", {"multiline": True, "default": "", "placeholder": "【セリフのアイデア】例: 1個目のカットで「こんにちは！」と言う"}),
                "extra_notes": ("STRING", {"multiline": True, "default": "", "placeholder": "【追加指示】"}),
                "duration_sec": ("INT", {"default": 0, "min": 0, "max": 60, "step": 1}),
                "attached_media": (MEDIA_OPTIONS, {"default": "none"}),
                "few_shot_example": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("system_prompt", "user_prompt")
    FUNCTION = "build"
    CATEGORY = "MiniMaxH3"

    def build(self, mode, action_idea, style, style_note, shot_count,
              include_soundscape, include_music, dialogue_idea="", extra_notes="", duration_sec=0,
              attached_media="none", few_shot_example=False):
        
        dialogue_rule = (
            "\n- 'dialogues': array of strings (one per shot). If a shot has speech, format it EXACTLY as: "
            "\"<Subject 1> (S1) says, <d>[Japanese] 実際のセリフ</d>\" (or empty string \"\" if no dialogue)."
            if dialogue_idea.strip() else ""
        )
        dialogue_key = ',\n  "dialogues": ["...", "..."]' if dialogue_idea.strip() else ""

        system_prompt = f"""You are a professional prompt writer for the MiniMax-H3 video generation model.
The user gives a short idea. Expand it into a complete, production-ready JSON prompt.

{MODE_RULES[mode]}

GENERAL RULES
- Write ALL field values in English (except the Japanese text inside <d>[Japanese] ...</d> if dialogues are used).
- Each shot = ONE continuous camera setup.
- For Shot 2 and later, include timestamps like "At 00:03.500," right after "[Shot N]".
- Do NOT write "[Shot N]" prefixes inside the shot text itself (the system adds markers).
- Return ONLY a single valid JSON object, no code fences.

FIELDS
- 'summary_action': ONE sentence describing what <Subject 1> does.
- 'camera_style': camera, lighting and look in one sentence.
- 'soundscape': diegetic sounds sentence.
- 'music': background music sentence or empty.
- 'shots': array of strings, one per shot.{dialogue_rule}

OUTPUT FORMAT
{{
  "summary_action": "...",
  "camera_style": "...",
  "soundscape": "...",
  "music": "...",
  "shots": ["...", "..."]{dialogue_key}
}}"""

        lines = [
            f"Action idea: {action_idea.strip() or '(none given)'}",
        ]
        if dialogue_idea.strip():
            lines.append(f"Dialogue idea: {dialogue_idea.strip()}")
        lines.append("Visual style: " + STYLE_PRESETS.get(style, ""))
        lines.append(f"Number of shots: exactly {shot_count}")
        if duration_sec > 0:
            lines.append(f"Approximate total duration: {duration_sec} seconds")
        if extra_notes.strip():
            lines.append(f"Extra notes: {extra_notes.strip()}")
        lines.append("\nReturn the JSON object now.")

        return (system_prompt, "\n".join(lines))


def _extract_json(text):
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S | re.I)
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
        fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            return _lenient_parse(candidate)


def _lenient_parse(text):
    data = {}
    for key in ("summary_action", "camera_style", "soundscape", "music", "motion_video_desc"):
        m = re.search(r'"%s"\s*:\s*"((?:[^"\\]|\\.)*)"' % key, text, flags=re.S)
        if m:
            data[key] = m.group(1).replace('\\"', '"').replace("\\n", " ")
    for key_arr in ("shots", "dialogues"):
        m = re.search(r'"%s"\s*:\s*\[(.*)' % key_arr, text, flags=re.S)
        if m:
            data[key_arr] = [x.replace('\\"', '"') for x in re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1))]
    if data:
        data["_lenient"] = True
        return data
    return None


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
        "STRING", "STRING", "STRING", "STRING",
        "BOOLEAN", "BOOLEAN", "BOOLEAN", "BOOLEAN",
        "STRING", "INT", "STRING",
    )
    RETURN_NAMES = (
        "summary_action", "camera_style", "soundscape", "music_text",
        "shot1_text", "shot2_text", "shot3_text", "shot4_text",
        "dialogue1", "dialogue2", "dialogue3", "dialogue4",
        "enable_music", "shot2_enable", "shot3_enable", "shot4_enable",
        "motion_video_desc", "shot_count", "status",
    )
    FUNCTION = "parse"
    CATEGORY = "MiniMaxH3"

    def parse(self, llm_text):
        data = _extract_json(llm_text)
        empty = ("", "", "", "", "", "", "", "", "", "", "", "", False, False, False, False, "", 0)

        if not isinstance(data, dict):
            return empty + ("ERROR: JSON を解析できませんでした。",)

        def s(key):
            v = data.get(key, "")
            return normalize_tags(str(v).strip()) if v else ""

        shots_raw = data.get("shots", [])
        if isinstance(shots_raw, str):
            shots_raw = [shots_raw]
        shots = [normalize_tags(strip_shot_prefix(str(x).strip())) for x in shots_raw if str(x).strip()][:4]
        count = len(shots)
        shots += [""] * (4 - len(shots))

        dialogues_raw = data.get("dialogues", [])
        if isinstance(dialogues_raw, str):
            dialogues_raw = [dialogues_raw]
        dialogues = [normalize_tags(str(x).strip()) for x in dialogues_raw][:4]
        dialogues += [""] * (4 - len(dialogues))

        warnings = []
        if data.get("_lenient"):
            warnings.append("JSONが不完全です")
        if count == 0:
            warnings.append("shots が空です")

        music = s("music")
        status = "OK" if not warnings else "WARN: " + " / ".join(warnings)

        return (
            s("summary_action"), s("camera_style"), s("soundscape"), music,
            shots[0], shots[1], shots[2], shots[3],
            dialogues[0], dialogues[1], dialogues[2], dialogues[3],
            bool(music), shots[1] != "", shots[2] != "", shots[3] != "",
            s("motion_video_desc"), count, status,
        )