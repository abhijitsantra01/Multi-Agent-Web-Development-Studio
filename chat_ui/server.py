import os
import re
import sys
import json
import base64
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Workspace paths
ROOT_DIR = Path(__file__).parent.parent.resolve()
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Import helper functions from orchestrator.py if available, or define robust local implementations
def get_incremented_path(folder: Path, base_name: str, ext: str) -> Path:
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
    html = None
    css = None

    # 1. HTML code block
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

    # 2. CSS code block
    css_match = re.search(r"```css[^\n]*\n(.*?)(?:```|$)", text, re.DOTALL | re.IGNORECASE)
    if css_match:
        css = css_match.group(1).strip()

    # 3. Extract <style> from HTML if no separate CSS
    if not css and html:
        style_matches = re.findall(r"<style[^>]*>(.*?)</style>", html, re.DOTALL | re.IGNORECASE)
        if style_matches:
            css = "\n\n".join(s.strip() for s in style_matches if s.strip())

    return html, css


def save_response_artifacts(text: str, output_dir: Path) -> list[dict]:
    """Detects and saves any returned output (HTML, CSS, SVG, base64 images, scripts)."""
    saved = []

    # 1. Base64 Data URI Images
    b64_matches = re.findall(r"data:image/([a-zA-Z0-9_\-+]+);base64,([A-Za-z0-9+/=\s]+)", text)
    for img_format, b64_str in b64_matches:
        try:
            raw_bytes = base64.b64decode(b64_str.strip())
            ext = f".{img_format.lower()}"
            if ext == ".jpeg":
                ext = ".jpg"
            target = get_incremented_path(output_dir, "image", ext)
            target.write_bytes(raw_bytes)
            saved.append({"name": target.name, "path": str(target), "size": len(raw_bytes), "type": "image"})
        except Exception:
            pass

    # 2. Standalone SVG
    svg_matches = re.findall(r"```(?:svg|xml)?[^\n]*\n\s*(<svg[\s\S]*?</svg>)\s*```", text, re.IGNORECASE)
    if not svg_matches and not ("<!DOCTYPE html>" in text or "<html" in text):
        svg_matches = re.findall(r"(<svg[\s\S]*?</svg>)", text, re.IGNORECASE)

    for svg_content in svg_matches:
        target = get_incremented_path(output_dir, "image", ".svg")
        target.write_text(svg_content.strip(), encoding="utf-8")
        saved.append({"name": target.name, "path": str(target), "size": target.stat().st_size, "type": "svg"})

    # 3. HTML and CSS
    html, css = extract_html_and_css(text)
    if html:
        main_index = output_dir / "index.html"
        main_index.write_text(html, encoding="utf-8")
        saved.append({"name": main_index.name, "path": str(main_index), "size": main_index.stat().st_size, "type": "html", "is_primary": True})

    if css:
        main_css = output_dir / "styles.css"
        main_css.write_text(css, encoding="utf-8")
        saved.append({"name": main_css.name, "path": str(main_css), "size": main_css.stat().st_size, "type": "css", "is_primary": True})

    # 4. Code formats (JS, JSON, Python)
    for lang, base, ext, ftype in [
        ("javascript", "script", ".js", "javascript"),
        ("js", "script", ".js", "javascript"),
        ("json", "data", ".json", "json"),
        ("python", "script", ".py", "python"),
    ]:
        code_match = re.search(rf"```{lang}[^\n]*\n(.*?)(?:```|$)", text, re.DOTALL | re.IGNORECASE)
        if code_match and not html:
            target = get_incremented_path(output_dir, base, ext)
            target.write_text(code_match.group(1).strip(), encoding="utf-8")
            saved.append({"name": target.name, "path": str(target), "size": target.stat().st_size, "type": ftype})

    return saved


app = FastAPI(title="Gemini Deep Thinking Studio UI")

def get_global_client():
    http_opts = types.HttpOptions(
        api_version="v1beta",
        timeout=90000,
        retry_options=types.HttpRetryOptions(attempts=1)
    )
    client = genai.Client(api_key=get_active_api_key(), http_options=http_opts)
    return observability.wrap_client(client, chat_name="Gemini Server")

# Session state
SESSION = {
    "chat": None,
    "thinking_budget": 1024,
    "temperature": 0.7,
    "model": os.getenv("GEMINI_COMPLEX_MODEL", "gemini-3.6-flash"),
    "complex_model": os.getenv("GEMINI_COMPLEX_MODEL", "gemini-3.6-flash"),
    "lite_model": os.getenv("GEMINI_LITE_MODEL", "gemini-3.1-flash-lite"),
    "chat_only": False,
    "chat_model": "gemini-3.1-flash-lite",
    "chat_temperature": 0.7,
    "chat_budget": 0,
    "messages": []
}

import orchestrator
import direct_chat
import project_store
import observability
from typing import Optional, List, Dict, Any


USER_CUSTOM_API_KEY: Optional[str] = None


def get_active_api_key() -> str:
    """Returns User API key if provided; otherwise falls back to fresh .env key on disk."""
    if USER_CUSTOM_API_KEY and USER_CUSTOM_API_KEY.strip():
        return USER_CUSTOM_API_KEY.strip()
    try:
        from dotenv import dotenv_values
        env_vals = dotenv_values(Path(__file__).parent.parent / ".env")
        if env_vals.get("GEMINI_API_KEY"):
            return env_vals["GEMINI_API_KEY"].strip()
    except Exception:
        pass
    return (os.getenv("GEMINI_API_KEY") or "").strip()


def get_key_source() -> str:
    if USER_CUSTOM_API_KEY and USER_CUSTOM_API_KEY.strip():
        return "user"
    return "env"


def get_masked_key(key: str | None) -> str:
    if not key or len(key.strip()) < 8:
        return ""
    k = key.strip()
    return f"{k[:7]}...{k[-4:]}"


class ApiKeySaveRequest(BaseModel):
    api_key: str


class Attachment(BaseModel):
    name: str
    mime_type: str = "image/png"
    data_b64: Optional[str] = None
    content: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    thinking_budget: Optional[int] = 2048
    temperature: Optional[float] = 1.0
    project_id: Optional[str] = None
    is_modifier: bool = False
    complex_model: Optional[str] = None
    lite_model: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    chat_only: bool = False
    chat_model: Optional[str] = None
    chat_temperature: Optional[float] = None
    chat_budget: Optional[int] = None


class ModelSelectRequest(BaseModel):
    complex_model: Optional[str] = None
    lite_model: Optional[str] = None


class ConfigUpdateRequest(BaseModel):
    thinking_budget: Optional[int] = 2048
    temperature: Optional[float] = 1.0
    complex_model: Optional[str] = None
    lite_model: Optional[str] = None
    chat_only: Optional[bool] = None
    chat_model: Optional[str] = None
    chat_temperature: Optional[float] = None
    chat_budget: Optional[int] = None


class ObservabilityConfigRequest(BaseModel):
    enabled: Optional[bool] = None
    api_key: Optional[str] = None
    project: Optional[str] = None
    endpoint: Optional[str] = None
    agent_id: Optional[str] = None
    agent_environment: Optional[str] = None


@app.get("/api/state")
async def get_state():
    """Returns current session config, active models, API key status, history count, and LangSmith status."""
    active_key = get_active_api_key()
    return {
        "model": SESSION.get("complex_model", SESSION.get("model", "gemini-3.8-flash")),
        "complex_model": SESSION.get("complex_model", "gemini-3.8-flash"),
        "lite_model": SESSION.get("lite_model", "gemini-3.5-flash-lite"),
        "chat_only": SESSION.get("chat_only", False),
        "chat_model": SESSION.get("chat_model", "gemini-3.5-flash-lite"),
        "chat_temperature": SESSION.get("chat_temperature", 0.7),
        "chat_budget": SESSION.get("chat_budget", 0),
        "has_key": bool(active_key),
        "key_source": get_key_source(),
        "is_custom": get_key_source() == "user",
        "masked_key": get_masked_key(active_key),
        "thinking_budget": SESSION.get("thinking_budget", 16384),
        "temperature": SESSION.get("temperature", 1.0),
        "output_dir": str(OUTPUT_DIR),
        "history_count": len(SESSION["messages"]),
        "observability": observability.get_langsmith_config()
    }


@app.get("/api/observability/status")
async def get_observability_status():
    """Returns LangSmith observability configuration and active connection status."""
    return observability.get_langsmith_config()


@app.post("/api/observability/config")
async def update_observability_config(req: ObservabilityConfigRequest):
    """Updates and persists LangSmith tracing state, API key, and project configuration."""
    cfg = observability.update_langsmith_config(
        api_key=req.api_key,
        project=req.project,
        enabled=req.enabled,
        endpoint=req.endpoint,
        agent_id=req.agent_id,
        agent_environment=req.agent_environment,
        persist_to_env=True
    )
    return {
        "status": "ok",
        "config": cfg,
        "message": "LangSmith observability configuration updated successfully."
    }


@app.get("/api/history")
async def get_chat_history():
    """Returns conversation messages for the current session."""
    return {"messages": SESSION.get("messages", [])}


@app.get("/api/key/status")
async def get_key_status():
    """Returns active Gemini API key status, source ('user' or 'env'), and masked key."""
    active_key = get_active_api_key()
    source = get_key_source()
    return {
        "has_key": bool(active_key),
        "source": source,
        "is_custom": source == "user",
        "masked_key": get_masked_key(active_key),
        "key_length": len(active_key)
    }


@app.post("/api/key/save")
async def save_key(req: ApiKeySaveRequest):
    """Sets custom User API key in memory with priority over .env. Preserves default .env key."""
    global USER_CUSTOM_API_KEY, GLOBAL_CLIENT
    cleaned = req.api_key.strip()
    if not cleaned or len(cleaned) < 10:
        raise HTTPException(status_code=400, detail="Invalid API key format. Please provide a valid Gemini key.")
    
    USER_CUSTOM_API_KEY = cleaned
    orchestrator.set_user_api_key(cleaned)
    raw_client = genai.Client(api_key=cleaned, http_options=types.HttpOptions(api_version="v1beta"))
    GLOBAL_CLIENT = observability.wrap_client(raw_client, chat_name="Gemini Server")
    return {
        "status": "ok",
        "source": "user",
        "message": "User API key activated with priority. Default .env key is preserved.",
        "masked_key": get_masked_key(cleaned)
    }


@app.post("/api/key/reset")
async def reset_key():
    """Clears User API key and reverts back to default .env key."""
    global USER_CUSTOM_API_KEY, GLOBAL_CLIENT
    USER_CUSTOM_API_KEY = None
    orchestrator.set_user_api_key(None)
    env_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    raw_client = genai.Client(api_key=env_key, http_options=types.HttpOptions(api_version="v1beta"))
    GLOBAL_CLIENT = observability.wrap_client(raw_client, chat_name="Gemini Server")
    return {
        "status": "ok",
        "source": "env",
        "message": "Reverted back to default .env API key.",
        "masked_key": get_masked_key(env_key)
    }


@app.post("/api/model/select")
async def select_model(req: ModelSelectRequest):
    """Switches active Complex, Lite, and/or Chat models."""
    if req.complex_model:
        c_key = req.complex_model.strip()
        if c_key in orchestrator.SUPPORTED_COMPLEX_MODELS:
            SESSION["complex_model"] = orchestrator.SUPPORTED_COMPLEX_MODELS[c_key]
            SESSION["model"] = SESSION["complex_model"]
    if req.lite_model:
        l_key = req.lite_model.strip()
        if l_key in orchestrator.SUPPORTED_LITE_MODELS:
            SESSION["lite_model"] = orchestrator.SUPPORTED_LITE_MODELS[l_key]
    return {
        "status": "ok",
        "complex_model": SESSION.get("complex_model", "gemini-3.6-flash"),
        "lite_model": SESSION.get("lite_model", "gemini-3.1-flash-lite")
    }


@app.post("/api/projects/{project_id}/like")
async def like_project(project_id: str):
    """Accepts staged version and promotes it to .backup/ baseline."""
    res = project_store.promote_staged_to_baseline(project_id)
    return res


@app.post("/api/projects/{project_id}/dislike")
async def dislike_project(project_id: str):
    """Rejects staged version and restores root files from .backup/ baseline."""
    res = project_store.revert_staged_from_baseline(project_id)
    return res


@app.post("/api/reset")
async def reset_session():
    """Resets the chat context to a blank slate (/new)."""
    SESSION["messages"] = []
    return {"status": "ok", "message": "Context reset to fresh session"}


@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    """Updates thinking budget, generation temperature, and models live."""
    if req.thinking_budget is not None:
        SESSION["thinking_budget"] = max(0, min(req.thinking_budget, 32768))
    if req.temperature is not None:
        SESSION["temperature"] = max(0.0, min(req.temperature, 2.0))
    if req.complex_model:
        c_key = req.complex_model.strip()
        if c_key in orchestrator.SUPPORTED_COMPLEX_MODELS:
            SESSION["complex_model"] = orchestrator.SUPPORTED_COMPLEX_MODELS[c_key]
            SESSION["model"] = SESSION["complex_model"]
    if req.lite_model:
        l_key = req.lite_model.strip()
        if l_key in orchestrator.SUPPORTED_LITE_MODELS:
            SESSION["lite_model"] = orchestrator.SUPPORTED_LITE_MODELS[l_key]
    if req.chat_only is not None:
        SESSION["chat_only"] = bool(req.chat_only)
    if req.chat_model:
        c_mod = req.chat_model.strip().lower()
        if c_mod in direct_chat.SUPPORTED_CHAT_ONLY_MODELS:
            SESSION["chat_model"] = direct_chat.SUPPORTED_CHAT_ONLY_MODELS[c_mod]
    if req.chat_temperature is not None:
        SESSION["chat_temperature"] = max(0.0, min(float(req.chat_temperature), 2.0))
    if req.chat_budget is not None:
        SESSION["chat_budget"] = max(0, min(int(req.chat_budget), 32768))

    return {
        "status": "ok",
        "thinking_budget": SESSION["thinking_budget"],
        "temperature": SESSION["temperature"],
        "complex_model": SESSION.get("complex_model", "gemini-3.6-flash"),
        "lite_model": SESSION.get("lite_model", "gemini-3.1-flash-lite"),
        "chat_only": SESSION.get("chat_only", False),
        "chat_model": SESSION.get("chat_model", "gemini-3.1-flash-lite"),
        "chat_temperature": SESSION.get("chat_temperature", 0.7),
        "chat_budget": SESSION.get("chat_budget", 0)
    }


@app.get("/api/artifacts")
async def list_artifacts():
    """Lists all files currently in output folder with details."""
    files = []
    if OUTPUT_DIR.exists():
        for p in sorted(OUTPUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if p.is_file():
                ext = p.suffix.lower()
                ftype = "other"
                if ext in [".html", ".htm"]:
                    ftype = "html"
                elif ext == ".css":
                    ftype = "css"
                elif ext in [".png", ".jpg", ".jpeg", ".webp", ".gif"]:
                    ftype = "image"
                elif ext == ".svg":
                    ftype = "svg"
                elif ext == ".js":
                    ftype = "javascript"
                elif ext == ".json":
                    ftype = "json"
                elif ext == ".py":
                    ftype = "python"
                
                files.append({
                    "name": p.name,
                    "size": p.stat().st_size,
                    "mtime": p.stat().st_mtime,
                    "type": ftype,
                    "url": f"/api/artifacts/{p.name}"
                })
    return {"artifacts": files, "count": len(files)}


@app.get("/api/artifacts/{filename}")
async def get_artifact(filename: str):
    """Serves a specific generated artifact file."""
    # Sanitize filename
    safe_name = os.path.basename(filename)
    file_path = OUTPUT_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    media_type = None
    if safe_name.endswith(".html"):
        media_type = "text/html; charset=utf-8"
    elif safe_name.endswith(".css"):
        media_type = "text/css; charset=utf-8"
    elif safe_name.endswith(".svg"):
        media_type = "image/svg+xml"
    elif safe_name.endswith(".js"):
        media_type = "application/javascript"
    elif safe_name.endswith(".json"):
        media_type = "application/json"
    
    return FileResponse(file_path, media_type=media_type)


@app.get("/api/projects")
async def list_projects():
    """Lists all pr-* projects with metadata and file counts."""
    projects = project_store.list_all_projects()
    next_id = project_store.get_next_project_id()
    return {"projects": projects, "next_id": next_id}


@app.get("/api/projects/{project_id}")
async def get_project_details(project_id: str):
    """Returns project metadata and text contents of its files."""
    meta = project_store.load_project_meta(project_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Project not found")
    files = project_store.get_project_files(project_id)
    return {"meta": meta, "files": files}


@app.get("/api/projects/{project_id}/{filepath:path}")
async def serve_project_file(project_id: str, filepath: str):
    """Serves a static file from a specific project folder for live sandbox preview."""
    safe_pid = os.path.basename(project_id)
    p_dir = project_store.PROJECTS_DIR / safe_pid
    if not p_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If empty filepath or trailing slash, default to index.html
    if not filepath or filepath.endswith("/"):
        filepath = (filepath + "index.html").lstrip("/")
    
    target_file = (p_dir / filepath).resolve()
    # Path traversal check
    if not str(target_file).startswith(str(p_dir.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail=f"File '{filepath}' not found in {project_id}")

    fn_lower = target_file.name.lower()
    media_type = None
    if fn_lower.endswith(".html") or fn_lower.endswith(".htm"):
        media_type = "text/html; charset=utf-8"
    elif fn_lower.endswith(".css"):
        media_type = "text/css; charset=utf-8"
    elif fn_lower.endswith(".js"):
        media_type = "application/javascript"
    elif fn_lower.endswith(".json"):
        media_type = "application/json"
    elif fn_lower.endswith(".svg"):
        media_type = "image/svg+xml"
    elif fn_lower.endswith(".png"):
        media_type = "image/png"
    elif fn_lower.endswith(".jpg") or fn_lower.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif fn_lower.endswith(".webp"):
        media_type = "image/webp"

    headers = {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    if fn_lower.endswith(".html") or fn_lower.endswith(".htm"):
        try:
            raw_html = target_file.read_text(encoding="utf-8")
            mtime = int(target_file.stat().st_mtime)
            # Automatically cache-bust any local CSS or JS files referenced in the HTML
            busted_html = re.sub(
                r'(href|src)=["\']([^"\':]+\.(?:css|js))(?:\?[^"\']*)?["\']',
                rf'\1="\2?t={mtime}"',
                raw_html
            )
            from starlette.responses import Response
            return Response(content=busted_html, media_type=media_type, headers=headers)
        except Exception:
            pass

    return FileResponse(target_file, media_type=media_type, headers=headers)


@app.post("/api/projects/new")
async def create_empty_project():
    """Initializes a new incremental project (pr-1, pr-2, etc.)."""
    meta = project_store.create_new_project()
    return {"status": "ok", "project": meta}


ACTIVE_TASKS: list[asyncio.Task] = []


@app.post("/api/chat/stop")
async def stop_execution():
    """Immediately force-stops active LLM streaming and orchestration tasks."""
    orchestrator.request_stop()
    direct_chat.request_stop()
    for t in list(ACTIVE_TASKS):
        if not t.done():
            t.cancel()
    ACTIVE_TASKS.clear()
    return {"status": "ok", "message": "Execution force stopped."}


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest, request: Request):
    """
    Streams multi-agent progress, thoughts, and assembled code using SSE.
    If Chat-Only mode is active, routes directly to direct_chat without multi-agent overhead.
    Otherwise uses pure Gemini Multi-Agent Orchestration (orchestrator.py).
    """
    orchestrator.reset_stop()
    direct_chat.reset_stop()
    raw_attachments = [a.model_dump() for a in req.attachments] if req.attachments else None
    is_chat_only = bool(req.chat_only or SESSION.get("chat_only", False))

    if is_chat_only:
        active_chat_model = req.chat_model or SESSION.get("chat_model", "gemini-3.5-flash-lite")
        active_chat_temp = req.chat_temperature if req.chat_temperature is not None else SESSION.get("chat_temperature", 0.7)
        active_chat_budget = req.chat_budget if req.chat_budget is not None else SESSION.get("chat_budget", 0)

        target_project_id = req.project_id
        if not target_project_id or not (project_store.PROJECTS_DIR / target_project_id).exists():
            projects = project_store.list_all_projects()
            if projects:
                target_project_id = projects[0]["id"]
            else:
                meta = project_store.create_new_project(prompt=req.message)
                target_project_id = meta["id"]

        async def chat_only_event_generator() -> AsyncGenerator[str, None]:
            thought_buffer = []
            answer_buffer = []

            chat_queue: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def run_chat_in_thread():
                try:
                    for chunk in direct_chat.execute_direct_chat_stream(
                        message=req.message,
                        model=active_chat_model,
                        temperature=active_chat_temp,
                        thinking_budget=active_chat_budget,
                        history=SESSION.get("messages", []),
                        attachments=raw_attachments,
                        api_key=get_active_api_key()
                    ):
                        loop.call_soon_threadsafe(chat_queue.put_nowait, chunk)
                except Exception as ex:
                    loop.call_soon_threadsafe(chat_queue.put_nowait, {"type": "error", "error": str(ex)})
                finally:
                    loop.call_soon_threadsafe(chat_queue.put_nowait, {"type": "_STREAM_DONE_"})

            chat_task = asyncio.create_task(asyncio.to_thread(run_chat_in_thread))
            ACTIVE_TASKS.append(chat_task)
            chat_task.add_done_callback(lambda t: ACTIVE_TASKS.remove(t) if t in ACTIVE_TASKS else None)

            saved_files = []
            final_answer = ""
            full_thought = ""

            try:
                while True:
                    chunk = await chat_queue.get()
                    c_type = chunk.get("type")

                    if c_type == "_STREAM_DONE_":
                        break
                    elif c_type == "thought":
                        content = chunk.get("content", "")
                        thought_buffer.append(content)
                        yield f"data: {json.dumps({'type': 'thought', 'content': content})}\n\n"
                    elif c_type == "token":
                        content = chunk.get("content", "")
                        answer_buffer.append(content)
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                    elif c_type == "done":
                        final_answer = chunk.get("full_answer", "".join(answer_buffer))
                        full_thought = chunk.get("full_thought", "".join(thought_buffer))
                    elif c_type == "error":
                        yield f"data: {json.dumps({'type': 'error', 'error': chunk.get('error', 'Error in direct chat')})}\n\n"
                        break

                if not final_answer:
                    final_answer = "".join(answer_buffer)
                if not full_thought:
                    full_thought = "".join(thought_buffer)

                # Extract HTML/CSS if returned in code blocks to enable Live Preview Sandbox & Code Inspector
                html_code, css_code = extract_html_and_css(final_answer)
                if html_code or css_code:
                    p_dir = project_store.PROJECTS_DIR / target_project_id
                    p_dir.mkdir(parents=True, exist_ok=True)
                    if html_code:
                        (p_dir / "index.html").write_text(html_code, encoding="utf-8")
                        saved_files.append({"name": "index.html", "path": str(p_dir / "index.html"), "size": len(html_code.encode("utf-8")), "type": "html", "is_primary": True})
                    if css_code:
                        (p_dir / "styles.css").write_text(css_code, encoding="utf-8")
                        saved_files.append({"name": "styles.css", "path": str(p_dir / "styles.css"), "size": len(css_code.encode("utf-8")), "type": "css", "is_primary": True})

                SESSION["messages"].append({"role": "user", "content": req.message})
                SESSION["messages"].append({
                    "role": "model",
                    "content": final_answer,
                    "thought": full_thought,
                    "model": active_chat_model,
                    "temperature": active_chat_temp,
                    "thinking_budget": active_chat_budget
                })

                summary = {
                    "type": "done",
                    "project_id": target_project_id,
                    "is_modified": False,
                    "is_chat": True,
                    "chat_only": True,
                    "saved_artifacts": saved_files,
                    "preview_url": f"/api/projects/{target_project_id}/index.html",
                    "total_thought_chars": len(full_thought),
                    "total_answer_chars": len(final_answer),
                    "has_html": bool(html_code),
                    "has_css": bool(css_code),
                    "model_used": active_chat_model,
                    "temperature": active_chat_temp,
                    "thinking_budget": active_chat_budget
                }
                yield f"data: {json.dumps(summary)}\n\n"

            except Exception as ex:
                yield f"data: {json.dumps({'type': 'error', 'error': str(ex)})}\n\n"

        return StreamingResponse(
            chat_only_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # 1. Determine Target Project ID & Mode for Multi-Agent Studio Flow
    parent_project_id = None
    if req.is_modifier:
        # User explicitly requested modification/upgrade (Modifier: ON)
        target_project_id = req.project_id
        if not target_project_id or not (project_store.PROJECTS_DIR / target_project_id).exists():
            projects = project_store.list_all_projects()
            if projects:
                target_project_id = projects[0]["id"]
            else:
                meta = project_store.create_new_project(prompt=req.message)
                target_project_id = meta["id"]
                req.is_modifier = False
    else:
        # Generation Mode (Modifier: OFF / New Chat / New Project)
        # Check if requested project exists and is totally blank (0 code files)
        if req.project_id and project_store.is_project_blank(req.project_id):
            # If the current project is totally blank, reuse it without creating an extra project
            target_project_id = req.project_id
            req.is_modifier = False
        elif req.project_id and (project_store.PROJECTS_DIR / req.project_id).exists() and not project_store.is_project_blank(req.project_id):
            # Project exists and has baseline files: check intent to prevent accidental project resets
            active_lite_for_intent = req.lite_model or SESSION.get("lite_model", orchestrator.DEFAULT_LITE_MODEL)
            if active_lite_for_intent in orchestrator.SUPPORTED_LITE_MODELS:
                active_lite_for_intent = orchestrator.SUPPORTED_LITE_MODELS[active_lite_for_intent]
            else:
                active_lite_for_intent = orchestrator.DEFAULT_LITE_MODEL

            intent_check = orchestrator.classify_conversation_intent(
                user_prompt=req.message,
                project_id=req.project_id,
                has_files=True,
                lite_model=active_lite_for_intent
            )
            detected_intent = intent_check.get("intent", "create")
            if detected_intent in ["upgrade", "chat"]:
                target_project_id = req.project_id
                req.is_modifier = (detected_intent == "upgrade")
            else:
                meta = project_store.create_new_project(prompt=req.message)
                target_project_id = meta["id"]
                req.is_modifier = False
        else:
            # Otherwise (no project active), create a brand new project!
            meta = project_store.create_new_project(prompt=req.message)
            target_project_id = meta["id"]
            req.is_modifier = False

    active_complex = req.complex_model or SESSION.get("complex_model", orchestrator.DEFAULT_COMPLEX_MODEL)
    if active_complex in orchestrator.SUPPORTED_COMPLEX_MODELS:
        active_complex = orchestrator.SUPPORTED_COMPLEX_MODELS[active_complex]
    else:
        active_complex = orchestrator.DEFAULT_COMPLEX_MODEL

    active_lite = req.lite_model or SESSION.get("lite_model", orchestrator.DEFAULT_LITE_MODEL)
    if active_lite in orchestrator.SUPPORTED_LITE_MODELS:
        active_lite = orchestrator.SUPPORTED_LITE_MODELS[active_lite]
    else:
        active_lite = orchestrator.DEFAULT_LITE_MODEL

    active_budget = req.thinking_budget if req.thinking_budget is not None else SESSION.get("thinking_budget", 1024)
    active_temp = req.temperature if req.temperature is not None else SESSION.get("temperature", 0.7)

    queue: asyncio.Queue = asyncio.Queue()

    def handle_event(event_text: str):
        queue.put_nowait({"type": "thought", "content": f"{event_text}\n"})

    loop = asyncio.get_running_loop()

    async def run_orchestration_task():
        try:
            result = await loop.run_in_executor(
                None,
                lambda: orchestrator.orchestrate_generation(
                    prompt=req.message,
                    project_id=target_project_id,
                    is_upgrade=req.is_modifier,
                    complex_model=active_complex,
                    lite_model=active_lite,
                    temperature=active_temp,
                    thinking_budget=active_budget,
                    attachments=raw_attachments,
                    on_event=handle_event
                )
            )
            await queue.put({"type": "_DONE_", "data": result})
        except (asyncio.CancelledError, InterruptedError):
            await queue.put({"type": "_STOPPED_"})
        except Exception as e:
            if orchestrator.is_stop_requested() or "stopped by user" in str(e).lower():
                await queue.put({"type": "_STOPPED_"})
            else:
                await queue.put({"type": "_ERROR_", "error": str(e)})

    orch_task = asyncio.create_task(run_orchestration_task())
    ACTIVE_TASKS.append(orch_task)
    orch_task.add_done_callback(lambda t: ACTIVE_TASKS.remove(t) if t in ACTIVE_TASKS else None)

    async def event_generator() -> AsyncGenerator[str, None]:
        thought_buffer = []
        final_answer = ""

        try:
            while True:
                item = await queue.get()
                item_type = item.get("type")

                if item_type == "thought":
                    content = item.get("content", "")
                    thought_buffer.append(content)
                    yield f"data: {json.dumps({'type': 'thought', 'content': content})}\n\n"

                elif item_type == "_DONE_":
                    data = item["data"]
                    final_answer = data.get("assembled_text", "")
                    saved_files = data.get("saved_files", [])

                    # Stream tokens in small chunks so UI can render smoothly
                    chunk_size = 500
                    for i in range(0, len(final_answer), chunk_size):
                        tok = final_answer[i:i+chunk_size]
                        yield f"data: {json.dumps({'type': 'token', 'content': tok})}\n\n"
                        await asyncio.sleep(0.005)

                    is_chat = data.get("is_chat", False)

                    # Only save legacy artifacts if actual files were generated
                    if not is_chat and saved_files:
                        save_response_artifacts(final_answer, OUTPUT_DIR)

                    full_thought = "".join(thought_buffer)
                    active_model_used = active_lite if (is_chat or (req.is_modifier and data.get("tier") != "complex")) else active_complex
                    active_temp_used = active_temp

                    SESSION["messages"].append({"role": "user", "content": req.message})
                    SESSION["messages"].append({
                        "role": "model",
                        "content": final_answer,
                        "thought": full_thought,
                        "model": active_model_used,
                        "temperature": active_temp_used,
                        "thinking_budget": active_budget
                    })

                    summary = {
                        "type": "done",
                        "project_id": target_project_id,
                        "parent_id": parent_project_id,
                        "is_modified": req.is_modifier and not is_chat,
                        "is_chat": is_chat,
                        "saved_artifacts": saved_files,
                        "preview_url": f"/api/projects/{target_project_id}/index.html",
                        "total_thought_chars": len(full_thought),
                        "total_answer_chars": len(final_answer),
                        "has_html": any(f.get("name", "").endswith(".html") for f in saved_files),
                        "has_css": any(f.get("name", "").endswith(".css") for f in saved_files),
                        "model_used": active_model_used,
                        "temperature": active_temp_used,
                        "thinking_budget": active_budget
                    }
                    yield f"data: {json.dumps(summary)}\n\n"
                    break

                elif item_type == "_STOPPED_":
                    yield f"data: {json.dumps({'type': 'stopped', 'message': 'Execution force stopped by user.'})}\n\n"
                    break

                elif item_type == "_ERROR_":
                    err_msg = item.get("error", "Unknown error")
                    yield f"data: {json.dumps({'type': 'error', 'error': err_msg})}\n\n"
                    break

        except Exception as ex:
            yield f"data: {json.dumps({'type': 'error', 'error': str(ex)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )



# Serve Static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def root():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return HTMLResponse("<h1>Chat UI is initializing...</h1>")


if __name__ == "__main__":
    import socket

    def find_free_port(start_port: int = 8080, max_attempts: int = 20) -> int:
        for p in range(start_port, start_port + max_attempts):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(("127.0.0.1", p))
                    return p
                except OSError:
                    continue
        return start_port

    port = find_free_port(8080)
    init_chat_session()
    print("=" * 65)
    print(" Gemini 3.5 Flash Lite Deep Thinking Web UI")
    print(f" Serving at: http://127.0.0.1:{port}")
    print(f" Artifacts directory: {OUTPUT_DIR}")
    print("=" * 65)
    uvicorn.run("chat_ui.server:app", host="127.0.0.1", port=port, reload=False)
