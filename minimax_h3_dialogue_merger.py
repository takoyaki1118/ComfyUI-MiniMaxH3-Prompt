try:
    from .common import clean_prompt
except ImportError:
    from common import clean_prompt
import re


class MinimaxH3DialogueMerger:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "forceInput": True}),
                "dialogue": ("STRING", {"multiline": True, "forceInput": True}),
                "merge_mode": (["append_to_end", "insert_into_shots"], {
                    "default": "append_to_end",
                    "tooltip": "append_to_end: 末尾にまとめて追加 / insert_into_shots: 各 [Shot N] の直後に挿入"
                }),
                "dialogue_label": ("STRING", {"default": "Dialogue", "tooltip": "末尾追加時の見出しラベル"})
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("merged_prompt",)
    FUNCTION = "merge"
    CATEGORY = "MiniMaxH3"

    def merge(self, prompt, dialogue, merge_mode, dialogue_label):
        p_text = (prompt or "").strip()
        d_text = (dialogue or "").strip()

        if not d_text:
            return (p_text,)

        if merge_mode == "append_to_end":
            merged = f"{p_text}\n\n{dialogue_label}:\n{d_text}"
            return (clean_prompt(merged),)

        # insert_into_shots モード
        # dialogue行ごとに [Shot N] を探して直後に差し込む
        d_lines = d_text.split("\n")
        current_prompt = p_text

        inserted_any = False
        for line in d_lines:
            match = re.match(r"^(\[Shot \d+\])\s*(.*)", line.strip())
            if match:
                shot_tag, content = match.groups()
                if not content:
                    continue # 内容が空ならスキップ
                
                # プロンプト内から [Shot N] を探し、そのブロックの末尾（次ぎのShotか空行まで）の直後に挿入
                # 簡単のため、 "[Shot N] 英文..." の行自体の直下に改行してセリフを挟み込む
                pattern = re.escape(shot_tag) + r"[^\n]*"
                m_shot = re.search(pattern, current_prompt)
                if m_shot:
                    end_pos = m_shot.end()
                    # 直後にDialogueを挿入
                    formatted_line = f"\n  - Dialogue: \"{content}\""
                    current_prompt = current_prompt[:end_pos] + formatted_line + current_prompt[end_pos:]
                    inserted_any = True

        if not inserted_any:
            # マーカーが見つからない場合はフォールバックとして末尾に追加
            merged = f"{p_text}\n\n{dialogue_label}:\n{d_text}"
            return (clean_prompt(merged),)

        return (clean_prompt(current_prompt),)