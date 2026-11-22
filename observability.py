import os
import re
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from dotenv import load_dotenv, dotenv_values

# Suppress beta notices for cleaner console logs
warnings.filterwarnings("ignore", message=".*wrap_gemini is in beta.*")

# Load current environment
ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(ENV_PATH, override=False)


def reconcile_agent_routing():
    """
    LangSmith requires that if an Agent address (LANGSMITH_AGENT_ID) is set,
    LANGSMITH_PROJECT / LANGCHAIN_PROJECT must NOT be set in the environment,
    otherwise LangSmith disables tracing with:
    'A project and an address are both set in the environment, so neither outranks the other.'
    """
    agent_id = (os.getenv("LANGSMITH_AGENT_ID") or "").strip()
    if agent_id:
        os.environ.pop("LANGSMITH_PROJECT", None)
        os.environ.pop("LANGCHAIN_PROJECT", None)


reconcile_agent_routing()

# Optional LangSmith imports with graceful fallback
try:
    from langsmith import traceable as _ls_traceable
    from langsmith.wrappers import wrap_gemini as _ls_wrap_gemini
    LANGSMITH_AVAILABLE = True
except ImportError:
    _ls_traceable = None
    _ls_wrap_gemini = None
    LANGSMITH_AVAILABLE = False


def is_tracing_enabled() -> bool:
    """
    Checks if LangSmith tracing is explicitly enabled and configured.
    Supports standard LANGSMITH_* and legacy LANGCHAIN_* variables.
    """
    if not LANGSMITH_AVAILABLE:
        return False
    
    tracing_val = (
        os.getenv("LANGSMITH_TRACING")
        or os.getenv("LANGCHAIN_TRACING_V2")
        or ""
    ).strip().lower()
    
    if tracing_val not in ("true", "1", "yes", "on"):
        return False

    api_key = (
        os.getenv("LANGSMITH_API_KEY")
        or os.getenv("LANGCHAIN_API_KEY")
        or ""
    ).strip()

    return bool(api_key)


def get_agent_metadata(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Returns standard agent identification and environment metadata for LangSmith traces.
    """
    meta = {
        "agent_id": os.getenv("LANGSMITH_AGENT_ID", "agentic-orchestration"),
        "agent_environment": os.getenv("LANGSMITH_AGENT_ENVIRONMENT", "local"),
        "environment": os.getenv("LANGSMITH_AGENT_ENVIRONMENT", "local"),
    }
    if extra:
        meta.update(extra)
    return meta


def get_langsmith_config() -> Dict[str, Any]:
    """
    Returns the current LangSmith configuration, connection status, agent metadata, and project details.
    """
    api_key = (
        os.getenv("LANGSMITH_API_KEY")
        or os.getenv("LANGCHAIN_API_KEY")
        or ""
    ).strip()

    agent_id = (os.getenv("LANGSMITH_AGENT_ID") or "").strip()
    agent_env = (os.getenv("LANGSMITH_AGENT_ENVIRONMENT") or "local").strip()

    project = (
        os.getenv("LANGSMITH_PROJECT")
        or os.getenv("LANGCHAIN_PROJECT")
        or ("" if agent_id else "gemini-orchestration-studio")
    ).strip()

    endpoint = (
        os.getenv("LANGSMITH_ENDPOINT")
        or os.getenv("LANGCHAIN_ENDPOINT")
        or "https://api.smith.langchain.com"
    ).strip()

    enabled = is_tracing_enabled()
    masked_key = ""
    if api_key:
        if len(api_key) > 8:
            masked_key = f"{api_key[:4]}...{api_key[-4:]}"
        else:
            masked_key = "••••••••"

    # Deep link to agent or project view in LangSmith
    if agent_id:
        dashboard_url = "https://smith.langchain.com/o/default/agents"
    elif project and api_key:
        dashboard_url = f"https://smith.langchain.com/o/default/projects/p/{project}"
    else:
        dashboard_url = "https://smith.langchain.com"

    return {
        "available": LANGSMITH_AVAILABLE,
        "enabled": enabled,
        "project": project,
        "endpoint": endpoint,
        "agent_id": agent_id,
        "agent_environment": agent_env,
        "has_api_key": bool(api_key),
        "masked_key": masked_key,
        "dashboard_url": dashboard_url,
    }


def update_langsmith_config(
    api_key: Optional[str] = None,
    project: Optional[str] = None,
    enabled: Optional[bool] = None,
    endpoint: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_environment: Optional[str] = None,
    persist_to_env: bool = True
) -> Dict[str, Any]:
    """
    Dynamically updates LangSmith runtime environment variables,
    and optionally persists them to the local .env file.
    """
    if enabled is not None:
        val = "true" if enabled else "false"
        os.environ["LANGSMITH_TRACING"] = val
        os.environ["LANGCHAIN_TRACING_V2"] = val

    if api_key is not None:
        cleaned_key = api_key.strip()
        os.environ["LANGSMITH_API_KEY"] = cleaned_key
        os.environ["LANGCHAIN_API_KEY"] = cleaned_key

    if project is not None:
        cleaned_proj = project.strip() or "gemini-orchestration-studio"
        os.environ["LANGSMITH_PROJECT"] = cleaned_proj
        os.environ["LANGCHAIN_PROJECT"] = cleaned_proj

    if endpoint is not None:
        cleaned_end = endpoint.strip() or "https://api.smith.langchain.com"
        os.environ["LANGSMITH_ENDPOINT"] = cleaned_end
        os.environ["LANGCHAIN_ENDPOINT"] = cleaned_end

    if agent_id is not None:
        cleaned_id = agent_id.strip() or "agentic-orchestration"
        os.environ["LANGSMITH_AGENT_ID"] = cleaned_id

    if agent_environment is not None:
        cleaned_env = agent_environment.strip() or "local"
        os.environ["LANGSMITH_AGENT_ENVIRONMENT"] = cleaned_env

    if persist_to_env and ENV_PATH.exists():
        try:
            content = ENV_PATH.read_text(encoding="utf-8")
            
            def upsert_var(key: str, val: str, text: str) -> str:
                pattern = rf"^(?:#\s*)?{re.escape(key)}=.*$"
                replacement = f"{key}={val}"
                if re.search(pattern, text, flags=re.MULTILINE):
                    return re.sub(pattern, replacement, text, flags=re.MULTILINE)
                return text.rstrip() + f"\n{replacement}\n"

            if enabled is not None:
                content = upsert_var("LANGSMITH_TRACING", "true" if enabled else "false", content)
            if api_key is not None and api_key.strip():
                content = upsert_var("LANGSMITH_API_KEY", api_key.strip(), content)
            if project is not None:
                content = upsert_var("LANGSMITH_PROJECT", project.strip(), content)
            if endpoint is not None:
                content = upsert_var("LANGSMITH_ENDPOINT", endpoint.strip(), content)
            if agent_id is not None:
                content = upsert_var("LANGSMITH_AGENT_ID", agent_id.strip(), content)
            if agent_environment is not None:
                content = upsert_var("LANGSMITH_AGENT_ENVIRONMENT", agent_environment.strip(), content)

            ENV_PATH.write_text(content, encoding="utf-8")
        except Exception:
            pass

    return get_langsmith_config()


def wrap_client(client: Any, chat_name: str = "Gemini") -> Any:
    """
    Wraps a Google GenAI Client with LangSmith's wrap_gemini if tracing is enabled.
    Safely no-ops if LangSmith is unavailable or tracing is disabled.
    """
    if not is_tracing_enabled() or not LANGSMITH_AVAILABLE or _ls_wrap_gemini is None:
        return client

    try:
        # Check if client already wrapped to avoid duplicate wrap exceptions
        if (
            hasattr(client, "models")
            and hasattr(client.models, "generate_content")
            and hasattr(client.models.generate_content, "__wrapped__")
        ):
            return client
        
        tracing_extra = {
            "metadata": get_agent_metadata({"chat_name": chat_name})
        }
        return _ls_wrap_gemini(client, chat_name=chat_name, tracing_extra=tracing_extra)
    except Exception:
        return client


def traceable(*args, **kwargs) -> Callable:
    """
    Universal traceable decorator.
    If LangSmith is installed, delegates directly to langsmith.traceable.
    If LangSmith is unavailable, gracefully acts as a zero-cost pass-through decorator.
    """
    if LANGSMITH_AVAILABLE and _ls_traceable is not None:
        return _ls_traceable(*args, **kwargs)

    # Fallback no-op decorator
    def noop_decorator(func: Callable) -> Callable:
        return func

    if len(args) == 1 and callable(args[0]) and not kwargs:
        return args[0]
    return noop_decorator
