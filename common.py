"""MiniMax-H3 Prompt Generator 共通ユーティリティ（V3完全版）。"""
import re

SUBJECT_TYPES = ["woman", "man", "girl", "boy", "character", "person"]
_POSSESSIVE = {"woman": "her", "girl": "her", "man": "his", "boy": "his"}

# "[Shot 1]" "Shot 2:" "(shot 3)" "【Shot 1】" などの先頭表記
_SHOT_PREFIX_RE = re.compile(
    r"^\s*[\[\(［（【]?\s*shot\s*\d+\s*[\]\)］）】]?\s*[:：\-－]?\s*",
    re.I,
)

_TAG_LABELS = [
    ("Subject", ["被写体", "サブジェクト"]),
    ("Video", ["参照動画"]),
    ("Picture", ["画像"]),
]

_ASCII_BEFORE = r"(?<![<A-Za-z0-9_])"
_ASCII_AFTER = r"(?![A-Za-z0-9_>])"


def normalize_tags(text):
    """Subject 1 / <subject 1> / 被写体1 などを <Subject 1> に統一する。"""
    if not text:
        return ""
    for label, jp_words in _TAG_LABELS:
        alts = "|".join([label] + jp_words)
        text = re.sub(
            rf"<\s*(?:{alts})\s*(\d+)\s*>",
            lambda m, l=label: f"<{l} {m.group(1)}>",
            text, flags=re.I,
        )
        text = re.sub(
            rf"{_ASCII_BEFORE}{label}\s*(\d+){_ASCII_AFTER}",
            lambda m, l=label: f"<{l} {m.group(1)}>",
            text,
        )
        if label != "Picture":
            for jp in jp_words:
                text = re.sub(
                    rf"{jp}\s*(\d+)",
                    lambda m, l=label: f"<{l} {m.group(1)}>",
                    text,
                )
    return text


def strip_shot_prefix(text):
    return _SHOT_PREFIX_RE.sub("", text, count=1)


def normalize_and_strip_shot(text):
    return normalize_tags(strip_shot_prefix((text or "").strip())).strip()


def collect_shots(shot_inputs, append_suffix=None, skip_if_contains=None):
    """有効な Shot を集め、連番に振り直して整形する。"""
    bodies = []
    for enabled, text in shot_inputs:
        body = normalize_and_strip_shot(text)
        if enabled and body:
            bodies.append(body)

    formatted, names = [], []
    for i, body in enumerate(bodies, 1):
        if append_suffix and not (skip_if_contains and skip_if_contains in body):
            body = f"{body} {append_suffix}"
        names.append(f"[Shot {i}]")
        formatted.append(f"[Shot {i}] {body}")
    return formatted, names


def collect_dialogues(dialogue_inputs, shot_inputs):
    """有効な Shot と同期させてセリフを収集・連番整形する。"""
    dialogues = []
    for (enabled, text), (_, _) in zip(dialogue_inputs, shot_inputs):
        # Shot自体が有効かつセリフがある場合のみ抽出
        d_text = (text or "").strip()
        body = normalize_tags(strip_shot_prefix(d_text)).strip()
        # Shotが有効な場合の位置に合わせる
        dialogues.append((enabled, body))

    # 有効なShotの有効インデックスに対応させるため、shot_inputsと同時に判定
    valid_dialogues = []
    for (s_enabled, _), (d_enabled, d_body) in zip(shot_inputs, dialogues):
        if s_enabled:
            if d_enabled and d_body:
                valid_dialogues.append(d_body)
            else:
                valid_dialogues.append("")

    formatted_dialogues = []
    for i, d_body in enumerate(valid_dialogues, 1):
        if d_body:
            formatted_dialogues.append(f"[Shot {i}] {d_body}")
        else:
            formatted_dialogues.append(f"[Shot {i}]")
    return formatted_dialogues


def resolve_music(enable_music, music_text):
    text = (music_text or "").strip()
    return text if (enable_music and text) else "N/A"


def clean_prompt(prompt):
    return re.sub(r"\n{3,}", "\n\n", prompt).strip()