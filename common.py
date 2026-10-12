"""MiniMax-H3 Prompt Generator 共通ユーティリティ。"""
import re

# "[Shot 1]" "Shot 2:" "(shot 3)" "【Shot 1】" などの先頭表記
_SHOT_PREFIX_RE = re.compile(
    r"^\s*[\[\(［（【]?\s*shot\s*\d+\s*[\]\)］）】]?\s*[:：\-－]?\s*",
    re.I,
)

# (正規ラベル, 日本語の表記ゆれ)
_TAG_LABELS = [
    ("Subject", ["被写体", "サブジェクト"]),
    ("Video", ["参照動画"]),
    ("Picture", ["画像"]),
]

_ASCII_BEFORE = r"(?<![<A-Za-z0-9_])"
_ASCII_AFTER = r"(?![A-Za-z0-9_>])"


def normalize_tags(text):
    """Subject 1 / <subject 1> / 被写体1 などを <Subject 1> に統一する。"""
    for label, jp_words in _TAG_LABELS:
        alts = "|".join([label] + jp_words)
        # 山括弧付きの表記ゆれ（<subject 1>, <被写体1> など）
        text = re.sub(
            rf"<\s*(?:{alts})\s*(\d+)\s*>",
            lambda m, l=label: f"<{l} {m.group(1)}>",
            text, flags=re.I,
        )
        # 山括弧なしの英語表記
        text = re.sub(
            rf"{_ASCII_BEFORE}{label}\s*(\d+){_ASCII_AFTER}",
            lambda m, l=label: f"<{l} {m.group(1)}>",
            text, flags=re.I,
        )
        # 日本語表記
        for jp in jp_words:
            text = re.sub(
                rf"{jp}\s*(\d+)",
                lambda m, l=label: f"<{l} {m.group(1)}>",
                text,
            )
    return text


def strip_shot_prefix(text):
    return _SHOT_PREFIX_RE.sub("", text, count=1)


def collect_shots(shot_inputs, append_suffix=None, skip_if_contains=None):
    """有効な Shot を集め、連番に振り直して整形する。

    shot_inputs: [(enabled, text), ...]
    append_suffix: 各Shot末尾に補完する文（None なら補完しない）
    skip_if_contains: この文字列が本文にあれば補完しない
    returns: (整形済みShot文のリスト, ["[Shot 1]", ...])
    """
    bodies = []
    for enabled, text in shot_inputs:
        body = normalize_tags(strip_shot_prefix((text or "").strip())).strip()
        if enabled and body:
            bodies.append(body)

    formatted, names = [], []
    for i, body in enumerate(bodies, 1):
        if append_suffix and not (skip_if_contains and skip_if_contains in body):
            body = f"{body} {append_suffix}"
        names.append(f"[Shot {i}]")
        formatted.append(f"[Shot {i}] {body}")
    return formatted, names


def resolve_music(enable_music, music_text):
    text = (music_text or "").strip()
    return text if (enable_music and text) else "N/A"


def clean_prompt(prompt):
    return re.sub(r"\n{3,}", "\n\n", prompt).strip()
