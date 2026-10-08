import traceback

print("Initializing MiniMax-H3 Prompt Generator Node...")

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

try:
    try:
        from .minimax_h3_prompt import MinimaxH3PromptGenerator
    except ImportError:
        from minimax_h3_prompt import MinimaxH3PromptGenerator

    NODE_CLASS_MAPPINGS["MinimaxH3PromptGenerator"] = MinimaxH3PromptGenerator
    NODE_DISPLAY_NAME_MAPPINGS["MinimaxH3PromptGenerator"] = "MiniMax-H3 Prompt Generator"

    print(f"Successfully initialized {len(NODE_CLASS_MAPPINGS)} node for MiniMax-H3 Prompt Generator.")

except Exception as e:
    print(f"Error initializing MiniMax-H3 Prompt Generator node: {e}")
    traceback.print_exc()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]