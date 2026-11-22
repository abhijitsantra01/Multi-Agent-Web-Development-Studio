# Gemini Deep Thinking Studio & Orchestrator

An autonomous web generation studio powered by Google Gemini models (`gemini-3.8-flash`, `gemini-3.5-flash-lite`), live Server-Sent Events (SSE) streaming, a split reader pane, multi-project versioning, and an interactive live sandbox.

---

## 📁 Project Structure

```
gemini-orchestration-chat-ui/
├── chat_ui/
│   ├── server.py             # FastAPI backend (SSE streaming, project & sandbox APIs)
│   └── static/
│       ├── index.html        # Modern Studio web interface
│       ├── app.js            # Live streaming, Monaco/code viewer, sandbox bridge
│       └── styles.css        # Studio design system styling
├── run_ui.py                 # Application launcher (finds free port & opens browser)
├── orchestrator.py           # Multi-agent Gemini orchestration engine
├── observability.py          # LangSmith multi-agent tracing & observability engine
├── project_store.py          # Project revision, baseline & staging storage manager
├── direct_chat.py            # Direct streaming chat module
├── output/
│   └── projects/             # Project workspaces (pr-1, pr-2, ..., baseline/staged files)
├── requirements.txt          # Dedicated dependencies
├── .env                      # API keys (GEMINI_API_KEY)
└── .env.example              # Template environment configuration
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Ensure your `.env` contains your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Launch Studio UI
```bash
python run_ui.py
```
This automatically launches the local server (default: `http://127.0.0.1:8080`) and opens your browser.

---

## 🔭 LangSmith Agent Observability & Tracing

Full observability into multi-agent operations and LLM calls is natively integrated via **LangSmith**.

### Tracked Agents & Spans:
- **Studio Agent Orchestrator**: Root end-to-end execution tree.
- **Intent Router Agent**: Triage classification (`chat` vs `upgrade` vs `create`).
- **Vision & Brand Agent**: Multimodal asset inspection & brand DNA extraction.
- **Architect Agent**: Component breakdown & subtask planning.
- **Component Workers**: Individual HTML, CSS, and JS snippet generation subtasks.
- **Master Assembler Agent**: Final synthesis and code harmonization.
- **Upgrade Complexity Classifier & Tier Workers**: Lite and Complex transactional file modifiers.
- **Direct Chat Stream**: Token-by-token streaming conversation agent.
- **Gemini LLM Spans**: Token count, reasoning budget, latency, parameters, and automatic fallback failover tracking.

### Enabling LangSmith:
Add the following to your `.env` (or configure live in the Studio **Settings ⚙️ -> Observability** tab):
```env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=gemini-orchestration-studio
```
Open your [LangSmith Dashboard](https://smith.langchain.com) to view the live execution tree, token usage, latency, and step-by-step agent decisions.

