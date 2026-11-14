"""
LLM-backed ad text generator (placeholder).

`emergentintegrations` is not publicly installable from PyPI, so until a real
LLM client is wired in this returns a deterministic placeholder. The function
signature and UNIVERSAL_KEY contract match what the frontend expects
({"generated_text": ...}). To integrate a real provider, implement the marked
section below and keep the return type as `str`.
"""
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


def generate_ad_text(prompt: str) -> str:
    """Generates ad text based on a prompt."""
    universal_key = os.getenv("UNIVERSAL_KEY")

    if not universal_key:
        return (
            "Warning: UNIVERSAL_KEY is not configured. Set it in app/backend/.env. "
            "Returning placeholder text."
        )

    # --- Real LLM integration goes here, e.g.: ---------------------------------
    # from emergentintegrations.llm.chat import LlmChat, UserMessage
    # llm = LlmChat(api_key=universal_key)
    # response = llm.get_response([UserMessage(prompt)])
    # return response
    # ---------------------------------------------------------------------------
    return (
        f"This is a generated ad for the prompt: '{prompt}' "
        "(placeholder — no LLM provider is wired up yet)"
    )
