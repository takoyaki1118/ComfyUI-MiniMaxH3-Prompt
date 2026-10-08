from .minimax_h3_prompt import MinimaxH3PromptGenerator

NODE_CLASS_MAPPINGS = {
    "MinimaxH3PromptGenerator": MinimaxH3PromptGenerator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MinimaxH3PromptGenerator": "MiniMax-H3 Prompt Generator"
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]