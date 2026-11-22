import os
import re
import json
from typing import Generator, Dict, Any, Optional, List
from dotenv import load_dotenv
import observability

load_dotenv()

SUPPORTED_CHAT_ONLY_MODELS = {
    "gemini-3.7-flash": "gemini-3.7-flash",
    "3.7": "gemini-3.7-flash",
    "gemini-3.6-flash": "gemini-3.6-flash",
    "3.6": "gemini-3.6-flash",
    "gemini-3.1-flash-lite": "gemini-3.1-flash-lite",
    "3.1": "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite": "gemini-3.5-flash-lite",
    "3.5": "gemini-3.5-flash-lite",
    "gemini-4-hydrogen": "gemini-4-hydrogen",
    "hydrogen": "gemini-4-hydrogen",
    "4-hydrogen": "gemini-4-hydrogen",
    "gemini-3.8-flash": "gemini-3.8-flash",
    "3.8": "gemini-3.8-flash",
}

DEFAULT_CHAT_ONLY_MODEL = "gemini-3.1-flash-lite"


STOP_REQUESTED = False

def request_stop() -> None:
    """Signals direct chat stream generator to halt immediately."""
    global STOP_REQUESTED
    STOP_REQUESTED = True

def reset_stop() -> None:
    """Resets the stop flag before direct chat begins."""
    global STOP_REQUESTED
    STOP_REQUESTED = False

def is_stop_requested() -> bool:
    """Returns True if a stop has been requested."""
    global STOP_REQUESTED
    return STOP_REQUESTED


def get_genai_client(api_key: Optional[str] = None):
    """Initializes Google GenAI client with custom or fresh env API key."""
    from google import genai
    from google.genai import types
    from pathlib import Path
    if api_key and api_key.strip():
        key = api_key.strip()
    else:
        try:
            from dotenv import dotenv_values
            env_vals = dotenv_values(Path(__file__).parent / ".env")
            key = env_vals.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
        except Exception:
            key = os.getenv("GEMINI_API_KEY")
    http_opts = types.HttpOptions(
        api_version="v1beta",
        timeout=90000,
        retry_options=types.HttpRetryOptions(attempts=1)
    )
    client = genai.Client(api_key=key, http_options=http_opts)
    return observability.wrap_client(client, chat_name="Gemini Direct Chat")


@observability.traceable(
    name="Direct Chat Stream",
    run_type="chain",
    tags=["agent", "direct-chat", "streaming"],
    metadata=observability.get_agent_metadata()
)
def execute_direct_chat_stream(
    message: str,
    model: str = DEFAULT_CHAT_ONLY_MODEL,
    temperature: float = 0.7,
    thinking_budget: int = 0,
    history: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    api_key: Optional[str] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Dedicated, standalone single-model Chat-Only pipeline.
    Bypasses all multi-agent decomposition and reasoning overhead.
    Streams tokens directly for conversational QA, coding, learning, and HTML generation.
    """
    from google.genai import types

    # Clean model resolution with fallback
    active_model = SUPPORTED_CHAT_ONLY_MODELS.get(model.strip().lower(), DEFAULT_CHAT_ONLY_MODEL)
    client = get_genai_client(api_key=api_key)

    # Format contents from previous history if provided
    contents = []
    if history:
        for msg in history[-8:]:  # preserve recent context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if content:
                contents.append(f"{role.capitalize()}: {content}")
        contents.append(f"User: {message}")
    else:
        contents = [message]

    # Convert any multimodal image attachments to Gemini Part objects
    if attachments:
        import base64
        for att in attachments:
            b64_str = att.get("data_b64") or ""
            m_type = att.get("mime_type") or "image/png"
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            if b64_str:
                try:
                    img_bytes = base64.b64decode(b64_str.strip())
                    contents.append(types.Part.from_bytes(data=img_bytes, mime_type=m_type))
                except Exception:
                    pass

    # Configure generation parameters
    gen_config_kwargs: Dict[str, Any] = {
        "temperature": max(0.0, min(float(temperature), 2.0)),
        "system_instruction": (
            "You are an expert, direct AI assistant running in Chat-Only mode.\n"
            "Provide clear, accurate, conversational responses.\n"
            "If the user asks for code, web components, or HTML/CSS, provide clean, production-ready code with language tags (e.g. ```html ... ``` or ```css ... ```)."
        )
    }

    if thinking_budget > 0:
        gen_config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=int(thinking_budget))

    config = types.GenerateContentConfig(**gen_config_kwargs)

    # Fallback chain: requested model -> fallback chain
    models_to_try = [active_model]
    for fallback_cand in ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.7-flash", "gemini-3.6-flash"]:
        if fallback_cand not in models_to_try:
            models_to_try.append(fallback_cand)

    last_error = None
    for target_model in models_to_try:
        try:
            resp_stream = client.models.generate_content_stream(
                model=target_model,
                contents=contents,
                config=config
            )

            full_thought = ""
            full_answer = ""

            for chunk in resp_stream:
                if is_stop_requested():
                    yield {"type": "token", "content": "\n\n*[⏹️ Execution stopped by user]*"}
                    return
                if chunk.candidates:
                    cand = chunk.candidates[0]
                    if cand.content and cand.content.parts:
                        for part in cand.content.parts:
                            if getattr(part, "thought", False):
                                t_text = part.text or ""
                                full_thought += t_text
                                yield {"type": "thought", "content": t_text}
                            elif part.text:
                                ans_text = part.text
                                full_answer += ans_text
                                yield {"type": "token", "content": ans_text}

            # Signal completion
            yield {
                "type": "done",
                "full_answer": full_answer,
                "full_thought": full_thought,
                "model_used": target_model,
                "temperature": temperature,
                "thinking_budget": thinking_budget
            }
            return

        except Exception as e:
            last_error = e
            # Try next model in fallback list if server error or 503
            continue

    # If all models in the fallback chain failed
    yield {"type": "error", "error": str(last_error or "Direct chat failed.")}
