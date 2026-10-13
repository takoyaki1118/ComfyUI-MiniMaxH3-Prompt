"""MiniMax-H3 Prompt Generator 共通ユーティリティ（V3 完全版）。"""
import re

SUBJECT_TYPES = ["woman", "man", "girl", "boy", "character", "person"]
_POSSESSIVE = {"woman": "her", "girl": "her", "man": "his", "boy": "his"}

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


def collect_shots(shot_inputs, dialogue_inputs=None, append_suffix=None, skip_if_contains=None, auto_speech_cue=True, timestamp_step_sec=3.0):
    """有効な Shot を集め、連番・タイムスタンプ・セリフ（公式フォーマット）を統合して整形する。"""
    bodies = []
    dialogues = []
    
    for i, (enabled, text) in enumerate(shot_inputs):
        body = normalize_and_strip_shot(text)
        d_text = ""
        if dialogue_inputs and i < len(dialogue_inputs):
            d_text = normalize_tags(strip_shot_prefix((dialogue_inputs[i][1] or "").strip())).strip()
            
        if enabled and body:
            # セリフがあり、auto_speech_cue が有効なら末尾に発話アクションを追加
            if d_text and auto_speech_cue and "<Subject 1>" in body and "speaks" not in body:
                body = f"{body} <Subject 1> (S1) speaks a line."
            bodies.append(body)
            dialogues.append(d_text)

    formatted, names, formatted_dialogues = [], [], []
    for i, (body, d_text) in enumerate(zip(bodies, dialogues), 1):
        # タイムスタンプ付与（Shot 2以降）
        prefix = f"[Shot {i}]"
        if i > 1 and timestamp_step_sec > 0:
            ts_sec = (i - 1) * timestamp_step_sec
            mins = int(ts_sec // 60)
            secs = ts_sec % 60
            prefix = f"[Shot {i}] At {mins:02d}:{secs:06.3f},"

        if append_suffix and not (skip_if_contains and skip_if_contains in body):
            body = f"{body} {append_suffix}"
            
        names.append(f"[Shot {i}]")
        formatted.append(f"{prefix} {body}".strip())

        # セリフの公式フォーマット構築 (<d>[Japanese] ...</d>)
        if d_text:
            formatted_dialogues.append(f"[Shot {i}] <Subject 1> (S1) says, <d>[Japanese] {d_text}</d>")
        else:
            formatted_dialogues.append(f"[Shot {i}]")

    return formatted, names, formatted_dialogues


def resolve_music(enable_music, music_text):
    text = (music_text or "").strip()
    return text if (enable_music and text) else "N/A"


def clean_prompt(prompt):
    return re.sub(r"\n{3,}", "\n\n", prompt).strip()