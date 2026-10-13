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
                "merge_mode": (["official_format", "append_to_end", "insert_into_shots"], {
                    "default": "official_format",
                    "tooltip": "official_format: 公式ガイド形式 (<d>[Japanese] ...</d>) で各Shot内に安全に統合 / append_to_end: 末尾追加 / insert_into_shots: 簡易挿入"
                }),
                "dialogue_label": ("STRING", {"default": "dialogues", "tooltip": "末尾追加時の見出しラベル"})
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

        d_lines = [l.strip() for l in d_text.split("\n") if l.strip()]

        if merge_mode == "official_format":
            current_prompt = p_text
            inserted_count = 0
            
            # detailed_description: 以降の領域のみを対象にする、または [Shot N] が行頭から始まるものを厳密に狙う
            for line in d_lines:
                match = re.match(r"^(\[Shot \d+\])\s*(.*)", line)
                if match:
                    shot_tag, dialogue_content = match.groups()
                    
                    # 改善: 行頭に [Shot N] があるものを正確にマッチさせる（detailed_description内を想定）
                    # 例: "[Shot 1] ショット1の動作だよ"
                    pattern = rf"(^|\n)({re.escape(shot_tag)}[^\n]*)"
                    m_shot = re.search(pattern, current_prompt)
                    
                    if m_shot:
                        prefix_newline = m_shot.group(1)
                        shot_full_line = m_shot.group(2)
                        
                        # Shot行の直下に改行してセリフ行を挿入
                        replacement = f"{prefix_newline}{shot_full_line}\n  {dialogue_content}"
                        current_prompt = current_prompt.replace(f"{prefix_newline}{shot_full_line}", replacement, 1)
                        inserted_count += 1

            if inserted_count == 0:
                merged = f"{p_text}\n\ndialogues:\n{d_text}"
                return (clean_prompt(merged),)
            return (clean_prompt(current_prompt),)

        # 従来の insert_into_shots モード
        current_prompt = p_text
        for line in d_lines:
            match = re.match(r"^(\[Shot \d+\])\s*(.*)", line)
            if match:
                shot_tag, content = match.groups()
                pattern = rf"(^|\n)({re.escape(shot_tag)}[^\n]*)"
                m_shot = re.search(pattern, current_prompt)
                if m_shot:
                    prefix_newline = m_shot.group(1)
                    shot_full_line = m_shot.group(2)
                    replacement = f"{prefix_newline}{shot_full_line}\n  - Dialogue: {content}"
                    current_prompt = current_prompt.replace(f"{prefix_newline}{shot_full_line}", replacement, 1)

        return (clean_prompt(current_prompt),)