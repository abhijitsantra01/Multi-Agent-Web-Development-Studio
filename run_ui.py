import sys
import webbrowser
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ensure utf-8 stdout on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

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

PORT = find_free_port(8080)
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}"

if __name__ == "__main__":
    print("=" * 65)
    print(" ⚡ Gemini 3.5 Flash Lite Deep Thinking Studio UI")
    print(f" 🌐 Access UI at: {URL}")
    print(" 📂 Projects Folder: output/projects/")
    print(" 🧠 Features: Live SSE Streaming, Split Reader Pane, Live Sandbox")
    print(" Press Ctrl+C in terminal to stop server.")
    print("=" * 65)
    
    # Try opening browser automatically
    try:
        webbrowser.open(URL)
    except Exception:
        pass

    uvicorn.run("chat_ui.server:app", host=HOST, port=PORT, reload=True, log_level="info")
