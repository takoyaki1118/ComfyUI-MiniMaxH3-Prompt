import traceback

print("Initializing MiniMax-H3 Prompt Generator Nodes...")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}


def _register(label, loader):
    """loader() は {クラス名: (クラス, 表示名)} を返す。失敗しても他ノードの登録は続行する。"""
    try:
        for name, (cls, display) in loader().items():
            NODE_CLASS_MAPPINGS[name] = cls
            NODE_DISPLAY_NAME_MAPPINGS[name] = display
    except Exception as e:
        print(f"Error initializing {label}: {e}")
        traceback.print_exc()


def _first_frame():
    from .minimax_h3_prompt import MinimaxH3PromptGenerator as C
    return {"MinimaxH3PromptGenerator": (C, "MiniMax-H3 Prompt Generator")}


def _last_frame():
    from .minimax_h3_last_frame_prompt import MinimaxH3LastFramePromptGenerator as C
    return {"MinimaxH3LastFramePromptGenerator": (C, "MiniMax-H3 Last Frame (L2VA) Prompt Generator")}


def _char_ref():
    from .minimax_h3_char_ref_prompt import MinimaxH3CharRefPromptGenerator as C
    return {"MinimaxH3CharRefPromptGenerator": (C, "MiniMax-H3 Char Ref Prompt Generator")}


def _char_ref_motion():
    from .minimax_h3_char_ref_motion_prompt import MinimaxH3CharRefMotionPromptGenerator as C
    return {"MinimaxH3CharRefMotionPromptGenerator": (C, "MiniMax-H3 Char Ref + Motion Prompt Generator")}


def _char_ref_first_frame():
    from .minimax_h3_char_ref_first_frame_prompt import MinimaxH3CharRefFirstFramePromptGenerator as C
    return {"MinimaxH3CharRefFirstFramePromptGenerator": (C, "MiniMax-H3 Char Ref + First Frame Prompt Generator")}


def _llm_helper():
    from .minimax_h3_llm_helper import MinimaxH3SystemPromptBuilder as B, MinimaxH3LLMOutputParser as P
    return {
        "MinimaxH3SystemPromptBuilder": (B, "MiniMax-H3 System Prompt Builder"),
        "MinimaxH3LLMOutputParser": (P, "MiniMax-H3 LLM Output Parser"),
    }


def _dialogue_merger():
    from .minimax_h3_dialogue_merger import MinimaxH3DialogueMerger as C
    return {"MinimaxH3DialogueMerger": (C, "MiniMax-H3 Dialogue Merger")}


_register("MiniMax-H3 Prompt Generator (first frame)", _first_frame)
_register("MiniMax-H3 Last Frame (L2VA) Prompt Generator", _last_frame)
_register("MiniMax-H3 Char Ref Prompt Generator", _char_ref)
_register("MiniMax-H3 Char Ref + Motion Prompt Generator", _char_ref_motion)
_register("MiniMax-H3 Char Ref + First Frame Prompt Generator", _char_ref_first_frame)
_register("MiniMax-H3 LLM Helper nodes", _llm_helper)
_register("MiniMax-H3 Dialogue Merger", _dialogue_merger)

print(f"Successfully initialized {len(NODE_CLASS_MAPPINGS)} nodes for MiniMax-H3 Prompt Generator.")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
