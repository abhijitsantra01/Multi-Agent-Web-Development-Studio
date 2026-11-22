import os
import re
import sys
import json
import base64
import shutil
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
import observability

load_dotenv(override=True)

# Ensure utf-8 stdout in Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STOP_REQUESTED = False

def request_stop() -> None:
    """Signals all running orchestration workers and LLM calls to immediately stop."""
    global STOP_REQUESTED
    STOP_REQUESTED = True

def reset_stop() -> None:
    """Clears the force stop flag prior to beginning a new generation run."""
    global STOP_REQUESTED
    STOP_REQUESTED = False

def is_stop_requested() -> bool:
    """Returns True if a user-requested force stop has been triggered."""
    global STOP_REQUESTED
    return STOP_REQUESTED

USER_OVERRIDE_KEY: str | None = None

def set_user_api_key(api_key: str | None) -> None:
    """Sets a runtime user API key with priority over .env."""
    global USER_OVERRIDE_KEY
    USER_OVERRIDE_KEY = api_key.strip() if api_key and api_key.strip() else None

def get_active_gemini_key() -> str:
    """Returns User API key if provided; otherwise falls back to fresh .env key on disk."""
    if USER_OVERRIDE_KEY:
        return USER_OVERRIDE_KEY
    try:
        from dotenv import dotenv_values
        env_vals = dotenv_values(Path(__file__).parent / ".env")
        if env_vals.get("GEMINI_API_KEY"):
            return env_vals["GEMINI_API_KEY"].strip()
    except Exception:
        pass
    load_dotenv(override=True)
    return os.getenv("GEMINI_API_KEY") or ""

def get_genai_client(api_key: str | None = None):
    key = api_key or get_active_gemini_key()
    http_opts = types.HttpOptions(
        api_version="v1beta",
        timeout=90000,
        retry_options=types.HttpRetryOptions(attempts=1)
    )
    client = genai.Client(api_key=key, http_options=http_opts)
    return observability.wrap_client(client, chat_name="Gemini Orchestrator")

def get_incremented_path(folder: Path, base_name: str, ext: str) -> Path:
    """
    Returns base_name.ext if it doesn't exist,
    otherwise base_name_1.ext, base_name_2.ext, etc.
    """
    if not ext.startswith("."):
        ext = f".{ext}"
    target = folder / f"{base_name}{ext}"
    if not target.exists():
        return target
    counter = 1
    while True:
        candidate = folder / f"{base_name}_{counter}{ext}"
        if not candidate.exists():
            return candidate
        counter += 1


def extract_html_and_css(text: str) -> tuple[str | None, str | None]:
    """
    Extracts HTML and CSS from model output.
    """
    html = None
    css = None

    # 1. Search for HTML code block (case-insensitive, allowing filename or attributes)
    html_match = re.search(r"```(?:html|htm)[^\n]*\n(.*?)(?:```|$)", text, re.DOTALL | re.IGNORECASE)
    if html_match:
        html = html_match.group(1).strip()
    elif "<!DOCTYPE html>" in text or "<html" in text:
        raw_match = re.search(r"(<!DOCTYPE html>.*?</html>|<html.*?</html>)", text, re.DOTALL | re.IGNORECASE)
        if raw_match:
            html = raw_match.group(1).strip()
        else:
            generic_match = re.search(r"```[^\n]*\n(.*?)(?:```|$)", text, re.DOTALL)
            if generic_match and ("<html" in generic_match.group(1).lower() or "<!doctype" in generic_match.group(1).lower()):
                html = generic_match.group(1).strip()

    # 2. Search for CSS code block (case-insensitive, allowing filename or attributes)
    css_match = re.search(r"```css[^\n]*\n(.*?)(?:```|$)", text, re.DOTALL | re.IGNORECASE)
    if css_match:
        css = css_match.group(1).strip()

    # 3. If no separate CSS block, extract from <style> tags inside the HTML
    if not css and html:
        style_matches = re.findall(r"<style[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE)
        if style_matches:
            css = "\n\n".join(s.strip() for s in style_matches if s.strip())

    return html, css


def save_response_artifacts(response, text: str, output_dir: Path) -> list[Path]:
    """
    Detects and saves any returned output (HTML, CSS, binary images, base64 images,
    SVGs, scripts) with auto-incremented file numbers if files already exist.
    """
    import base64
    saved = []

    # 1. Check for Multimodal / Binary Image parts in SDK response
    if hasattr(response, "candidates") and response.candidates:
        for cand in response.candidates:
            if hasattr(cand, "content") and cand.content and hasattr(cand.content, "parts"):
                for part in cand.content.parts:
                    if hasattr(part, "inline_data") and part.inline_data:
                        raw_bytes = part.inline_data.data
                        mime = getattr(part.inline_data, "mime_type", "image/png").lower()
                        ext = ".png"
                        if "jpeg" in mime or "jpg" in mime:
                            ext = ".jpg"
                        elif "webp" in mime:
                            ext = ".webp"
                        elif "gif" in mime:
                            ext = ".gif"
                        target = get_incremented_path(output_dir, "image", ext)
                        target.write_bytes(raw_bytes)
                        saved.append(target)

    # 2. Check for Base64 Data URI Images in text (data:image/...;base64,...)
    b64_matches = re.findall(r"data:image/([a-zA-Z0-9_\-+]+);base64,([A-Za-z0-9+/=\s]+)", text)
    for img_format, b64_str in b64_matches:
        try:
            raw_bytes = base64.b64decode(b64_str.strip())
            ext = f".{img_format.lower()}"
            if ext == ".jpeg":
                ext = ".jpg"
            target = get_incremented_path(output_dir, "image", ext)
            target.write_bytes(raw_bytes)
            saved.append(target)
        except Exception:
            pass

    # 3. Check for standalone SVG images
    # Matches ```svg ... ``` or standalone <svg ... </svg>
    svg_matches = re.findall(r"```(?:svg|xml)?\s*\n\s*(<svg[\s\S]*?</svg>)\s*```", text, re.IGNORECASE)
    if not svg_matches and not ("<!DOCTYPE html>" in text or "<html" in text):
        svg_matches = re.findall(r"(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)

    for svg_content in svg_matches:
        target = get_incremented_path(output_dir, "image", ".svg")
        target.write_text(svg_content.strip(), encoding="utf-8")
        saved.append(target)

    # 4. Check for HTML and CSS
    html, css = extract_html_and_css(text)
    if html:
        main_index = output_dir / "index.html"
        main_index.write_text(html, encoding="utf-8")
        saved.append(main_index)

    if css:
        main_css = output_dir / "styles.css"
        main_css.write_text(css, encoding="utf-8")
        saved.append(main_css)

    # 5. Check for any other code formats (JavaScript, JSON, Python)
    for lang, base, ext in [
        ("javascript", "script", ".js"),
        ("js", "script", ".js"),
        ("json", "data", ".json"),
        ("python", "script", ".py"),
    ]:
        code_match = re.search(rf"```{lang}[^\n]*\n(.*?)(?:```|$)", text, re.DOTALL | re.IGNORECASE)
        if code_match and not html:
            target = get_incremented_path(output_dir, base, ext)
            target.write_text(code_match.group(1).strip(), encoding="utf-8")
            saved.append(target)

    return saved


import json
import project_store

DEFAULT_COMPLEX_MODEL = os.getenv("GEMINI_COMPLEX_MODEL", "gemini-3.6-flash")
MODEL_COMPLEX = DEFAULT_COMPLEX_MODEL
DEFAULT_LITE_MODEL = os.getenv("GEMINI_LITE_MODEL", "gemini-3.1-flash-lite")

# Model Circuit Breaker & Health Tracking
import time
DEGRADED_MODELS: dict[str, float] = {}  # model_name -> cooldown_expiry_timestamp
DEGRADED_COOLDOWN_SECONDS = 300.0  # 5 minutes

def mark_model_degraded(model_name: str, duration: float = DEGRADED_COOLDOWN_SECONDS) -> None:
    """Marks a model as temporarily degraded or unavailable so fallback chains bypass it."""
    clean = (model_name or "").strip()
    if clean:
        DEGRADED_MODELS[clean] = time.time() + duration

def mark_model_healthy(model_name: str) -> None:
    """Clears degraded status when a model succeeds."""
    clean = (model_name or "").strip()
    if clean:
        DEGRADED_MODELS.pop(clean, None)

def is_model_degraded(model_name: str) -> bool:
    """Returns True if the model is currently marked as degraded."""
    clean = (model_name or "").strip()
    exp = DEGRADED_MODELS.get(clean)
    if not exp:
        return False
    if time.time() > exp:
        DEGRADED_MODELS.pop(clean, None)
        return False
    return True

# Optimized Fallback Chains (prioritizing responsive & verified models)
COMPLEX_FALLBACK_CHAINS = {
    "gemini-3.6-flash": ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.1-flash-lite"],
    "gemini-3.7-flash": ["gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"],
    "gemini-4-hydrogen": ["gemini-4-hydrogen", "gemini-3.6-flash", "gemini-3.1-flash-lite"],
    "gemini-3.8-flash": ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite"],
}

LITE_FALLBACK_CHAINS = {
    "gemini-3.1-flash-lite": ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.6-flash"],
    "gemini-3.5-flash-lite": ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"],
    "gemini-3.6-flash": ["gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-3.5-flash-lite"],
}

SUPPORTED_COMPLEX_MODELS = {
    "3.7": "gemini-3.7-flash",
    "gemini-3.7-flash": "gemini-3.7-flash",
    "3.6": "gemini-3.6-flash",
    "gemini-3.6-flash": "gemini-3.6-flash",
    "3.8": "gemini-3.8-flash",
    "gemini-3.8-flash": "gemini-3.8-flash",
    "hydrogen": "gemini-4-hydrogen",
    "4-hydrogen": "gemini-4-hydrogen",
    "gemini-4-hydrogen": "gemini-4-hydrogen",
    "gemini-hydrogen": "gemini-4-hydrogen",
    "gemini-4": "gemini-4-hydrogen",
}

SUPPORTED_LITE_MODELS = {
    "3.1": "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite": "gemini-3.1-flash-lite",
    "3.5": "gemini-3.5-flash-lite",
    "gemini-3.5-flash-lite": "gemini-3.5-flash-lite",
    "3.6": "gemini-3.6-flash",
    "gemini-3.6-flash": "gemini-3.6-flash",
}


def resolve_fallback_chain(model_name: str) -> list[str]:
    m = (model_name or "").strip().lower()
    base_chain = []
    if m in SUPPORTED_COMPLEX_MODELS and SUPPORTED_COMPLEX_MODELS[m] in COMPLEX_FALLBACK_CHAINS:
        base_chain = list(COMPLEX_FALLBACK_CHAINS[SUPPORTED_COMPLEX_MODELS[m]])
    elif m in COMPLEX_FALLBACK_CHAINS:
        base_chain = list(COMPLEX_FALLBACK_CHAINS[m])
    elif m in LITE_FALLBACK_CHAINS:
        base_chain = list(LITE_FALLBACK_CHAINS[m])
    elif "lite" in m or "3.1" in m or "3.5" in m:
        base_chain = ["gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.6-flash"]
    else:
        base_chain = ["gemini-3.6-flash", "gemini-3.7-flash", "gemini-3.1-flash-lite"]

    # Deduplicate while preserving sequence
    seen = set()
    deduped = []
    for x in base_chain:
        if x not in seen:
            seen.add(x)
            deduped.append(x)

    # Reorder dynamically: healthy models first, degraded models pushed to the tail
    healthy = [x for x in deduped if not is_model_degraded(x)]
    degraded = [x for x in deduped if is_model_degraded(x)]
    return healthy + degraded if healthy else deduped


def prepare_gemini_multimodal_parts(attachments: list[dict] | None) -> list[types.Part]:
    """Converts uploaded base64 files into Gemini multimodal inline Part objects."""
    parts = []
    if not attachments:
        return parts

    for att in attachments:
        data_b64 = att.get("data_b64") or ""
        mime_type = att.get("mime_type") or "image/png"
        if "," in data_b64:
            data_b64 = data_b64.split(",", 1)[1]

        if data_b64 and ("image" in mime_type.lower() or mime_type in ["application/pdf"]):
            try:
                raw_bytes = base64.b64decode(data_b64.strip())
                parts.append(types.Part.from_bytes(data=raw_bytes, mime_type=mime_type))
            except Exception:
                pass
    return parts


def save_project_attachments(project_id: str, attachments: list[dict] | None) -> list[dict]:
    """
    Saves uploaded attachments directly into output/projects/{project_id}/assets/.
    Also creates convenient aliases (e.g. assets/logo.png) if it is an image/logo,
    and returns a list of asset dicts with rel_path, filename, is_image, etc.
    """
    saved_assets = []
    if not attachments:
        return saved_assets

    p_dir = project_store.get_project_dir(project_id)
    assets_dir = p_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    has_logo_alias = False

    for idx, att in enumerate(attachments):
        orig_name = att.get("name") or f"upload_{idx+1}.png"
        clean_name = os.path.basename(orig_name.replace("\\", "/")).strip()
        if not clean_name:
            clean_name = f"attachment_{idx+1}.png"

        data_b64 = att.get("data_b64") or ""
        mime_type = att.get("mime_type") or "image/png"
        if "," in data_b64:
            data_b64 = data_b64.split(",", 1)[1]

        raw_bytes = None
        if data_b64:
            try:
                raw_bytes = base64.b64decode(data_b64.strip())
            except Exception:
                pass
        elif att.get("content"):
            raw_bytes = att["content"].encode("utf-8")

        if raw_bytes:
            target_path = assets_dir / clean_name
            target_path.write_bytes(raw_bytes)
            is_image = mime_type.startswith("image/") or target_path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".svg"]

            asset_info = {
                "name": clean_name,
                "rel_path": f"assets/{clean_name}",
                "size": len(raw_bytes),
                "mime_type": mime_type,
                "is_image": is_image,
                "is_logo": False,
                "logo_path": f"assets/{clean_name}"
            }

            if is_image and not has_logo_alias:
                ext = target_path.suffix.lower() or ".png"
                logo_alias_name = f"logo{ext}"
                logo_alias_path = assets_dir / logo_alias_name
                try:
                    if logo_alias_path.resolve() != target_path.resolve():
                        logo_alias_path.write_bytes(raw_bytes)
                except Exception:
                    pass
                asset_info["logo_path"] = f"assets/{logo_alias_name}"
                asset_info["is_logo"] = True
                has_logo_alias = True

            saved_assets.append(asset_info)

    # Mirror into .backup/assets/ if .backup exists so revert/fork works seamlessly
    backup_dir = p_dir / ".backup" / "assets"
    if (p_dir / ".backup").exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        for item in assets_dir.iterdir():
            if item.is_file():
                try:
                    (backup_dir / item.name).write_bytes(item.read_bytes())
                except Exception:
                    pass

    return saved_assets


@observability.traceable(
    name="Vision & Brand Agent",
    run_type="chain",
    tags=["agent", "vision", "multimodal"]
)
def analyze_brand_and_vision_context(
    prompt: str,
    attachments: list[dict] | None,
    on_event: callable = None
) -> dict:
    """
    Uses Gemini Multimodal Vision to inspect uploaded logos/images and extract
    verified brand guidelines: exact company name, tagline, color palette, and visual identity.
    """
    parts = prepare_gemini_multimodal_parts(attachments)
    if not parts:
        return {}

    if on_event:
        on_event("🔍 [Vision Agent]: Inspecting uploaded brand asset for visual identity, typography & colors...")

    vision_prompt = (
        f"You are a Principal Brand Identity & UI Design Specialist.\n"
        f"Analyze the attached image/logo carefully in context of the user request: \"{prompt}\".\n"
        "Extract the brand details and output strictly valid JSON in this exact structure:\n"
        "{\n"
        '  "company_name": "Exact text of the company/brand name visible in the logo (e.g. Bharat Logistics)",\n'
        '  "tagline": "Exact slogan or subtitle visible in the logo (e.g. Reliable Goods Transport)",\n'
        '  "primary_color": "Hex code for the primary brand color (e.g. #0f2b48 or #1e3a8a for navy blue)",\n'
        '  "secondary_color": "Hex code for secondary accent color (e.g. #f58220 or #ea580c for orange)",\n'
        '  "accent_color": "Hex code for highlight or gold/amber trim",\n'
        '  "background_tone": "clean-light or rich-commercial",\n'
        '  "color_palette_summary": "Description of colors (e.g. Navy Blue, Industrial Transport Orange, Clean White)",\n'
        '  "logo_description": "Description of imagery and symbols in the logo (e.g. Truck inside circular India map outline)",\n'
        '  "design_direction": "Clean, realistic, professional commercial design suited for this industry with real human trust elements"\n'
        "}"
    )

    try:
        raw = call_gemini_model(
            model="gemini-3.6-flash",
            contents=[vision_prompt],
            multimodal_parts=parts,
            temperature=0.1,
            response_mime_type="application/json",
            custom_chain=["gemini-3.6-flash", "gemini-3.1-flash-lite"]
        )
        parsed = None
        if raw:
            try:
                parsed = json.loads(raw.strip())
            except Exception:
                m = re.search(r"\{[\s\S]*\}", raw)
                if m:
                    parsed = json.loads(m.group(0))

        if parsed and parsed.get("company_name"):
            c_name = parsed["company_name"]
            c_colors = parsed.get("color_palette_summary") or f"{parsed.get('primary_color', '')}, {parsed.get('secondary_color', '')}"
            if on_event:
                on_event(f"✓ [Vision Agent]: Brand identified: '{c_name}' | Palette: {c_colors}")
            return parsed
    except Exception as ex:
        if on_event:
            on_event(f"⚠️ [Vision Agent]: Vision inspection notice: {ex}")

    return {}


def call_gemini_model(
    model: str,
    contents: list | str,
    system_instruction: str = "",
    temperature: float = 0.7,
    thinking_budget: int = 0,
    on_event: callable = None,
    custom_chain: list[str] | None = None,
    response_mime_type: str | None = None,
    multimodal_parts: list | None = None
) -> str:
    """
    Helper to call Gemini models using Google GenAI SDK with graceful retry and response parsing.
    Supports user-specified fallback chains:
    - Gemini 3.8 Flash -> Gemini 3.6 Flash -> Gemini 2.5 Flash
    - Gemini 3.5 Flash Lite -> Gemini 3.1 Flash Lite -> Gemini 2.5 Flash
    - Normal Chat: Gemini 2.5 Flash -> Gemini 3.1 Flash Lite -> Gemini 3.5 Flash Lite
    """
    import time
    config_args = {
        "temperature": max(0.0, min(float(temperature), 2.0)),
        "max_output_tokens": 65536
    }
    if response_mime_type:
        config_args["response_mime_type"] = response_mime_type
    if system_instruction:
        config_args["system_instruction"] = system_instruction
    if thinking_budget is not None and int(thinking_budget) > 0:
        config_args["thinking_config"] = types.ThinkingConfig(
            thinking_budget=int(thinking_budget),
            include_thoughts=True
        )
    # When thinking_budget <= 0, do not pass thinking_config to avoid 400 INVALID_ARGUMENT from Google GenAI API

    config = types.GenerateContentConfig(**config_args)
    if isinstance(contents, str):
        contents_list = [contents]
    elif isinstance(contents, list):
        contents_list = list(contents)
    else:
        contents_list = [str(contents)]

    if multimodal_parts:
        contents_list.extend(multimodal_parts)

    if is_stop_requested():
        raise InterruptedError("Execution stopped by user.")

    models_to_try = list(custom_chain) if custom_chain else resolve_fallback_chain(model)
    last_err = None

    for idx, target_model in enumerate(models_to_try):
        if is_stop_requested():
            raise InterruptedError("Execution stopped by user.")
        next_model = models_to_try[idx + 1] if idx + 1 < len(models_to_try) else None
        for attempt in range(2):
            if is_stop_requested():
                raise InterruptedError("Execution stopped by user.")
            try:
                active_client = get_genai_client()
                response = active_client.models.generate_content(
                    model=target_model,
                    contents=contents_list,
                    config=config
                )

                answer_parts = []
                if hasattr(response, "candidates") and response.candidates:
                    cand = response.candidates[0]
                    if cand.content and hasattr(cand.content, "parts"):
                        for part in cand.content.parts:
                            if not getattr(part, "thought", False) and part.text:
                                answer_parts.append(part.text)

                result_text = "".join(answer_parts) if answer_parts else (response.text or "")
                mark_model_healthy(target_model)
                return result_text
            except Exception as e:
                last_err = e
                err_str = str(e).lower()

                # If response_mime_type is unsupported on this specific model, retry without it
                if ("response_mime_type" in err_str or "mime" in err_str) and hasattr(config, "response_mime_type") and config.response_mime_type:
                    config.response_mime_type = None
                    continue

                # If thinking config is unsupported on this specific model, retry without it
                if ("thinking" in err_str or "unsupported" in err_str) and hasattr(config, "thinking_config") and config.thinking_config:
                    config.thinking_config = None
                    continue
                is_transient = (
                    "503" in err_str or "unavailable" in err_str or 
                    "high demand" in err_str or "resource" in err_str or
                    "429" in err_str or "quota" in err_str or
                    "404" in err_str or "not found" in err_str or
                    "timeout" in err_str or "deadline" in err_str or
                    "connection" in err_str or "servererror" in err_str
                )
                if next_model:
                    mark_model_degraded(target_model)
                    fallback_msg = f"⚠️ [Model Fallback] {target_model} unavailable ({type(e).__name__}). Failing over to {next_model}..."
                    if on_event:
                        on_event(fallback_msg)
                    else:
                        print(fallback_msg)
                    break  # Fail over immediately to next_model in chain
                elif is_transient and attempt == 0:
                    time.sleep(1.0)
                    continue
                else:
                    mark_model_degraded(target_model)
                    raise e

    if last_err:
        raise last_err
    return ""


def extract_worker_code_snippet(raw_output: str, target_file: str) -> str:
    """Extracts clean code content from worker output fences."""
    if not raw_output:
        return ""
    # Check if output contains search/replace blocks
    if "<<<<<<< SEARCH" in raw_output and ">>>>>>>" in raw_output:
        m_diff = re.search(r"(<<<<<<< SEARCH[\s\S]*?>>>>>>>)", raw_output)
        if m_diff:
            return m_diff.group(1).strip()
    
    # Check for markdown code fences
    m = re.search(r"```(?:[a-zA-Z0-9_\-\.]+)?(?:\s+filename=[\"'][^\"']+[\"'])?\s*\n([\s\S]*?)(?:```|$)", raw_output)
    if m:
        return m.group(1).strip()
    return raw_output.strip()


@observability.traceable(
    name="Intent Router Agent",
    run_type="chain",
    tags=["agent", "intent-router"]
)
def classify_conversation_intent(
    user_prompt: str,
    project_id: str | None = None,
    has_files: bool = False,
    lite_model: str = DEFAULT_LITE_MODEL,
    on_event: callable = None
) -> dict:
    """
    Intelligent Intent Classifier:
    Determines if user prompt is a normal conversation / question / discussion ('chat'),
    an explicit instruction to update code/styling/components ('upgrade'),
    or a new project creation request ('create').
    """
    system_instruction = (
        "You are an expert Intent Triage Router for an AI Web Development Studio.\n"
        "Categorize the user's message into one of three intents:\n\n"
        "1. 'chat': The user is having a normal talk, asking questions, seeking explanations or architectural breakdowns, "
        "asking what/how/why, greeting, or discussing project ideas WITHOUT giving an imperative command to modify or write files.\n"
        "Examples of 'chat': 'How does this work?', 'Can you explain the CSS?', 'What fonts did you use?', 'Hello', "
        "'What do you think about a pricing table?', 'Show me where the navbar is defined'.\n\n"
        "2. 'upgrade': The user is explicitly instructing to update, edit, modify, add, delete, style, or fix code in the existing project.\n"
        "Examples of 'upgrade': 'Add a sign in button', 'Change the background to dark blue', 'Fix the navbar alignment', "
        "'Make the cards 3 columns', 'Update the title to Acme Corp'.\n\n"
        "3. 'create': The user is requesting to build or generate a brand new landing page or app from scratch.\n"
        "Examples of 'create': 'Create a luxury smartwatch landing page', 'Build a fintech crypto dashboard'.\n\n"
        "CRITICAL RULES:\n"
        "- If user is asking a question or just talking, ALWAYS classify as 'chat'.\n"
        "- Only classify as 'upgrade' if there is an explicit request to modify code/files.\n"
        "- If no project exists and user asks to build or generate a page, classify as 'create'.\n\n"
        "Output strictly valid JSON:\n"
        "{\n"
        '  "intent": "chat" | "upgrade" | "create",\n'
        '  "reason": "Brief explanation"\n'
        "}"
    )

    prompt = (
        f"User Message: {user_prompt}\n"
        f"Active Project: {project_id or 'None'}\n"
        f"Has Existing Project Files: {has_files}\n\n"
        f"Classify intent:"
    )

    try:
        raw = call_gemini_model(
            model=lite_model,
            contents=[prompt],
            system_instruction=system_instruction,
            temperature=0.1,
            custom_chain=["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
        )
        m = re.search(r"```(?:json)?\s*\n([\s\S]*?)\n```", raw)
        text_to_parse = m.group(1) if m else raw
        result = json.loads(text_to_parse)
        if result.get("intent") in ["chat", "upgrade", "create"]:
            if on_event:
                on_event(f"🧠 [Intent Router]: Detected '{result['intent'].upper()}' intent ({result.get('reason', '')})")
            return result
    except Exception:
        pass

    # Heuristic fallback
    p_lower = user_prompt.lower().strip()
    is_question = (
        p_lower.startswith(("how", "what", "why", "who", "where", "can you explain", "explain", "tell me", "is there", "does it", "hello", "hi", "hey")) or
        p_lower.endswith("?")
    )
    if is_question:
        return {"intent": "chat", "reason": "Question detected in heuristic fallback"}
    if has_files:
        return {"intent": "upgrade", "reason": "Defaulting to upgrade for existing project"}
    return {"intent": "create", "reason": "Defaulting to initial creation"}


@observability.traceable(
    name="Conversational Chat Agent",
    run_type="chain",
    tags=["agent", "chat"]
)
def execute_normal_chat(
    project_id: str | None,
    user_prompt: str,
    lite_model: str = DEFAULT_LITE_MODEL,
    temperature: float = 0.7,
    thinking_budget: int = 0,
    on_event: callable = None
) -> dict:
    """
    Normal Chat Handler:
    Uses Flash Lite models for normal chatting about project details,
    code explanations, and architecture understanding WITHOUT modifying or executing files.
    """
    if on_event:
        on_event(f"💬 [{lite_model} (Temp: {temperature:.2f}, Budget: {thinking_budget})]: Answering in conversational mode (No code execution)...")

    project_context = ""
    if project_id:
        try:
            files = project_store.get_project_files(project_id)
            summaries = []
            for fn, finfo in files.items():
                if not finfo.get("is_binary") and finfo.get("content"):
                    content = finfo["content"]
                    summaries.append(f"=== File: {fn} ({len(content)} chars) ===\n{content[:3000]}")
            if summaries:
                project_context = f"\n\nContext of Project {project_id}:\n" + "\n\n".join(summaries)
        except Exception:
            pass

    system_instruction = (
        "You are an expert AI Web Development Assistant running on Gemini Flash Lite.\n"
        "The user is having a normal chat, asking questions, or discussing their web project.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Answer clearly, accurately, and conversationally.\n"
        "2. Do NOT output SEARCH/REPLACE diff blocks and do NOT generate replacement files.\n"
        "3. Explain the architecture, styling, components, or reasoning based on the project code provided.\n"
        "4. Be friendly, concise, and helpful."
    )

    contents = [
        f"User Prompt: {user_prompt}{project_context}"
    ]

    # Ensure custom fallback chain begins with the user's selected chat model
    chain = [lite_model]
    for m in ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-2.5-flash"]:
        if m not in chain:
            chain.append(m)

    answer = call_gemini_model(
        model=lite_model,
        contents=contents,
        system_instruction=system_instruction,
        temperature=temperature,
        thinking_budget=thinking_budget,
        custom_chain=chain,
        on_event=on_event
    )

    if on_event:
        on_event("✓ Conversational response complete.")

    return {
        "project_id": project_id,
        "saved_files": [],
        "assembled_text": answer,
        "is_chat": True
    }


@observability.traceable(
    name="Upgrade Complexity Classifier",
    run_type="chain",
    tags=["agent", "classifier"]
)
def classify_upgrade_complexity(
    user_prompt: str,
    baseline_files: dict,
    lite_model: str = DEFAULT_LITE_MODEL,
    on_event: callable = None
) -> dict:
    """
    Tier Router (Flash Lite):
    Evaluates whether the user's upgrade prompt can be handled by Flash Lite (Tier 1)
    or requires Gemini 3.8 Flash (Tier 2).
    """
    if on_event:
        on_event(f"🚦 [{lite_model} Router]: Analyzing task complexity & resource routing...")

    system_instruction = (
        "You are an expert Frontend Architect Triage Router running on Gemini Flash Lite.\n"
        "Evaluate the user's project modification request and classify it into TIER 1 (LITE) or TIER 2 (COMPLEX).\n\n"
        "TIER 1 (LITE) CRITERIA (Localized tweaks only):\n"
        "- Purely localized cosmetic or visual styling updates on a single element or container (e.g. changing one button color, one font size, padding on a specific card).\n"
        "- Isolated static copy/text changes (rewording a specific heading, subtitle, or label).\n"
        "- Minor static markup adjustments that do NOT affect overall theme tokens, colors, or multiple components.\n\n"
        "TIER 2 (COMPLEX) CRITERIA (Systemic, interactive, or multi-component changes):\n"
        "- ANY global theme redesign, light/dark mode overhaul, palette refactoring, or site-wide contrast/readability adjustments.\n"
        "- ANY behavioral or interactive functionality (opening/closing popups, modals, windows, drawers, dialogs, dropdowns, tabs).\n"
        "- Connecting buttons or UI elements to actions, event handlers, click listeners, or JavaScript state.\n"
        "- Multi-component additions (e.g. adding functional settings panels, deposit flows, assistant chat windows).\n"
        "- Changes that span or require coordination across HTML, CSS, and JavaScript.\n"
        "- Data state management, dynamic rendering, chart generation, SVG coordinate math, or animation logic.\n\n"
        "DECISION RULE:\n"
        "If the user asks to fix or change the light/dark theme, overhaul contrast or readability across the page, "
        "make buttons functional, open windows/popups/modals, wire interactions, or modify multiple components, "
        "or if there is any doubt about complexity, you MUST classify as 'complex'.\n\n"
        "Output strictly valid JSON:\n"
        "{\n"
        '  "tier": "lite" | "complex",\n'
        '  "target_files": ["index.html", "styles.css", "app.js"],\n'
        '  "primary_reason": "Clear explanation of complexity decision",\n'
        '  "requires_interaction": true | false\n'
        "}"
    )

    prompt = (
        f"User Modification Prompt:\n{user_prompt}\n\n"
        f"Available Baseline Files: {list(baseline_files.keys())}\n\n"
        f"Classify complexity:"
    )

    raw = call_gemini_model(
        model=lite_model,
        contents=[prompt],
        system_instruction=system_instruction,
        temperature=0.1,
        response_mime_type="application/json"
    )

    parsed = None
    if raw:
        # 1. Direct JSON parse
        try:
            parsed = json.loads(raw.strip())
        except Exception:
            pass

        # 2. Markdown fence extraction
        if not parsed:
            m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", raw, re.IGNORECASE)
            if m:
                try:
                    parsed = json.loads(m.group(1).strip())
                except Exception:
                    pass

        # 3. First '{' to last '}' extraction
        if not parsed:
            first_brace = raw.find("{")
            last_brace = raw.rfind("}")
            if first_brace != -1 and last_brace > first_brace:
                try:
                    parsed = json.loads(raw[first_brace:last_brace + 1].strip())
                except Exception:
                    pass

    if parsed and isinstance(parsed, dict) and parsed.get("tier") in ["lite", "complex"]:
        result = parsed
    else:
        # Safe default: Any modification where parsing fails or is ambiguous must route to COMPLEX (Tier 2)
        # to prevent breaking files or dropping functionality with a truncated patch.
        result = {
            "tier": "complex",
            "target_files": ["index.html", "styles.css", "app.js"],
            "primary_reason": "Safely defaulting to complex tier for comprehensive architectural handling"
        }

    if on_event:
        on_event(f"✓ Routed to: {result.get('tier', 'complex').upper()} TIER ({result.get('primary_reason', 'Analysis complete')})")

    return result


@observability.traceable(
    name="Lite Tier Upgrade Agent",
    run_type="chain",
    tags=["agent", "lite-upgrade"]
)
def execute_lite_tier_upgrade(
    project_id: str,
    baseline_files: dict,
    user_prompt: str,
    lite_model: str,
    classification: dict,
    temperature: float = 0.2,
    thinking_budget: int = 0,
    on_event: callable = None
) -> dict | None:
    """
    Tier 1 (Flash Lite with Contract Pipelining):
    Executes localized changes using Flash Lite.
    Pipes extracted HTML IDs into CSS/JS workers so they share a locked contract.
    If search/replace validation fails, returns None to signal immediate escalation.
    """
    if on_event:
        on_event(f"⚡ [{lite_model} Lite Engine]: Executing localized Antigravity surgical patch...")

    target_files = classification.get("target_files", ["styles.css", "index.html"])
    staged_files = {}
    for fn, finfo in baseline_files.items():
        if not finfo.get("is_binary") and finfo.get("content"):
            staged_files[fn] = finfo["content"]

    locked_contract = {}
    applied_changes = []

    # 1. HTML Phase (if needed)
    if "index.html" in target_files and "index.html" in staged_files:
        html_prompt = (
            f"User Request: {user_prompt}\n\n"
            f"Baseline HTML File:\n```html\n{staged_files['index.html']}\n```\n\n"
            f"Find the exact existing lines in the baseline HTML that need to be changed to satisfy the user request.\n"
            f"Output exact <<<<<<< SEARCH ... ======= ... >>>>>>> diff for index.html:"
        )
        html_res = call_gemini_model(
            model=lite_model,
            contents=[html_prompt],
            system_instruction=(
                "You are an Antigravity Surgical HTML Engineer running on Flash Lite.\n"
                "Inspect the baseline HTML carefully, find the exact existing lines that need to be updated to satisfy the user request, "
                "and output ONLY a search/replace diff block without rewriting unrelated code:\n"
                "<<<<<<< SEARCH\n[exact original lines from baseline]\n=======\n[updated replacement lines]\n>>>>>>>"
            ),
            temperature=0.2
        )
        patched_html, applied = project_store.apply_search_replace(staged_files["index.html"], html_res)
        if applied:
            staged_files["index.html"] = patched_html
            applied_changes.append("index.html (targeted diff)")
            # Extract IDs and classes into locked contract
            new_ids = re.findall(r'id=["\']([^"\']+)["\']', html_res)
            new_classes = re.findall(r'class=["\']([^"\']+)["\']', html_res)
            locked_contract["ids"] = new_ids
            locked_contract["classes"] = new_classes
        elif "index.html" in target_files and len(target_files) == 1:
            # If standalone HTML search block failed to match, signal escalation
            return None

    # 2. CSS Phase (if needed)
    if "styles.css" in target_files and "styles.css" in staged_files:
        contract_hint = f"Locked HTML Contract: IDs={locked_contract.get('ids', [])}, Classes={locked_contract.get('classes', [])}" if locked_contract else ""
        css_prompt = (
            f"User Request: {user_prompt}\n\n"
            f"{contract_hint}\n\n"
            f"Baseline CSS File:\n```css\n{staged_files['styles.css']}\n```\n\n"
            f"Find the exact existing rules in the baseline CSS that need to be changed to satisfy the user request.\n"
            f"Output exact <<<<<<< SEARCH ... ======= ... >>>>>>> diff for styles.css:"
        )
        css_res = call_gemini_model(
            model=lite_model,
            contents=[css_prompt],
            system_instruction=(
                "You are an Antigravity Surgical CSS Engineer running on Flash Lite.\n"
                "Inspect the baseline CSS carefully, find the exact existing rules that need to be updated to satisfy the user request, "
                "and output ONLY a search/replace block:\n"
                "<<<<<<< SEARCH\n[exact original code]\n=======\n[updated code]\n>>>>>>>"
            ),
            temperature=0.2
        )
        patched_css, applied = project_store.apply_search_replace(staged_files["styles.css"], css_res)
        if applied:
            staged_files["styles.css"] = patched_css
            applied_changes.append("styles.css (targeted diff)")
        else:
            # Fallback to smart rule merge if not a strict search/replace
            rule_clean = extract_worker_code_snippet(css_res, "styles.css")
            if "{" in rule_clean and "}" in rule_clean:
                staged_files["styles.css"] = project_store.merge_css(staged_files["styles.css"], rule_clean)
                applied_changes.append("styles.css (rule update)")

    # 3. JS Phase (if needed)
    if "app.js" in target_files:
        if "app.js" not in staged_files:
            # Requires new JS logic that does not exist in baseline; escalate to complex tier
            return None
        contract_hint = f"Locked HTML Contract: IDs={locked_contract.get('ids', [])}" if locked_contract else ""
        js_prompt = (
            f"User Request: {user_prompt}\n\n"
            f"{contract_hint}\n\n"
            f"Baseline JS File:\n```javascript\n{staged_files['app.js']}\n```\n\n"
            f"Find the exact existing lines in the baseline JS that need to be changed to satisfy the user request.\n"
            f"Output exact <<<<<<< SEARCH ... ======= ... >>>>>>> diff for app.js:"
        )
        js_res = call_gemini_model(
            model=lite_model,
            contents=[js_prompt],
            system_instruction=(
                "You are an Antigravity Surgical JS Engineer running on Flash Lite.\n"
                "Inspect the baseline JS carefully, find the exact existing functions or event listeners that need to be updated, "
                "and output ONLY a search/replace block:\n"
                "<<<<<<< SEARCH\n[exact original code]\n=======\n[updated code]\n>>>>>>>"
            ),
            temperature=0.2
        )
        patched_js, applied = project_store.apply_search_replace(staged_files["app.js"], js_res)
        if applied:
            staged_files["app.js"] = patched_js
            applied_changes.append("app.js (targeted diff)")

    if not applied_changes:
        # None of the lite patches matched cleanly; signal escalation
        return None

    # Save to project staged preview
    saved_files = project_store.apply_surgical_modification(project_id, staged_files, user_prompt)

    assembled_report = (
        f"### ✓ Antigravity Lite Upgrade Complete ({lite_model})\n\n"
        f"**Project**: `{project_id}`\n\n"
        f"**Modified Files**:\n"
        + "\n".join(f"- `{f['name']}` ({f['size']} bytes)" for f in saved_files) + "\n\n"
        f"**Routing**: Resolved in Tier 1 (Flash Lite) for optimal resource efficiency."
    )

    if on_event:
        on_event(f"✓ Lite upgrade complete! {len(saved_files)} file(s) staged in project {project_id}.")

    return {
        "project_id": project_id,
        "saved_files": saved_files,
        "assembled_text": assembled_report
    }


@observability.traceable(
    name="Complex Tier Upgrade Agent",
    run_type="chain",
    tags=["agent", "complex-upgrade"]
)
def execute_complex_tier_upgrade(
    project_id: str,
    baseline_files: dict,
    user_prompt: str,
    complex_model: str = DEFAULT_COMPLEX_MODEL,
    temperature: float = 0.3,
    thinking_budget: int = 1024,
    attachments: list[dict] | None = None,
    on_event: callable = None
) -> dict:
    """
    Tier 2 (Gemini Complex - Unified Transactional Engine):
    Executes multi-file, cross-component, stateful, or SVG coordinate upgrades
    in a single cohesive transaction using exact SEARCH/REPLACE blocks.
    Auto-falls back: 3.8 Flash -> 3.6 Flash -> 2.5 Flash if needed.
    """
    if on_event:
        on_event(f"🛠️ [{complex_model} Unified Engine]: Executing transactional multi-file upgrade...")

    # Save any new uploaded attachments to project assets
    saved_assets = save_project_attachments(project_id, attachments) if attachments else []
    brand_info = analyze_brand_and_vision_context(user_prompt, attachments, on_event=on_event) if attachments else {}

    files_dump = []
    for fn, finfo in baseline_files.items():
        if not finfo.get("is_binary") and finfo.get("content"):
            files_dump.append(f"=== File: {fn} ===\n{finfo['content']}")
    full_context = "\n\n".join(files_dump)

    brand_guidelines_note = ""
    if brand_info:
        c_name = brand_info.get("company_name", "")
        t_line = brand_info.get("tagline", "")
        c_pal = brand_info.get("color_palette_summary", "")
        brand_guidelines_note += f"\nVISUAL BRAND GUIDELINES:\n- Company Name: '{c_name}'\n- Tagline: '{t_line}'\n- Palette: {c_pal}\n"
    if saved_assets:
        brand_guidelines_note += "\nAVAILABLE ASSETS:\n" + "\n".join(f"- `<img src=\"{a['rel_path']}\">` ({a['name']})" for a in saved_assets) + "\n"

    system_instruction = (
        f"You are the Principal Lead Full-Stack Frontend Engineer ({complex_model}) in Antigravity Surgical Mode.\n"
        "Your mission: Execute the user's upgrade request as a single cohesive transaction across all necessary files.\n\n"
        "CRITICAL ANTIGRAVITY SURGICAL RULES:\n"
        "1. Do NOT rewrite full files from scratch. Output exact <<<<<<< SEARCH ... ======= ... >>>>>>> diff blocks for each file that needs changes.\n"
        "2. REQUIRED OUTPUT FORMAT:\n"
        "   ```{lang} filename=\"{filename}\"\n"
        "   <<<<<<< SEARCH\n"
        "   [exact original lines from baseline]\n"
        "   =======\n"
        "   [updated replacement lines]\n"
        "   >>>>>>>\n"
        "   ```\n"
        "3. MODAL BEST PRACTICES: If adding a modal dialog (e.g. signup/login/profile):\n"
        "   - Add the trigger button into the appropriate container (e.g. <nav class=\"nav-actions\">).\n"
        "   - Add the modal markup (<div id=\"authModal\" class=\"modal\">...</div>) before </body>.\n"
        "   - REUSE existing modal design system tokens (.modal, .modal-dialog, .modal-backdrop, .modal-header, .modal-close-icon).\n"
        "   - Bind click listeners in app.js for open, close, and demo submission.\n"
        "4. SVG BEST PRACTICES: Preserve all coordinate transforms, rotation angles (e.g. transform: rotate(90deg) and transform-origin on text inside rotated SVGs), and viewBox properties.\n"
        "5. DYNAMIC UI BEST PRACTICES: If fixing dynamic states (e.g. connected wallet text 0x71...89B), ensure proper overflow-hidden, text-ellipsis, and monospace pill badge styling so buttons don't break navbar alignment."
    )

    prompt = (
        f"Project ID: {project_id}\n\n"
        f"Baseline Codebase:\n{full_context}\n\n"
        f"User Upgrade Request:\n{user_prompt}\n"
        f"{brand_guidelines_note}\n"
        f"Generate the exact, cohesive SEARCH/REPLACE diff blocks for all modified files:"
    )

    raw_response = call_gemini_model(
        model=complex_model,
        contents=[prompt],
        system_instruction=system_instruction,
        temperature=temperature,
        thinking_budget=thinking_budget,
        on_event=on_event
    )

    # Initialize staged files with baseline
    staged_files = {}
    for fn, finfo in baseline_files.items():
        if not finfo.get("is_binary") and finfo.get("content"):
            staged_files[fn] = finfo["content"]

    # Parse multi-file diff blocks
    fence_pattern = re.compile(
        r"```(?P<lang>[a-zA-Z0-9_\-+]+)?(?:\s+(?:filename|file|path)=[\"'](?P<fn>[^\"']+)[\"'])?\s*\n(?P<code>[\s\S]*?)(?:```|$)",
        re.IGNORECASE
    )

    applied_count = 0
    for m in fence_pattern.finditer(raw_response):
        target_fn = m.group("fn")
        diff_code = m.group("code")
        if not target_fn:
            # Detect filename from language
            lang = (m.group("lang") or "").lower()
            if "html" in lang:
                target_fn = "index.html"
            elif "css" in lang:
                target_fn = "styles.css"
            elif "js" in lang or "javascript" in lang:
                target_fn = "app.js"

        if target_fn and target_fn in staged_files:
            patched, applied = project_store.apply_search_replace(staged_files[target_fn], diff_code)
            if applied:
                staged_files[target_fn] = patched
                applied_count += 1
            else:
                # Fallback to component/rule merge if search block was slightly non-contiguous
                clean_snippet = extract_worker_code_snippet(diff_code, target_fn)
                if target_fn.endswith(".html"):
                    staged_files[target_fn] = project_store.replace_or_append_html(staged_files[target_fn], clean_snippet)
                elif target_fn.endswith(".css"):
                    staged_files[target_fn] = project_store.merge_css(staged_files[target_fn], clean_snippet)
                elif target_fn.endswith(".js"):
                    staged_files[target_fn] = project_store.merge_js(staged_files[target_fn], clean_snippet)
                applied_count += 1

    # Connect any standalone SVG assets generated (ONLY if explicitly marked in code fences, never scrape inline HTML SVGs)
    standalone_svg_blocks = re.findall(
        r"```(?:svg|xml)(?:\s+(?:filename|file)=[\"']([^\"']+)[\"'])?\s*\n\s*(<svg[\s\S]*?</svg>)\s*```",
        raw_response,
        re.IGNORECASE
    )
    if standalone_svg_blocks:
        p_dir = project_store.get_project_dir(project_id)
        assets_dir = p_dir / "assets" / "icons"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for i, (fn_attr, svg_code) in enumerate(standalone_svg_blocks, 1):
            if fn_attr:
                target_svg = p_dir / fn_attr.strip()
                target_svg.parent.mkdir(parents=True, exist_ok=True)
                target_svg.write_text(svg_code.strip(), encoding="utf-8")
                staged_files[fn_attr.strip()] = svg_code.strip()
            else:
                id_match = re.search(r'id=["\']([^"\']+)["\']', svg_code)
                icon_name = f"icon_{id_match.group(1)}.svg" if id_match else f"icon_{i}.svg"
                icon_path = assets_dir / icon_name
                icon_path.write_text(svg_code.strip(), encoding="utf-8")
                staged_files[f"assets/icons/{icon_name}"] = svg_code.strip()

    # Apply surgical modification to disk (creates staged preview)
    saved_files = project_store.apply_surgical_modification(project_id, staged_files, user_prompt)

    assembled_report = (
        f"### ✓ Antigravity Transactional Upgrade Complete ({complex_model})\n\n"
        f"**Project**: `{project_id}`\n\n"
        f"**Modified Files**:\n"
        + "\n".join(f"- `{f['name']}` ({f['size']} bytes)" for f in saved_files) + "\n\n"
        f"**Routing**: Handled by Tier 2 ({complex_model}) for cross-file cohesion & state alignment."
    )

    if on_event:
        on_event(f"✓ Transactional upgrade complete! {len(saved_files)} file(s) staged in project {project_id}.")

    return {
        "project_id": project_id,
        "saved_files": saved_files,
        "assembled_text": assembled_report
    }


@observability.traceable(
    name="Component Worker Agent",
    run_type="chain",
    tags=["agent", "worker", "component-worker"]
)
def execute_component_worker_subtask(st: dict, lite_model: str, on_event: callable = None) -> dict:
    """Executes an isolated subtask component generation worker."""
    raw = call_gemini_model(
        model=lite_model,
        contents=[f"Objective: {st['objective']}\nGuidelines: {st['instructions']}"],
        system_instruction=f"Generate component code for {st['target_file']} wrapped in ```{st['target_file'].split('.')[-1]} filename=\"{st['target_file']}\"",
        temperature=0.4,
        on_event=on_event
    )
    return {
        "target_file": st["target_file"],
        "subtask_id": st["id"],
        "clean_snippet": extract_worker_code_snippet(raw, st["target_file"]),
        "raw_output": raw
    }


@observability.traceable(
    name="Master Assembler Agent",
    run_type="chain",
    tags=["agent", "assembler", "master-assembler"]
)
def execute_master_assembler(
    project_id: str,
    prompt: str,
    snippets_dump: str,
    system_instruction: str,
    complex_model: str,
    temperature: float,
    thinking_budget: int,
    on_event: callable = None
) -> str:
    """Harmonizes component snippets into complete production-ready files."""
    return call_gemini_model(
        model=complex_model,
        contents=[f"Project {project_id}\nPrompt: {prompt}\n\nSnippets:\n{snippets_dump}"],
        system_instruction=system_instruction,
        temperature=temperature,
        thinking_budget=thinking_budget,
        on_event=on_event
    )


@observability.traceable(
    name="Initial Project Synthesis Pipeline",
    run_type="chain",
    tags=["agent", "pipeline", "synthesis"]
)
def synthesize_initial_project(
    project_id: str,
    prompt: str,
    complex_model: str = DEFAULT_COMPLEX_MODEL,
    lite_model: str = DEFAULT_LITE_MODEL,
    temperature: float = 0.3,
    thinking_budget: int = 1024,
    attachments: list[dict] | None = None,
    on_event: callable = None
) -> dict:
    """
    Initial Project Creation (Full Multi-Agent Synthesis):
    1. Vision & Asset Engine: Persist uploaded assets to assets/ and extract Brand Guidelines.
    2. Complex Architect: Adaptive subtask synthesis honoring user prompt and brand DNA.
    3. Lite Workers: Targeted component generation.
    4. Complex Master Assembler: Master assembly with asset path resolution.
    """
    if is_stop_requested():
        raise InterruptedError("Execution stopped by user.")

    # 1. Save uploaded attachments to project assets directory
    saved_assets = save_project_attachments(project_id, attachments) if attachments else []

    # 2. Extract Brand DNA and visual palette via Gemini Multimodal Vision
    brand_info = analyze_brand_and_vision_context(prompt, attachments, on_event=on_event) if attachments else {}
    company_name = brand_info.get("company_name", "")
    tagline = brand_info.get("tagline", "")
    primary_color = brand_info.get("primary_color", "#1e3a8a")
    secondary_color = brand_info.get("secondary_color", "#ea580c")
    accent_color = brand_info.get("accent_color", "#f59e0b")
    palette_desc = brand_info.get("color_palette_summary", "Professional, high-trust commercial color palette")
    design_dir = brand_info.get("design_direction", "Clean, realistic, professional commercial layout suited for the requested business with real human involvement")

    logo_path = None
    for a in saved_assets:
        if a.get("is_logo") or a.get("is_image"):
            logo_path = a.get("logo_path") or a.get("rel_path")
            break

    brand_label = f" for '{company_name}'" if company_name else ""
    if on_event:
        on_event(f"🎨 [{complex_model} Architect]: Creating architectural blueprint & component subtasks{brand_label}...")

    # Build dynamic domain-adapted subtasks based on user prompt and brand guidelines
    hero_instructions = (
        (f"Brand/Company Name: {company_name}\n" if company_name else "") +
        (f"Tagline: {tagline}\n" if tagline else "") +
        (f"Logo Image Asset: Use <img src=\"{logo_path}\" alt=\"{company_name or 'Logo'}\" class=\"h-12 w-auto\"> in the header and footer.\n" if logo_path else "") +
        f"User Requirements: {prompt}\n"
        "Include a modern sticky navbar with brand logo/name, 24*7 emergency dispatch badge/call button, headline, and primary conversion CTA."
    )

    features_instructions = (
        f"Fulfill the core business workflows specified in: {prompt}\n"
        "Create rich, interactive feature cards and widgets (e.g. selective porter chooser based on cargo requirements/capacity, transparent rate estimates, Pan-India route tracking).\n"
        "Realistic presentation conveying trust, reliability, and human involvement."
    )

    css_instructions = (
        f"Brand Palette: Primary {primary_color}, Secondary {secondary_color}, Accent {accent_color} ({palette_desc}).\n"
        f"Visual Aesthetic: {design_dir}. Realistic, trustworthy commercial layout (do NOT use dark obsidian crypto themes unless explicitly asked).\n"
        "Crisp typography, clean readable cards, responsive container layout, polished micro-interactions."
    )

    js_instructions = (
        f"Vanilla JavaScript interactions for: {prompt}\n"
        "Include interactive porter selection logic (filtering/selecting porters based on requirements), booking calculation modals, smooth scroll, and mobile drawer toggle."
    )

    subtasks = [
        {"id": "task_hero", "role": "html_worker", "target_file": "index.html", "objective": f"Hero section and brand navigation for: {prompt}", "template_format": "COMPONENT_SNIPPET", "instructions": hero_instructions},
        {"id": "task_features", "role": "html_worker", "target_file": "index.html", "objective": f"Core business features and interactive widgets for: {prompt}", "template_format": "COMPONENT_SNIPPET", "instructions": features_instructions},
        {"id": "task_css", "role": "css_worker", "target_file": "styles.css", "objective": f"Design tokens and styling matching brand palette ({palette_desc})", "template_format": "CSS_MODULE", "instructions": css_instructions},
        {"id": "task_js", "role": "js_worker", "target_file": "app.js", "objective": f"Interactive UI controls and porter selection logic for: {prompt}", "template_format": "JS_FUNCTION", "instructions": js_instructions}
    ]

    from concurrent.futures import ThreadPoolExecutor, as_completed

    if on_event:
        on_event(f"⚡ [Parallel Fan-Out]: Concurrently synthesizing {len(subtasks)} components with {lite_model}...")

    worker_results_map = {}

    def _run_worker(task):
        if is_stop_requested():
            raise InterruptedError("Execution stopped by user.")
        if on_event:
            on_event(f"⚡ [{lite_model} Worker]: Synthesizing {task['id']} ({task['target_file']})...")
        res = execute_component_worker_subtask(task, lite_model, on_event=on_event)
        if on_event:
            on_event(f"✓ [{lite_model} Worker]: Finished {task['id']} ({task['target_file']})")
        return res

    with ThreadPoolExecutor(max_workers=min(4, len(subtasks))) as executor:
        future_to_task = {executor.submit(_run_worker, st): st for st in subtasks}
        for future in as_completed(future_to_task):
            if is_stop_requested():
                executor.shutdown(wait=False, cancel_futures=True)
                raise InterruptedError("Execution stopped by user.")
            st = future_to_task[future]
            try:
                worker_results_map[st["id"]] = future.result()
            except Exception as ex:
                if on_event:
                    on_event(f"⚠️ [{lite_model} Worker]: Subtask {st['id']} notice: {ex}")
                worker_results_map[st["id"]] = {
                    "target_file": st["target_file"],
                    "subtask_id": st["id"],
                    "clean_snippet": "",
                    "raw_output": ""
                }

    # Reconstruct worker results in deterministic order matching subtasks
    worker_results = [worker_results_map[st["id"]] for st in subtasks if st["id"] in worker_results_map]

    # Master Assembly
    if is_stop_requested():
        raise InterruptedError("Execution stopped by user.")
    if on_event:
        on_event(f"🛠️ [{complex_model} Assembler]: Harmonizing into complete index.html, styles.css, and app.js...")

    snippets_dump = "\n\n".join(f"--- {wr['target_file']} ---\n{wr['clean_snippet']}" for wr in worker_results)

    brand_context_note = ""
    if company_name:
        brand_context_note += f"\nCOMPANY NAME: '{company_name}'\nTAGLINE: '{tagline}'\n"
    if logo_path:
        brand_context_note += f"LOGO ASSET PATH: Use `<img src=\"{logo_path}\" alt=\"{company_name or 'Logo'}\" class=\"h-12 w-auto\">` in the navbar and footer. Do NOT replace with generic text or placeholder icons.\n"

    system_instruction = (
        f"You are the Principal Lead Frontend Assembler ({complex_model}).\n"
        "Take the blueprints and assemble the complete, cohesive, production-ready files.\n"
        f"{brand_context_note}\n"
        "Output each file with filename: ```html filename=\"index.html\", ```css filename=\"styles.css\", ```javascript filename=\"app.js\"."
    )
    # Strategic thinking budget: allow up to 1024 reasoning tokens for cohesive cross-component alignment,
    # or respect user's lower/0 budget for maximum speed
    assembler_budget = min(int(thinking_budget), 1024) if thinking_budget and int(thinking_budget) > 0 else 0

    assembled = execute_master_assembler(
        project_id=project_id,
        prompt=prompt,
        snippets_dump=snippets_dump,
        system_instruction=system_instruction,
        complex_model=complex_model,
        temperature=temperature,
        thinking_budget=assembler_budget,
        on_event=on_event
    )

    parsed_files = project_store.parse_multi_file_response(assembled)
    html, css = extract_html_and_css(assembled)
    if html and "index.html" not in parsed_files:
        parsed_files["index.html"] = html
    if css and "styles.css" not in parsed_files:
        parsed_files["styles.css"] = css

    saved_files = project_store.save_files_to_project(project_id, parsed_files)

    # Update project_meta title with identified brand name if available
    if company_name:
        try:
            meta = project_store.load_project_meta(project_id) or {}
            meta["title"] = f"{company_name} - {tagline}" if tagline else company_name
            meta_path = project_store.get_project_dir(project_id) / "project_meta.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception:
            pass

    if on_event:
        on_event(f"✓ Initial project synthesis complete! {len(saved_files)} file(s) staged in project {project_id}.")

    return {
        "project_id": project_id,
        "saved_files": saved_files,
        "assembled_text": assembled
    }


@observability.traceable(
    name="Studio Agent Orchestrator",
    run_type="chain",
    tags=["orchestrator", "multi-agent"],
    metadata=observability.get_agent_metadata()
)
def orchestrate_generation(
    prompt: str,
    project_id: str | None = None,
    is_upgrade: bool = False,
    complex_model: str = DEFAULT_COMPLEX_MODEL,
    lite_model: str = DEFAULT_LITE_MODEL,
    temperature: float = 1.0,
    thinking_budget: int = 2048,
    attachments: list[dict] | None = None,
    on_event: callable = None,
    **kwargs
) -> dict:
    """
    End-to-End Intelligent Router Orchestration:
    1. Distinguishes normal chat from code upgradation/creation.
    2. Normal Chat: Uses Flash Lite models conversationally with live temperature & thinking budget.
    3. Upgradation Flow: Triggered ONLY when the user is explicitly saying to update/modify code.
    4. Initial Creation: Triggered when user asks to build or generate a new project.
    """
    if is_stop_requested():
        raise InterruptedError("Execution stopped by user.")

    has_files = bool(project_id and project_store.has_baseline_backup(project_id))

    # Step 1: Intelligent Intent Classification
    intent_data = classify_conversation_intent(
        user_prompt=prompt,
        project_id=project_id,
        has_files=has_files,
        lite_model=lite_model,
        on_event=on_event
    )
    intent = intent_data.get("intent", "chat" if (not has_files and "?" in prompt) else ("upgrade" if has_files else "create"))

    # Step 2: Route Normal Chat (Conversation Only - No File Modifications)
    if intent == "chat":
        return execute_normal_chat(
            project_id=project_id,
            user_prompt=prompt,
            lite_model=lite_model,
            temperature=temperature,
            thinking_budget=thinking_budget,
            on_event=on_event
        )

    # Step 3: Upgradation Flow (Only when user asks to update something)
    if intent == "upgrade" and project_id:
        baseline_files = project_store.get_baseline_files(project_id)
        classification = classify_upgrade_complexity(prompt, baseline_files, lite_model, on_event=on_event)
        tier = classification.get("tier", "complex")

        if tier == "lite":
            lite_result = execute_lite_tier_upgrade(
                project_id=project_id,
                baseline_files=baseline_files,
                user_prompt=prompt,
                lite_model=lite_model,
                classification=classification,
                temperature=temperature,
                thinking_budget=thinking_budget,
                on_event=on_event
            )
            if lite_result is not None:
                return lite_result

            if on_event:
                on_event(f"⚠️ [Dynamic Router]: Escalating to Tier 2 ({complex_model}) for cross-file state alignment...")

        return execute_complex_tier_upgrade(
            project_id=project_id,
            baseline_files=baseline_files,
            user_prompt=prompt,
            complex_model=complex_model,
            temperature=temperature,
            thinking_budget=thinking_budget,
            attachments=attachments,
            on_event=on_event
        )

    # Step 4: Initial Project Creation Flow
    if not project_id:
        meta = project_store.create_new_project(prompt=prompt)
        project_id = meta["id"]

    return synthesize_initial_project(
        project_id=project_id,
        prompt=prompt,
        complex_model=complex_model,
        lite_model=lite_model,
        temperature=temperature,
        thinking_budget=thinking_budget,
        attachments=attachments,
        on_event=on_event
    )


def main():
    active_lite_model = DEFAULT_LITE_MODEL
    current_project_id = None
    modifier_mode = False

    print("=" * 68)
    print(" Pure Gemini Multi-Agent Orchestration Generator")
    print(f" Master Architect & Assembler : {MODEL_COMPLEX}")
    print(f" Active Lite Worker Model     : {active_lite_model}")
    print(f" Projects Folder              : {project_store.PROJECTS_DIR}")
    print(" Commands:")
    print("   'exit' or 'quit'    : Exit session")
    print("   '/new'              : Start fresh new project (e.g. PR-1, PR-2)")
    print("   '/mod' or '/modify' : Toggle Upgrade Mode on top of .backup/ baseline")
    print("   '/model <3.1|3.5>'  : Select Lite Model (gemini-3.1-flash-lite or 3.5)")
    print("   '/like'             : 👍 Accept staged version (promotes to .backup/)")
    print("   '/dislike'          : 👎 Revert staged version (restores from .backup/)")
    print("   '/status'           : Display active project & baseline status")
    print("=" * 68)

    def log_event(msg: str):
        print(f"  {msg}")

    while True:
        try:
            status_tag = f"[{current_project_id or 'New'} | UPGRADE]" if modifier_mode else f"[{current_project_id or 'New'}]"
            prompt = input(f"\n{status_tag} ({active_lite_model}) > ").strip()
            if not prompt:
                continue

            if prompt.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break

            if prompt.lower() in ["/new", "/fresh", "clear"]:
                current_project_id = None
                modifier_mode = False
                print("[✓ Starting fresh new project on next prompt]")
                continue

            if prompt.lower().startswith("/model"):
                parts = prompt.split()
                if len(parts) > 1 and parts[1].strip() in SUPPORTED_LITE_MODELS:
                    active_lite_model = SUPPORTED_LITE_MODELS[parts[1].strip()]
                    print(f"[✓ Lite Worker Model switched to: {active_lite_model}]")
                else:
                    print(f"[!] Options: /model 3.1 or /model 3.5. Current: {active_lite_model}")
                continue

            if prompt.lower().startswith("/mod"):
                modifier_mode = not modifier_mode
                status = "ACTIVATED (Upgrades will build on .backup/ baseline)" if modifier_mode else "DEACTIVATED"
                print(f"[✓ Upgrade Mode: {status}]")
                continue

            if prompt.lower() == "/like":
                if current_project_id:
                    res = project_store.promote_staged_to_baseline(current_project_id)
                    print(f"[👍 Accepted! Staged files promoted to .backup/ baseline for {current_project_id}]")
                else:
                    print("[!] No active project selected.")
                continue

            if prompt.lower() == "/dislike":
                if current_project_id:
                    res = project_store.revert_staged_from_baseline(current_project_id)
                    print(f"[👎 Reverted! Restored {current_project_id} back to pristine .backup/ baseline]")
                else:
                    print("[!] No active project selected.")
                continue

            if prompt.lower() == "/status":
                if current_project_id:
                    meta = project_store.load_project_meta(current_project_id) or {}
                    has_b = project_store.has_baseline_backup(current_project_id)
                    print(f"Project: {current_project_id} | Title: {meta.get('title')} | Review Status: {meta.get('review_status')} | Baseline Exists: {has_b}")
                else:
                    print("No active project currently loaded.")
                continue

            # Run Multi-Agent Orchestration Pipeline
            print(f"\n🚀 Launching Multi-Agent Orchestration for: {prompt[:60]}...")
            result = orchestrate_generation(
                prompt=prompt,
                project_id=current_project_id,
                is_upgrade=modifier_mode,
                lite_model=active_lite_model,
                on_event=log_event
            )

            current_project_id = result["project_id"]
            modifier_mode = True  # Subsequent prompts in this project will default to upgrading

            print(f"\n[✓ Staged Artifacts in projects/{current_project_id}]:")
            for f in result["saved_files"]:
                print(f"   -> {f['name']} ({f['size']:,} bytes)")
            print(f"   [💡 Type '/like' to accept this design, or '/dislike' to revert to baseline]")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break
        except Exception as e:
            print(f"\n[!] Error: {e}")


if __name__ == "__main__":
    main()

