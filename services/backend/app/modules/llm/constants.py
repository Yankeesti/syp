from enum import Enum


# Deprecated: Use ModelRole from app.modules.llm.providers.base instead.
# This enum is kept for backwards compatibility but should not be used in new code.
class OllamaModel(str, Enum):
    LLAVA_13B = "llava:13b"
    LLAVA_34B = "llava:34b"
    DEEPSEEK_R1_32B = "deepseek-r1:32b"
    GPT_OSS_20B = "gpt-oss:20b"
    QWEN2_5_14B = "qwen2.5:14b"
    CODELLAMA_13B = "codellama:13b"
