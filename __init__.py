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

print(f"Successfully initialized {len(NODE_CLASS_MAPPINGS)} nodes for MiniMax-H3 Prompt Generator.")

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]