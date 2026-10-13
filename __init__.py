import traceback

print("Initializing MiniMax-H3 Prompt Generator Nodes...")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 1. 既存のファーストフレーム参照型ノードの初期化
try:
    try:
        from .minimax_h3_prompt import MinimaxH3PromptGenerator
    except ImportError:
        from minimax_h3_prompt import MinimaxH3PromptGenerator

    NODE_CLASS_MAPPINGS["MinimaxH3PromptGenerator"] = MinimaxH3PromptGenerator
    NODE_DISPLAY_NAME_MAPPINGS["MinimaxH3PromptGenerator"] = "MiniMax-H3 Prompt Generator"
except Exception as e:
    print(f"Error initializing MiniMax-H3 Prompt Generator node: {e}")
    traceback.print_exc()

# 2. キャラクターリファレンス参照型ノードの初期化
try:
    try:
        from .minimax_h3_char_ref_prompt import MinimaxH3CharRefPromptGenerator
    except ImportError:
        from minimax_h3_char_ref_prompt import MinimaxH3CharRefPromptGenerator

    NODE_CLASS_MAPPINGS["MinimaxH3CharRefPromptGenerator"] = MinimaxH3CharRefPromptGenerator
    NODE_DISPLAY_NAME_MAPPINGS["MinimaxH3CharRefPromptGenerator"] = "MiniMax-H3 Char Ref Prompt Generator"
except Exception as e:
    print(f"Error initializing MiniMax-H3 Char Ref Prompt Generator node: {e}")
    traceback.print_exc()

# 3. キャラクターリファレンス ＋ 参照動画（モーション）型ノードの初期化
try:
    try:
        from .minimax_h3_char_ref_motion_prompt import MinimaxH3CharRefMotionPromptGenerator
    except ImportError:
        from minimax_h3_char_ref_motion_prompt import MinimaxH3CharRefMotionPromptGenerator

    NODE_CLASS_MAPPINGS["MinimaxH3CharRefMotionPromptGenerator"] = MinimaxH3CharRefMotionPromptGenerator
    NODE_DISPLAY_NAME_MAPPINGS["MinimaxH3CharRefMotionPromptGenerator"] = "MiniMax-H3 Char Ref + Motion Prompt Generator"
except Exception as e:
    print(f"Error initializing MiniMax-H3 Char Ref + Motion Prompt Generator node: {e}")
    traceback.print_exc()

# 4. LLMヘルパー（System Prompt Builder & Output Parser）ノードの初期化
try:
    try:
        from .minimax_h3_llm_helper import (
            MinimaxH3SystemPromptBuilder,
            MinimaxH3LLMOutputParser,
        )
    except ImportError:
        from minimax_h3_llm_helper import (
            MinimaxH3SystemPromptBuilder,
            MinimaxH3LLMOutputParser,
        )

    NODE_CLASS_MAPPINGS["MinimaxH3SystemPromptBuilder"] = MinimaxH3SystemPromptBuilder
    NODE_DISPLAY_NAME_MAPPINGS["MinimaxH3SystemPromptBuilder"] = "MiniMax-H3 System Prompt Builder"

    NODE_CLASS_MAPPINGS["MinimaxH3LLMOutputParser"] = MinimaxH3LLMOutputParser
    NODE_DISPLAY_NAME_MAPPINGS["MinimaxH3LLMOutputParser"] = "MiniMax-H3 LLM Output Parser"
except Exception as e:
    print(f"Error initializing MiniMax-H3 LLM Helper nodes: {e}")
    traceback.print_exc()

print(f"Successfully initialized {len(NODE_CLASS_MAPPINGS)} nodes for MiniMax-H3 Prompt Generator.")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

# 5. キャラクターリファレンス ＋ ファーストフレーム指定型ノードの初期化
try:
    try:
        from .minimax_h3_char_ref_first_frame_prompt import MinimaxH3CharRefFirstFramePromptGenerator
    except ImportError:
        from minimax_h3_char_ref_first_frame_prompt import MinimaxH3CharRefFirstFramePromptGenerator

    NODE_CLASS_MAPPINGS["MinimaxH3CharRefFirstFramePromptGenerator"] = MinimaxH3CharRefFirstFramePromptGenerator
    NODE_DISPLAY_NAME_MAPPINGS["MinimaxH3CharRefFirstFramePromptGenerator"] = "MiniMax-H3 Char Ref + First Frame Prompt Generator"
except Exception as e:
    print(f"Error initializing MiniMax-H3 Char Ref + First Frame Prompt Generator node: {e}")
    traceback.print_exc()