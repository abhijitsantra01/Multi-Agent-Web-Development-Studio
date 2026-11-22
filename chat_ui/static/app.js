/**
 * Gemini 3.5 Flash Lite Deep Thinking Chat & Artifact Studio
 * Frontend Application Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const appContainer = document.getElementById("app");
  const mainContainer = document.getElementById("mainContainer");
  const chatFeed = document.getElementById("chatFeed");
  const welcomeScreen = document.getElementById("welcomeScreen");
  const promptInput = document.getElementById("promptInput");
  const btnSend = document.getElementById("btnSend");
  const btnForceStop = document.getElementById("btnForceStop");
  const sendBtnLabel = document.getElementById("sendBtnLabel");
  const charCounter = document.getElementById("charCounter");
  const budgetDisplay = document.getElementById("budgetDisplay");

  // Project & Sidebar Elements
  const btnToggleProjectsSidebar = document.getElementById("btnToggleProjectsSidebar");
  const projectsSidebar = document.getElementById("projectsSidebar");
  const headerActiveProjectBadge = document.getElementById("headerActiveProjectBadge");
  const projectSearchInput = document.getElementById("projectSearchInput");
  const btnClearProjectSearch = document.getElementById("btnClearProjectSearch");
  const projectsList = document.getElementById("projectsList");
  const projectsCountPill = document.getElementById("projectsCountPill");
  const btnRefreshProjects = document.getElementById("btnRefreshProjects");
  const projectSelect = document.getElementById("projectSelect");
  const btnToggleModifier = document.getElementById("btnToggleModifier");
  const modifierBtnLabel = document.getElementById("modifierBtnLabel");
  const btnComposerModToggle = document.getElementById("btnComposerModToggle");
  const sandboxProjectBadge = document.getElementById("sandboxProjectBadge");
  const btnTriggerModifier = document.getElementById("btnTriggerModifier");

  // Multi-Agent & Model Selection Elements
  const headerComplexModelSelect = document.getElementById("headerComplexModelSelect");
  const cfgComplexModel = document.getElementById("cfgComplexModel");
  const headerLiteModelSelect = document.getElementById("headerLiteModelSelect");
  const cfgLiteModel = document.getElementById("cfgLiteModel");
  const btnResetSettings = document.getElementById("btnResetSettings");
  const reviewActionGroup = document.getElementById("reviewActionGroup");
  const stagedBadge = document.getElementById("stagedBadge");
  const btnLikeVersion = document.getElementById("btnLikeVersion");
  const btnDislikeVersion = document.getElementById("btnDislikeVersion");

  // API Key Elements
  const btnApiKey = document.getElementById("btnApiKey");
  const keyStatusIndicator = document.getElementById("keyStatusIndicator");
  const apiKeyModal = document.getElementById("apiKeyModal");
  const btnCloseApiKeyModal = document.getElementById("btnCloseApiKeyModal");
  const btnCancelApiKey = document.getElementById("btnCancelApiKey");
  const btnSaveApiKey = document.getElementById("btnSaveApiKey");
  const btnResetApiKey = document.getElementById("btnResetApiKey");
  const keySourceBadge = document.getElementById("keySourceBadge");
  const activeKeyDisplay = document.getElementById("activeKeyDisplay");
  const keyBadgeText = document.getElementById("keyBadgeText");
  const apiKeyInput = document.getElementById("apiKeyInput");
  const btnToggleKeyVis = document.getElementById("btnToggleKeyVis");
  const btnPasteClipboardKey = document.getElementById("btnPasteClipboardKey");
  const btnFullscreenPane = document.getElementById("btnFullscreenPane");

  // Attachment Elements
  const btnAttachFile = document.getElementById("btnAttachFile");
  const fileInput = document.getElementById("fileInput");
  const attachmentsBar = document.getElementById("attachmentsBar");
  const composerBox = document.getElementById("composerBox");
  
  // Toolbar Elements
  const btnFontDec = document.getElementById("btnFontDec");
  const btnFontInc = document.getElementById("btnFontInc");
  const fontLabel = document.getElementById("fontLabel");
  const btnToggleSplit = document.getElementById("btnToggleSplit");
  const splitBtnText = document.getElementById("splitBtnText");
  const btnCloseSplit = document.getElementById("btnCloseSplit");
  const widthButtons = document.querySelectorAll("[data-width]");
  
  // Search
  const searchInput = document.getElementById("searchInput");
  const searchCount = document.getElementById("searchCount");

  // Reader / Sandbox Pane Elements
  const readerPane = document.getElementById("readerPane");
  const tabDocReader = document.getElementById("tabDocReader");
  const tabSandbox = document.getElementById("tabSandbox");
  const tabCode = document.getElementById("tabCode");
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");
  const docProse = document.getElementById("docProse");
  const tocLinks = document.getElementById("tocLinks");
  const docWordCount = document.getElementById("docWordCount");
  const docCharCount = document.getElementById("docCharCount");
  const btnCopyDoc = document.getElementById("btnCopyDoc");
  const previewIframe = document.getElementById("previewIframe");
  const viewportSwitcher = document.getElementById("viewportSwitcher");
  const vpButtons = document.querySelectorAll(".vp-btn[data-width]");
  const btnReloadPreview = document.getElementById("btnReloadPreview");
  const codeInspectorContent = document.getElementById("codeInspectorContent");
  const codeFilePicker = document.getElementById("codeFilePicker");
  const btnCopyInspectedCode = document.getElementById("btnCopyInspectedCode");

  // Drawers and Modals
  const btnArtifacts = document.getElementById("btnArtifacts");
  const artifactsDrawer = document.getElementById("artifactsDrawer");
  const drawerOverlay = document.getElementById("drawerOverlay");
  const btnCloseDrawer = document.getElementById("btnCloseDrawer");
  const drawerList = document.getElementById("drawerList");
  const artifactCountBadge = document.getElementById("artifactCountBadge");
  const drawerDirPath = document.getElementById("drawerDirPath");

  const btnSettings = document.getElementById("btnSettings");
  const settingsModal = document.getElementById("settingsModal");
  const btnCloseSettings = document.getElementById("btnCloseSettings");
  const btnCancelSettings = document.getElementById("btnCancelSettings");
  const btnSaveSettings = document.getElementById("btnSaveSettings");
  const cfgBudget = document.getElementById("cfgBudget");
  const cfgBudgetValue = document.getElementById("cfgBudgetValue");
  const cfgTemp = document.getElementById("cfgTemp");
  const cfgTempValue = document.getElementById("cfgTempValue");
  const btnNewChat = document.getElementById("btnNewChat");

  // Settings Tabs & Standalone Chat Pipeline Elements
  const tabSettingsStudio = document.getElementById("tabSettingsStudio");
  const tabSettingsChat = document.getElementById("tabSettingsChat");
  const panelSettingsStudio = document.getElementById("panelSettingsStudio");
  const panelSettingsChat = document.getElementById("panelSettingsChat");
  const chatTabStatusPill = document.getElementById("chatTabStatusPill");
  const btnChatOnlyPillToggle = document.getElementById("btnChatOnlyPillToggle");
  const pillToggleLabel = document.getElementById("pillToggleLabel");
  const chatControlsSubpanel = document.getElementById("chatControlsSubpanel");
  const cfgChatOnlyModel = document.getElementById("cfgChatOnlyModel");
  const cfgChatOnlyBudget = document.getElementById("cfgChatOnlyBudget");
  const cfgChatBudgetValue = document.getElementById("cfgChatBudgetValue");
  const cfgChatOnlyTemp = document.getElementById("cfgChatOnlyTemp");
  const cfgChatTempValue = document.getElementById("cfgChatTempValue");
  const btnComposerChatOnlyBadge = document.getElementById("btnComposerChatOnlyBadge");
  const composerChatPillText = document.getElementById("composerChatPillText");

  // LangSmith Observability Elements
  const tabSettingsObservability = document.getElementById("tabSettingsObservability");
  const panelSettingsObservability = document.getElementById("panelSettingsObservability");
  const observabilityTabStatusPill = document.getElementById("observabilityTabStatusPill");
  const observabilityLiveStatus = document.getElementById("observabilityLiveStatus");
  const cfgLangSmithEnabled = document.getElementById("cfgLangSmithEnabled");
  const cfgLangSmithApiKey = document.getElementById("cfgLangSmithApiKey");
  const btnToggleLangSmithKey = document.getElementById("btnToggleLangSmithKey");
  const cfgLangSmithKeyHint = document.getElementById("cfgLangSmithKeyHint");
  const cfgLangSmithProject = document.getElementById("cfgLangSmithProject");
  const cfgLangSmithEndpoint = document.getElementById("cfgLangSmithEndpoint");
  const cfgLangSmithAgentId = document.getElementById("cfgLangSmithAgentId");
  const cfgLangSmithAgentEnv = document.getElementById("cfgLangSmithAgentEnv");
  const linkLangSmithDashboard = document.getElementById("linkLangSmithDashboard");

  // Code Modal
  const codeModal = document.getElementById("codeModal");
  const btnCloseCodeModal = document.getElementById("btnCloseCodeModal");
  const codeModalTitle = document.getElementById("codeModalTitle");
  const codeModalContent = document.getElementById("codeModalContent");
  const btnCopyModalCode = document.getElementById("btnCopyModalCode");

  // Application State
  const state = {
    fontScale: 1.0,
    thinkingBudget: 16384,
    temperature: 1.0,
    isStreaming: false,
    activeTab: "readerView",
    currentHtml: "",
    currentCss: "",
    currentRawText: "",
    latestMessageIndex: 0,
    // Projects & Modifier State
    allProjects: [],
    projectSearchQuery: "",
    activeProjectId: null,
    isModifierMode: false,
    projectFiles: {},
    activeProjectFile: "index.html",
    // Multimodal attachments
    attachments: [],
    // Model Selection & Fallback State
    complexModel: "gemini-4-hydrogen",
    liteModel: "gemini-3.5-flash-lite",
    // Standalone Chat Pipeline State
    chatOnlyMode: false,
    chatOnlyModel: "gemini-3.5-flash-lite",
    chatOnlyBudget: 0,
    chatOnlyTemp: 0.70
  };

  // Configure marked options
  if (window.marked) {
    marked.setOptions({
      breaks: true,
      gfm: true
    });
  }

  // Initialize
  fetchInitialState();
  fetchArtifacts();
  fetchProjects();

  // ==========================================================================
  // Project & Modifier Controls
  // ==========================================================================

  // Model Selector Handlers (Complex & Lite with Fallback Chains)
  if (headerComplexModelSelect) {
    headerComplexModelSelect.addEventListener("change", (e) => {
      updateComplexModel(e.target.value);
    });
  }
  if (cfgComplexModel) {
    cfgComplexModel.addEventListener("change", (e) => {
      updateComplexModel(e.target.value);
    });
  }

  if (headerLiteModelSelect) {
    headerLiteModelSelect.addEventListener("change", (e) => {
      updateLiteModel(e.target.value);
    });
  }
  if (cfgLiteModel) {
    cfgLiteModel.addEventListener("change", (e) => {
      updateLiteModel(e.target.value);
    });
  }

  async function updateComplexModel(modelName) {
    state.complexModel = modelName;
    if (headerComplexModelSelect) headerComplexModelSelect.value = modelName;
    if (cfgComplexModel) cfgComplexModel.value = modelName;
    try {
      await fetch("/api/model/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ complex_model: modelName })
      });
    } catch (err) {
      console.error("Error updating complex model:", err);
    }
  }

  async function updateLiteModel(modelName) {
    state.liteModel = modelName;
    if (headerLiteModelSelect) headerLiteModelSelect.value = modelName;
    if (cfgLiteModel) cfgLiteModel.value = modelName;
    try {
      await fetch("/api/model/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lite_model: modelName })
      });
    } catch (err) {
      console.error("Error updating lite model:", err);
    }
  }

  function formatModelName(modelId) {
    if (!modelId) return "Gemini Flash";
    if (modelId.includes("hydrogen")) return "4 Hydrogen";
    if (modelId.includes("3.8")) return "3.8 Flash";
    if (modelId.includes("3.5")) return "3.5 Flash Lite";
    if (modelId.includes("3.1")) return "3.1 Flash Lite";
    if (modelId.includes("2.5")) {
      return modelId.includes("lite") ? "2.5 Flash Lite" : "2.5 Flash";
    }
    return modelId;
  }

  // Like / Dislike Baseline Handlers
  if (btnLikeVersion) {
    btnLikeVersion.addEventListener("click", async () => {
      if (!state.activeProjectId) return;
      try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/like`, { method: "POST" });
        if (res.ok) {
          if (stagedBadge) {
            stagedBadge.textContent = "Accepted";
            stagedBadge.className = "staged-pill accepted";
          }
          btnLikeVersion.style.opacity = "0.5";
          btnDislikeVersion.style.opacity = "0.5";
        }
      } catch (err) {
        console.error("Error liking version:", err);
      }
    });
  }

  if (btnDislikeVersion) {
    btnDislikeVersion.addEventListener("click", async () => {
      if (!state.activeProjectId) return;
      try {
        const res = await fetch(`/api/projects/${state.activeProjectId}/dislike`, { method: "POST" });
        if (res.ok) {
          if (stagedBadge) {
            stagedBadge.textContent = "Reverted";
            stagedBadge.className = "staged-pill rejected";
          }
          previewIframe.src = `/api/projects/${state.activeProjectId}/index.html?t=${Date.now()}`;
          await loadProject(state.activeProjectId);
        }
      } catch (err) {
        console.error("Error disliking version:", err);
      }
    });
  }

  if (projectSelect) {
    projectSelect.addEventListener("change", (e) => {
      loadProject(e.target.value);
      if (e.target.value) {
        openSplitView();
        switchTab("previewView");
      }
    });
  }

  // Left Projects Sidebar Toggle Handler
  if (btnToggleProjectsSidebar) {
    btnToggleProjectsSidebar.addEventListener("click", () => {
      mainContainer.classList.toggle("sidebar-collapsed");
      const isCollapsed = mainContainer.classList.contains("sidebar-collapsed");
      btnToggleProjectsSidebar.classList.toggle("active", !isCollapsed);
      localStorage.setItem("projects_sidebar_collapsed", isCollapsed ? "1" : "0");
    });

    // Restore preference
    if (localStorage.getItem("projects_sidebar_collapsed") === "1") {
      mainContainer.classList.add("sidebar-collapsed");
      btnToggleProjectsSidebar.classList.remove("active");
    } else {
      btnToggleProjectsSidebar.classList.add("active");
    }
  }

  // Project Search & Clear Filter
  if (projectSearchInput) {
    projectSearchInput.addEventListener("input", () => {
      state.projectSearchQuery = projectSearchInput.value.trim().toLowerCase();
      if (btnClearProjectSearch) {
        btnClearProjectSearch.style.display = state.projectSearchQuery ? "inline-block" : "none";
      }
      renderProjectsList();
    });
  }

  if (btnClearProjectSearch) {
    btnClearProjectSearch.addEventListener("click", () => {
      if (projectSearchInput) projectSearchInput.value = "";
      state.projectSearchQuery = "";
      btnClearProjectSearch.style.display = "none";
      renderProjectsList();
      if (projectSearchInput) projectSearchInput.focus();
    });
  }

  if (btnRefreshProjects) {
    btnRefreshProjects.addEventListener("click", () => {
      fetchProjects();
    });
  }

  function toggleModifierMode() {
    setModifierMode(!state.isModifierMode);
  }

  function setModifierMode(enabled) {
    state.isModifierMode = enabled;
    if (btnToggleModifier) btnToggleModifier.classList.toggle("active", enabled);
    if (btnComposerModToggle) btnComposerModToggle.classList.toggle("active", enabled);
    if (modifierBtnLabel) modifierBtnLabel.textContent = enabled ? "Modifier: ON" : "Modifier: OFF";
    if (btnComposerModToggle) {
      const span = btnComposerModToggle.querySelector("span");
      if (span) span.textContent = enabled ? "🔧 Modifier: ON" : "🔧 Modifier: OFF";
    }
    sendBtnLabel.textContent = enabled ? "Modify & Upgrade" : "Generate";

    if (enabled && !state.activeProjectId) {
      // Auto-select latest project from dropdown
      const options = Array.from(projectSelect.options).filter(o => o.value);
      if (options.length > 0) {
        projectSelect.value = options[0].value;
        loadProject(options[0].value);
      }
    }
  }

  if (btnToggleModifier) btnToggleModifier.addEventListener("click", toggleModifierMode);
  if (btnComposerModToggle) btnComposerModToggle.addEventListener("click", toggleModifierMode);

  btnTriggerModifier.addEventListener("click", () => {
    setModifierMode(true);
    promptInput.focus();
    promptInput.placeholder = `Describe specific changes or additions for ${state.activeProjectId} (updates existing project in-place)...`;
  });

  // ==========================================================================
  // Multimodal File & Screenshot Attachments
  // ==========================================================================

  btnAttachFile.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files) {
      Array.from(e.target.files).forEach(f => readAndAddFile(f));
    }
    fileInput.value = "";
  });

  // Clipboard screenshot paste (Ctrl+V)
  window.addEventListener("paste", (e) => {
    const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.indexOf("image") !== -1) {
        const blob = item.getAsFile();
        readAndAddFile(blob, `screenshot_${Date.now()}.png`, item.type || "image/png");
      }
    }
  });

  // Drag and drop onto composer box
  ["dragenter", "dragover"].forEach(evt => {
    composerBox.addEventListener(evt, (e) => {
      e.preventDefault();
      composerBox.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach(evt => {
    composerBox.addEventListener(evt, (e) => {
      e.preventDefault();
      composerBox.classList.remove("drag-over");
    });
  });

  composerBox.addEventListener("drop", (e) => {
    e.preventDefault();
    composerBox.classList.remove("drag-over");
    if (e.dataTransfer && e.dataTransfer.files) {
      Array.from(e.dataTransfer.files).forEach(f => readAndAddFile(f));
    }
  });

  function readAndAddFile(file, customName, customMime) {
    const fileName = customName || file.name;
    const fileMime = customMime || file.type || "application/octet-stream";
    const isImg = fileMime.startsWith("image/") || /\.(png|jpe?g|webp|gif)$/i.test(fileName);

    const reader = new FileReader();
    if (isImg && !fileName.endsWith(".svg")) {
      reader.onload = (e) => {
        state.attachments.push({
          name: fileName,
          mimeType: fileMime,
          dataB64: e.target.result,
          size: file.size,
          isImage: true
        });
        renderAttachments();
      };
      reader.readAsDataURL(file);
    } else {
      reader.onload = (e) => {
        state.attachments.push({
          name: fileName,
          mimeType: fileMime,
          content: e.target.result,
          size: file.size,
          isImage: false
        });
        renderAttachments();
      };
      reader.readAsText(file);
    }
  }

  function renderAttachments() {
    attachmentsBar.innerHTML = "";
    if (state.attachments.length === 0) {
      attachmentsBar.style.display = "none";
      return;
    }
    attachmentsBar.style.display = "flex";

    state.attachments.forEach((att, idx) => {
      const chip = document.createElement("div");
      chip.className = "attachment-chip";
      const sizeStr = formatBytes(att.size || 0);

      let previewEl = "";
      if (att.isImage && att.dataB64) {
        previewEl = `<img src="${att.dataB64}" class="attachment-thumb" alt="${att.name}">`;
      } else {
        previewEl = `<span class="attachment-icon">📄</span>`;
      }

      chip.innerHTML = `
        ${previewEl}
        <div class="attachment-info">
          <span class="attachment-name" title="${att.name}">${att.name}</span>
          <span class="attachment-size">${sizeStr}</span>
        </div>
        <button type="button" class="attachment-remove" title="Remove attachment" data-idx="${idx}">✕</button>
      `;

      chip.querySelector(".attachment-remove").addEventListener("click", (e) => {
        e.stopPropagation();
        state.attachments.splice(idx, 1);
        renderAttachments();
      });

      attachmentsBar.appendChild(chip);
    });
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  // ==========================================================================
  // Event Listeners: Composer & Chat
  // ==========================================================================

  promptInput.addEventListener("input", () => {
    promptInput.style.height = "auto";
    promptInput.style.height = Math.min(promptInput.scrollHeight, 180) + "px";
    charCounter.textContent = `${promptInput.value.length.toLocaleString()} chars`;
  });

  promptInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  });

  btnSend.addEventListener("click", handleSendMessage);

  let activeStreamAbortController = null;

  async function forceStopExecution() {
    if (!state.isStreaming) return;

    if (activeStreamAbortController) {
      try {
        activeStreamAbortController.abort();
      } catch (e) {}
      activeStreamAbortController = null;
    }

    try {
      await fetch("/api/chat/stop", { method: "POST" });
    } catch (e) {
      console.warn("Stop request failed:", e);
    }

    state.isStreaming = false;
    if (btnForceStop) btnForceStop.style.display = "none";
    if (btnSend) {
      btnSend.style.display = "inline-flex";
      btnSend.disabled = false;
      const btnLabelText = state.chatOnlyMode ? "Chat" : (state.isModifierMode ? "Modify & Upgrade" : "Generate");
      btnSend.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg><span id="sendBtnLabel">${btnLabelText}</span>`;
    }

    const activeModelMsg = chatFeed.querySelector(".model-message-container:last-child");
    if (activeModelMsg) {
      const dot = activeModelMsg.querySelector(".status-dot");
      if (dot) dot.classList.remove("pulse");
      const content = activeModelMsg.querySelector(".message-body-content");
      if (content && !content.querySelector(".execution-stopped-badge")) {
        content.innerHTML += `<div class="execution-stopped-badge">⏹️ Execution stopped by user</div>`;
      }
    }
  }

  if (btnForceStop) {
    btnForceStop.addEventListener("click", forceStopExecution);
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && state.isStreaming) {
      forceStopExecution();
    }
  });

  // Preset prompts: click populates textarea, resizes, and focuses
  document.querySelectorAll(".preset-card").forEach((card) => {
    card.addEventListener("click", () => {
      const promptText = card.getAttribute("data-prompt");
      if (promptInput && promptText) {
        promptInput.value = promptText;
        promptInput.style.height = "auto";
        promptInput.style.height = Math.min(promptInput.scrollHeight, 180) + "px";
        if (charCounter) charCounter.textContent = `${promptInput.value.length.toLocaleString()} chars`;
        promptInput.focus();
        promptInput.dispatchEvent(new Event("input"));
      }
    });
  });

  // Quick pills
  document.querySelectorAll(".pill-btn").forEach((pill) => {
    pill.addEventListener("click", () => {
      const text = pill.getAttribute("data-text");
      promptInput.value = text;
      promptInput.dispatchEvent(new Event("input"));
      promptInput.focus();
    });
  });

  // New Chat (/new) - Reset Context to Blank Slate
  if (btnNewChat) {
    btnNewChat.addEventListener("click", async () => {
      if (confirm("Reset conversation context and start fresh project?")) {
        try {
          await fetch("/api/reset", { method: "POST" });
          if (chatFeed) {
            chatFeed.innerHTML = "";
            chatFeed.style.display = "none";
          }
          if (welcomeScreen) welcomeScreen.style.display = "flex";
          state.activeProjectId = null;
          if (projectSelect) projectSelect.value = "";
          if (headerActiveProjectBadge) {
            headerActiveProjectBadge.textContent = "";
            headerActiveProjectBadge.style.display = "none";
          }
          if (sandboxProjectBadge) sandboxProjectBadge.style.display = "none";
          if (btnTriggerModifier) btnTriggerModifier.style.display = "none";
          if (previewIframe) {
            previewIframe.removeAttribute("srcdoc");
            previewIframe.src = "about:blank";
          }
          state.projectFiles = {};
          renderCodeFileChips({});
          setModifierMode(false);
          closeSplitView();
          await fetchProjects(false);
        } catch (e) {
          console.error(e);
        }
      }
    });
  }

  // ==========================================================================
  // Chat Streaming Logic
  // ==========================================================================

  async function handleSendMessage() {
    const text = promptInput.value.trim();
    if ((!text && state.attachments.length === 0) || state.isStreaming) return;

    // Switch from welcome screen to active chat feed
    if (welcomeScreen) welcomeScreen.style.display = "none";
    if (chatFeed) chatFeed.style.display = "flex";

    // Copy attachments for message rendering and payload
    const sentAttachments = [...state.attachments];
    state.attachments = [];
    renderAttachments();

    // 1. Render User Message
    appendUserMessage(text, sentAttachments);
    promptInput.value = "";
    promptInput.style.height = "auto";
    charCounter.textContent = "0 chars";

    // 2. Prepare Model Message Bubble
    state.isStreaming = true;
    if (btnSend) btnSend.style.display = "none";
    if (btnForceStop) btnForceStop.style.display = "inline-flex";

    activeStreamAbortController = new AbortController();

    const modelMsgEl = createModelMessageElement();
    chatFeed.appendChild(modelMsgEl);
    chatFeed.scrollTop = chatFeed.scrollHeight;

    const thoughtBodyEl = modelMsgEl.querySelector(".thought-body");
    const thoughtWordCountEl = modelMsgEl.querySelector(".thought-word-count");
    const thoughtAccordionEl = modelMsgEl.querySelector(".thought-accordion");
    const contentBodyEl = modelMsgEl.querySelector(".message-body-content");
    const statusDotEl = modelMsgEl.querySelector(".status-dot");

    let fullThought = "";
    let fullAnswer = "";
    let lastDoneData = null;

    try {
      const payload = {
        message: text,
        thinking_budget: state.thinkingBudget,
        temperature: state.temperature,
        project_id: state.activeProjectId,
        is_modifier: state.isModifierMode,
        complex_model: state.complexModel,
        lite_model: state.liteModel,
        chat_only: state.chatOnlyMode,
        chat_model: state.chatOnlyModel,
        chat_temperature: state.chatOnlyTemp,
        chat_budget: state.chatOnlyBudget,
        attachments: sentAttachments.map(a => ({
          name: a.name,
          mime_type: a.mimeType,
          data_b64: a.dataB64 || null,
          content: a.content || null
        }))
      };

      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: activeStreamAbortController.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // keep last unfinished line

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.replace(/^data: /, "").trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            if (data.type === "thought") {
              fullThought += data.content;
              thoughtAccordionEl.style.display = "block";
              thoughtBodyEl.textContent = fullThought;
              const words = fullThought.split(/\s+/).filter(Boolean).length;
              thoughtWordCountEl.textContent = `${words.toLocaleString()} words of deep reasoning`;
            } else if (data.type === "token") {
              fullAnswer += data.content;
              renderMarkdownToElement(contentBodyEl, fullAnswer);
              chatFeed.scrollTop = chatFeed.scrollHeight;
            } else if (data.type === "done") {
              lastDoneData = data;

              // Dynamically reflect active model and live temperature badge
              if (data.model_used) {
                const modelBadgeTitle = modelMsgEl.querySelector(".model-badge-info h3");
                if (modelBadgeTitle) modelBadgeTitle.textContent = formatModelName(data.model_used);
              }
              const budgetBadgeEl = modelMsgEl.querySelector(".budget-badge");
              if (budgetBadgeEl) {
                const bVal = data.thinking_budget !== undefined ? data.thinking_budget : (state.chatOnlyMode ? state.chatOnlyBudget : state.thinkingBudget);
                const tVal = data.temperature !== undefined ? data.temperature : (state.chatOnlyMode ? state.chatOnlyTemp : state.temperature);
                budgetBadgeEl.textContent = `${Number(bVal).toLocaleString()} tok | T=${Number(tVal).toFixed(2)}`;
              }

              // Project Extraction & Saving Complete
              if (data.project_id && (!data.is_chat || data.has_html || (data.saved_artifacts && data.saved_artifacts.length > 0))) {
                state.activeProjectId = data.project_id;
                await fetchProjects();
                await loadProject(data.project_id);
                openSplitView();
                switchTab("previewView");
              }

              if (data.saved_artifacts && data.saved_artifacts.length > 0) {
                renderArtifactsCard(modelMsgEl, data.saved_artifacts, data.project_id);
                fetchArtifacts(); // refresh drawer
              }
            } else if (data.type === "stopped") {
              contentBodyEl.innerHTML += `<div class="execution-stopped-badge">⏹️ ${data.message || "Execution stopped by user."}</div>`;
              chatFeed.scrollTop = chatFeed.scrollHeight;
            } else if (data.type === "error") {
              contentBodyEl.innerHTML += `<div style="color:var(--rose);margin-top:10px;">[!] Error: ${data.error}</div>`;
            }
          } catch (err) {
            console.error("JSON parse error on SSE chunk:", err);
          }
        }
      }

      // Finish streaming
      state.currentRawText = fullAnswer;
      decorateCodeBlocks(contentBodyEl);

      // Always update Reader Desk with generated output
      updateReaderDesk(fullAnswer, fullThought);

      // Extract and cache code for Preview and Inspector
      extractAndCacheCode(fullAnswer);

      // Status indicator to complete
      if (statusDotEl) {
        statusDotEl.classList.remove("pulse");
      }

    } catch (err) {
      if (err.name === "AbortError") {
        if (!contentBodyEl.querySelector(".execution-stopped-badge")) {
          contentBodyEl.innerHTML += `<div class="execution-stopped-badge">⏹️ Execution force stopped by user</div>`;
        }
      } else {
        console.error(err);
        contentBodyEl.innerHTML += `<div style="color:var(--rose);margin-top:10px;">[!] Connection Error: ${err.message}</div>`;
      }
    } finally {
      state.isStreaming = false;
      if (btnForceStop) btnForceStop.style.display = "none";
      if (btnSend) {
        btnSend.style.display = "inline-flex";
        btnSend.disabled = false;
        const btnLabelText = state.chatOnlyMode ? "Chat" : (state.isModifierMode ? "Modify & Upgrade" : "Generate");
        btnSend.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg><span id="sendBtnLabel">${btnLabelText}</span>`;
      }
      activeStreamAbortController = null;
      chatFeed.scrollTop = chatFeed.scrollHeight;
    }
  }

  function appendUserMessage(text, attachments = []) {
    const wrapper = document.createElement("div");
    wrapper.className = "message-wrapper user-message-container";

    let attHtml = "";
    if (attachments && attachments.length > 0) {
      attHtml = `
        <div class="user-bubble-attachments" style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">
          ${attachments.map(att => {
            if (att.isImage && att.dataB64) {
              return `<img src="${att.dataB64}" style="max-height:80px;border-radius:6px;border:1px solid rgba(255,255,255,0.2);" title="${escapeHtml(att.name)}" alt="${escapeHtml(att.name)}">`;
            } else {
              return `<span style="background:rgba(255,255,255,0.1);padding:3px 8px;border-radius:6px;font-size:0.75rem;">📄 ${escapeHtml(att.name)}</span>`;
            }
          }).join("")}
        </div>
      `;
    }

    wrapper.innerHTML = `<div class="user-bubble">${attHtml}<div>${escapeHtml(text)}</div></div>`;
    chatFeed.appendChild(wrapper);
  }


  function createModelMessageElement() {
    const wrapper = document.createElement("div");
    wrapper.className = "message-wrapper model-message-container";
    const initialModelName = formatModelName(state.isModifierMode ? state.liteModel : (state.complexModel || "4 Hydrogen"));
    const initialTemp = Number(state.temperature).toFixed(2);

    wrapper.innerHTML = `
      <div class="message-content">
        <div class="message-header">
          <div class="model-badge-info">
            <span class="status-dot pulse"></span>
            <h3>${initialModelName}</h3>
            <span class="budget-badge">${state.thinkingBudget.toLocaleString()} tok | T=${initialTemp}</span>
          </div>
          <div class="message-quick-tools">
            <button class="tool-chip btn-inspect-reader" title="Open full-screen reader pane">📖 Read in Pane</button>
            <button class="tool-chip btn-copy-msg" title="Copy text">📋 Copy</button>
          </div>
        </div>

        <!-- Collapsible Deep Thinking Accordion -->
        <div class="thought-accordion" style="display:none;">
          <div class="thought-header">
            <div class="thought-title-group">
              <span>🧠</span>
              <span>Reasoning & Strategic Planning</span>
            </div>
            <div class="thought-meta">
              <span class="thought-word-count">0 words</span>
              <svg class="thought-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
          </div>
          <div class="thought-body"></div>
        </div>

        <!-- Main Answer Body -->
        <div class="message-body-content markdown-body"></div>
      </div>
    `;

    // Toggle Thought Accordion
    const thoughtHeader = wrapper.querySelector(".thought-header");
    const thoughtAccordion = wrapper.querySelector(".thought-accordion");
    thoughtHeader.addEventListener("click", () => {
      thoughtAccordion.classList.toggle("open");
    });

    // Inspect in reader pane
    wrapper.querySelector(".btn-inspect-reader").addEventListener("click", () => {
      openSplitView();
      switchTab("readerView");
      const answerContent = wrapper.querySelector(".message-body-content").innerText;
      const thoughtContent = wrapper.querySelector(".thought-body").innerText;
      updateReaderDesk(answerContent, thoughtContent);
    });

    // Copy full answer
    wrapper.querySelector(".btn-copy-msg").addEventListener("click", () => {
      const text = wrapper.querySelector(".message-body-content").innerText;
      navigator.clipboard.writeText(text);
      const btn = wrapper.querySelector(".btn-copy-msg");
      btn.textContent = "✓ Copied!";
      setTimeout(() => (btn.textContent = "📋 Copy"), 2000);
    });

    return wrapper;
  }

  function renderMarkdownToElement(el, mdText) {
    if (window.marked) {
      el.innerHTML = marked.parse(mdText);
    } else {
      el.textContent = mdText;
    }
  }

  function decorateCodeBlocks(container) {
    container.querySelectorAll("pre").forEach((pre) => {
      // Check if already decorated
      if (pre.closest(".code-block-wrapper")) return;

      const codeEl = pre.querySelector("code");
      if (!codeEl) return;

      const className = codeEl.className || "";
      const langMatch = className.match(/language-(\w+)/);
      const lang = langMatch ? langMatch[1] : "code";

      // Count lines
      const codeText = codeEl.innerText;
      const lines = codeText.split("\n").length;

      // Wrap in custom card
      const wrapper = document.createElement("div");
      wrapper.className = "code-block-wrapper";

      const header = document.createElement("div");
      header.className = "code-block-header";
      header.innerHTML = `
        <div class="code-lang-tag">
          <span>${lang}</span>
          <span style="color:#64748b;font-weight:normal;">• ${lines} lines</span>
        </div>
        <div class="code-header-actions">
          ${lang === "html" || lang === "svg" ? `<button class="code-action-btn btn-preview-code">⚡ Live Preview</button>` : ""}
          <button class="code-action-btn btn-expand-code">⛶ Expand</button>
          <button class="code-action-btn btn-copy-code">📋 Copy</button>
        </div>
      `;

      pre.parentNode.insertBefore(wrapper, pre);
      wrapper.appendChild(header);
      wrapper.appendChild(pre);

      // Syntax highlight
      if (window.hljs) {
        hljs.highlightElement(codeEl);
      }

      // Action Handlers
      header.querySelector(".btn-copy-code").addEventListener("click", () => {
        navigator.clipboard.writeText(codeText);
        const btn = header.querySelector(".btn-copy-code");
        btn.textContent = "✓ Copied";
        setTimeout(() => (btn.textContent = "📋 Copy"), 2000);
      });

      header.querySelector(".btn-expand-code").addEventListener("click", () => {
        openCodeModal(`${lang.toUpperCase()} Code (${lines} lines)`, codeText, lang);
      });

      const previewBtn = header.querySelector(".btn-preview-code");
      if (previewBtn) {
        previewBtn.addEventListener("click", () => {
          openSplitView();
          switchTab("previewView");
          injectSandbox(codeText, "");
        });
      }
    });
  }

  function renderArtifactsCard(messageWrapper, artifacts, projectId = null) {
    if (!artifacts || artifacts.length === 0) return;

    let card = messageWrapper.querySelector(".artifacts-card");
    if (!card) {
      card = document.createElement("div");
      card.className = "artifacts-card";
      messageWrapper.querySelector(".message-content").appendChild(card);
    }

    const pid = projectId || state.activeProjectId;
    const headerTitle = pid ? `Project ${pid} Artifacts (${artifacts.length} files saved)` : `Generated Artifacts (${artifacts.length} files saved)`;

    card.innerHTML = `
      <div class="artifacts-card-header">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
        <span>${headerTitle}</span>
      </div>
      <div class="artifacts-grid">
        ${artifacts.map(art => {
          const downloadUrl = pid ? `/api/projects/${pid}/${art.name}` : `/api/artifacts/${art.name}`;
          return `
            <div class="artifact-chip">
              <span class="art-name" title="${art.name}">📄 ${art.name}</span>
              <div class="art-actions">
                ${art.type === 'html' ? `<button class="tool-chip btn-card-preview" data-name="${art.name}" data-pid="${pid || ''}">Preview</button>` : ''}
                <a href="${downloadUrl}" download class="tool-chip">⬇</a>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    `;

    card.querySelectorAll(".btn-card-preview").forEach(btn => {
      btn.addEventListener("click", () => {
        const name = btn.getAttribute("data-name");
        const bPid = btn.getAttribute("data-pid") || state.activeProjectId;
        openSplitView();
        switchTab("previewView");
        previewIframe.removeAttribute("srcdoc");
        if (bPid) {
          previewIframe.src = `/api/projects/${bPid}/${name}?t=${Date.now()}`;
        } else {
          previewIframe.src = `/api/artifacts/${name}?t=${Date.now()}`;
        }
      });
    });
  }

  // ==========================================================================
  // Reader Desk & Sandbox Pane Logic (Built for Large Outputs)
  // ==========================================================================

  function openSplitView() {
    mainContainer.classList.add("split-active");
    if (btnToggleSplit) btnToggleSplit.classList.add("active");
    if (splitBtnText) splitBtnText.textContent = "Close Pane";
  }

  function closeSplitView() {
    if (readerPane && readerPane.classList.contains("pane-fullscreen")) {
      toggleFullscreenPane(false);
    }
    mainContainer.classList.remove("split-active");
    if (btnToggleSplit) btnToggleSplit.classList.remove("active");
    if (splitBtnText) splitBtnText.textContent = "Split View";
  }

  function toggleFullscreenPane(forceState) {
    if (!readerPane) return;
    if (!mainContainer.classList.contains("split-active")) {
      openSplitView();
    }
    const isFs = typeof forceState === "boolean" ? forceState : !readerPane.classList.contains("pane-fullscreen");
    readerPane.classList.toggle("pane-fullscreen", isFs);

    if (btnFullscreenPane) {
      btnFullscreenPane.classList.toggle("active", isFs);
      const expandIcon = btnFullscreenPane.querySelector(".fs-icon-expand");
      const collapseIcon = btnFullscreenPane.querySelector(".fs-icon-collapse");
      const label = btnFullscreenPane.querySelector(".fs-label");
      if (expandIcon) expandIcon.style.display = isFs ? "none" : "block";
      if (collapseIcon) collapseIcon.style.display = isFs ? "block" : "none";
      if (label) label.textContent = isFs ? "Exit Fullscreen" : "Fullscreen";
      btnFullscreenPane.title = isFs ? "Exit Fullscreen (Esc)" : "Expand Output Pane to Fullscreen";
    }
  }

  if (btnFullscreenPane) {
    btnFullscreenPane.addEventListener("click", () => toggleFullscreenPane());
  }

  // Handle ESC key to exit fullscreen pane
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && readerPane && readerPane.classList.contains("pane-fullscreen")) {
      toggleFullscreenPane(false);
    }
  });

  if (btnToggleSplit) {
    btnToggleSplit.addEventListener("click", () => {
      if (mainContainer.classList.contains("split-active")) {
        closeSplitView();
      } else {
        openSplitView();
      }
    });
  }

  if (btnCloseSplit) {
    btnCloseSplit.addEventListener("click", closeSplitView);
  }

  // Tab switching
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");
      switchTab(target);
    });
  });

  function switchTab(tabId) {
    state.activeTab = tabId;
    tabButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-tab") === tabId));
    tabContents.forEach(c => c.classList.toggle("active", c.id === tabId));

    if (tabId === "previewView") {
      viewportSwitcher.style.display = "flex";
      // Auto-reload preview: ensure srcdoc is removed so project src actually renders
      if (state.activeProjectId) {
        const expectedSrc = `/api/projects/${state.activeProjectId}/index.html`;
        previewIframe.removeAttribute("srcdoc");
        if (!previewIframe.src || !previewIframe.src.includes(expectedSrc) || previewIframe.src === "about:blank" || previewIframe.src === window.location.href) {
          previewIframe.src = `${expectedSrc}?t=${Date.now()}`;
        }
      } else if (state.currentHtml) {
        injectSandbox(state.currentHtml, state.currentCss);
      }
    } else {
      viewportSwitcher.style.display = "none";
    }

    if (tabId === "codeView") {
      if (state.activeProjectId && Object.keys(state.projectFiles).length > 0) {
        renderCodeFileChips(state.projectFiles);
      } else {
        updateCodeInspector();
      }
    }

    if (tabId === "readerView") {
      // If reader is empty, populate from state or last model message in feed
      if (!docProse.innerHTML.trim() || docProse.querySelector(".empty-state")) {
        let textToDisplay = state.currentRawText;
        if (!textToDisplay && chatFeed) {
          const lastModelMsg = chatFeed.querySelector(".model-message-container:last-child");
          if (lastModelMsg) {
            const bodyEl = lastModelMsg.querySelector(".message-body-content");
            const thoughtEl = lastModelMsg.querySelector(".thought-body");
            if (bodyEl) {
              textToDisplay = bodyEl.innerText || bodyEl.textContent;
              updateReaderDesk(textToDisplay, thoughtEl ? thoughtEl.innerText : "");
            }
          }
        } else if (textToDisplay) {
          updateReaderDesk(textToDisplay);
        }
      }
    }
  }

  function updateReaderDesk(answerText, thoughtText) {
    if (!answerText) return;

    // 1. Document Reader View
    renderMarkdownToElement(docProse, answerText);
    decorateCodeBlocks(docProse);

    const words = answerText.split(/\s+/).filter(Boolean).length;
    docWordCount.textContent = `${words.toLocaleString()} words`;
    docCharCount.textContent = `${answerText.length.toLocaleString()} characters`;

    // 2. Build Sticky Table of Contents
    buildTableOfContents(docProse);

    // 3. Extract HTML & CSS fallback
    extractAndCacheCode(answerText);
    if (!state.activeProjectId && state.currentHtml) {
      injectSandbox(state.currentHtml, state.currentCss);
    }
  }

  function buildTableOfContents(container) {
    tocLinks.innerHTML = "";
    const headings = container.querySelectorAll("h1, h2, h3");

    if (headings.length === 0) {
      tocLinks.innerHTML = `<span class="toc-empty">No headings in document</span>`;
      return;
    }

    headings.forEach((h, index) => {
      const id = "heading_" + index;
      h.id = id;

      const link = document.createElement("a");
      link.className = `toc-link ${h.tagName.toLowerCase()}`;
      link.textContent = h.textContent;
      link.href = `#${id}`;

      link.addEventListener("click", (e) => {
        e.preventDefault();
        h.scrollIntoView({ behavior: "smooth", block: "start" });
      });

      tocLinks.appendChild(link);
    });
  }

  function extractAndCacheCode(text) {
    if (!text) return;

    // Extract HTML (allowing attributes on fence line like filename="index.html")
    const htmlMatch = text.match(/```(?:html|htm)[^\n]*\n([\s\S]*?)(?:```|$)/i);
    if (htmlMatch) {
      state.currentHtml = htmlMatch[1].trim();
    } else if (text.includes("<!DOCTYPE html>") || text.includes("<html")) {
      const rawMatch = text.match(/(<!DOCTYPE html>[\s\S]*?<\/html>|<html[\s\S]*?<\/html>)/i);
      if (rawMatch) state.currentHtml = rawMatch[1].trim();
    }

    // Extract CSS (allowing attributes on fence line like filename="styles.css")
    const cssMatch = text.match(/```css[^\n]*\n([\s\S]*?)(?:```|$)/i);
    if (cssMatch) {
      state.currentCss = cssMatch[1].trim();
    } else if (state.currentHtml) {
      const styleMatches = [...state.currentHtml.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/gi)];
      if (styleMatches.length > 0) {
        state.currentCss = styleMatches.map(m => m[1].trim()).join("\n\n");
      }
    }

    // Extract JS
    const jsMatch = text.match(/```(?:javascript|js)[^\n]*\n([\s\S]*?)(?:```|$)/i);
    if (jsMatch) {
      state.currentJs = jsMatch[1].trim();
    }

    updateCodeInspector();
  }

  function injectSandbox(html, css) {
    if (!html) return;
    let fullDoc = html;
    if (css && !fullDoc.includes(css)) {
      fullDoc = fullDoc.replace("</head>", `<style>\n${css}\n</style></head>`);
    }
    previewIframe.srcdoc = fullDoc;
  }

  btnReloadPreview.addEventListener("click", () => {
    previewIframe.removeAttribute("srcdoc");
    if (state.activeProjectId) {
      previewIframe.src = `/api/projects/${state.activeProjectId}/index.html?t=${Date.now()}`;
    } else if (state.currentHtml) {
      injectSandbox(state.currentHtml, state.currentCss);
    } else {
      previewIframe.src = `/api/artifacts/index.html?t=${Date.now()}`;
    }
  });

  // Viewport Device Switcher
  vpButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      vpButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const width = btn.getAttribute("data-width");
      previewIframe.style.width = width;
    });
  });

  // ==========================================================================
  // Project Management & Multi-File Code Inspection
  // ==========================================================================

  async function fetchProjects(autoSelect = true) {
    try {
      const res = await fetch("/api/projects");
      if (!res.ok) return;
      const data = await res.json();
      state.allProjects = data.projects || [];
      
      if (projectSelect) {
        projectSelect.innerHTML = `<option value="">+ New Project (${data.next_id})</option>`;
        state.allProjects.forEach(p => {
          const opt = document.createElement("option");
          opt.value = p.id;
          const modTag = p.parent_id ? ` (From ${p.parent_id})` : "";
          opt.textContent = `${p.id}: ${p.title} [${p.file_count} files]${modTag}`;
          projectSelect.appendChild(opt);
        });

        if (state.activeProjectId) {
          projectSelect.value = state.activeProjectId;
        } else {
          projectSelect.value = "";
        }
      }

      renderProjectsList();

      // Auto-load latest project if none is currently active and autoSelect is enabled
      if (autoSelect && !state.activeProjectId && state.allProjects.length > 0) {
        await loadProject(state.allProjects[0].id);
      }
    } catch (err) {
      console.error("Error fetching projects:", err);
    }
  }

  function renderProjectsList() {
    if (!projectsList) return;
    const query = state.projectSearchQuery || "";
    const filtered = (state.allProjects || []).filter(p => {
      if (!query) return true;
      const idMatch = (p.id || "").toLowerCase().includes(query);
      const titleMatch = (p.title || "").toLowerCase().includes(query);
      const promptMatch = (p.prompt || "").toLowerCase().includes(query);
      return idMatch || titleMatch || promptMatch;
    });

    if (projectsCountPill) {
      projectsCountPill.textContent = (state.allProjects || []).length;
    }

    if (filtered.length === 0) {
      if (query) {
        projectsList.innerHTML = `
          <div class="empty-projects-state">
            <div style="font-size:1.2rem;margin-bottom:0.35rem;">🔍</div>
            No projects match "<strong>${escapeHtml(query)}</strong>"
          </div>
        `;
      } else {
        projectsList.innerHTML = `
          <div class="empty-projects-state">
            <div style="font-size:1.2rem;margin-bottom:0.35rem;">📁</div>
            No projects found.<br>Click <strong>New Chat</strong> or generate your first landing page!
          </div>
        `;
      }
      return;
    }

    projectsList.innerHTML = filtered.map(p => {
      const isActive = p.id === state.activeProjectId;
      const fileCount = p.file_count || (p.files ? p.files.length : 0);
      const modTag = p.parent_id ? `<span class="project-mod-badge">From ${escapeHtml(p.parent_id)}</span>` : "";
      
      let dateDisplay = "";
      if (p.updated_at || p.created_at) {
        try {
          const d = new Date(p.updated_at || p.created_at);
          dateDisplay = d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
        } catch (e) {
          dateDisplay = "";
        }
      }

      return `
        <div class="project-card-item ${isActive ? 'active' : ''}" data-id="${p.id}">
          <div class="project-card-top">
            <span class="project-id-tag">${p.id.toUpperCase()}</span>
            ${dateDisplay ? `<span class="project-date">${dateDisplay}</span>` : ''}
          </div>
          <div class="project-card-title" title="${escapeHtml(p.title || p.id)}">${escapeHtml(p.title || p.id)}</div>
          <div class="project-card-meta">
            <span class="project-file-badge">${fileCount} file${fileCount === 1 ? '' : 's'}</span>
            ${modTag}
          </div>
        </div>
      `;
    }).join("");

    projectsList.querySelectorAll(".project-card-item").forEach(card => {
      card.addEventListener("click", () => {
        const pid = card.getAttribute("data-id");
        if (pid) {
          loadProject(pid);
          openSplitView();
          switchTab("previewView");
        }
      });
    });
  }

  async function loadProject(projectId) {
    if (!projectId) {
      state.activeProjectId = null;
      if (headerActiveProjectBadge) {
        headerActiveProjectBadge.textContent = "";
        headerActiveProjectBadge.style.display = "none";
      }
      sandboxProjectBadge.style.display = "none";
      btnTriggerModifier.style.display = "none";
      previewIframe.src = "about:blank";
      state.projectFiles = {};
      renderCodeFileChips({});
      renderProjectsList();
      setModifierMode(false);
      promptInput.placeholder = "Describe a landing page or web app to build from scratch...";
      return;
    }

    state.activeProjectId = projectId;
    if (projectSelect) projectSelect.value = projectId;
    if (headerActiveProjectBadge) {
      headerActiveProjectBadge.textContent = projectId.toUpperCase();
      headerActiveProjectBadge.style.display = "inline-block";
    }
    renderProjectsList();

    sandboxProjectBadge.style.display = "flex";
    sandboxProjectBadge.querySelector("span").textContent = projectId;
    btnTriggerModifier.style.display = "inline-flex";
    setModifierMode(true);
    promptInput.placeholder = `Describe specific changes or additions for ${projectId} (updates existing project in-place)...`;

    try {
      const res = await fetch(`/api/projects/${projectId}`);
      if (!res.ok) return;
      const data = await res.json();
      state.projectFiles = data.files || {};
      
      // Update Review Status Action Bar
      if (reviewActionGroup) {
        reviewActionGroup.style.display = "flex";
        const metaStatus = (data.meta && data.meta.review_status) || "accepted";
        if (metaStatus === "staged") {
          stagedBadge.textContent = "Staged";
          stagedBadge.className = "staged-pill";
          btnLikeVersion.style.opacity = "1";
          btnDislikeVersion.style.opacity = "1";
        } else if (metaStatus === "accepted") {
          stagedBadge.textContent = "Accepted";
          stagedBadge.className = "staged-pill accepted";
          btnLikeVersion.style.opacity = "0.5";
          btnDislikeVersion.style.opacity = "0.5";
        } else if (metaStatus === "rejected") {
          stagedBadge.textContent = "Reverted";
          stagedBadge.className = "staged-pill rejected";
          btnLikeVersion.style.opacity = "0.5";
          btnDislikeVersion.style.opacity = "0.5";
        }
      }

      // Synchronize primary files to state code cache for immediate inspector access
      if (state.projectFiles["index.html"] && state.projectFiles["index.html"].content) {
        state.currentHtml = state.projectFiles["index.html"].content;
      }
      if (state.projectFiles["styles.css"] && state.projectFiles["styles.css"].content) {
        state.currentCss = state.projectFiles["styles.css"].content;
      }

      renderCodeFileChips(state.projectFiles);

      // Load preview from project index.html
      previewIframe.removeAttribute("srcdoc");
      previewIframe.src = `/api/projects/${projectId}/index.html?t=${Date.now()}`;
    } catch (err) {
      console.error("Error loading project:", err);
    }
  }

  function renderCodeFileChips(files) {
    if (!codeFilePicker) return;
    codeFilePicker.innerHTML = "";
    const fileNames = Object.keys(files);

    if (fileNames.length === 0) {
      codeFilePicker.innerHTML = `
        <button class="file-chip active" data-file="html">index.html</button>
        <button class="file-chip" data-file="css">styles.css</button>
      `;
      // Re-bind fallback listeners
      codeFilePicker.querySelectorAll(".file-chip").forEach(chip => {
        chip.addEventListener("click", () => {
          codeFilePicker.querySelectorAll(".file-chip").forEach(c => c.classList.remove("active"));
          chip.classList.add("active");
          updateCodeInspector();
        });
      });
      updateCodeInspector();
      return;
    }

    // Sort: index.html first, styles.css second, app.js third
    fileNames.sort((a, b) => {
      if (a === "index.html") return -1;
      if (b === "index.html") return 1;
      if (a === "styles.css") return -1;
      if (b === "styles.css") return 1;
      if (a === "app.js") return -1;
      if (b === "app.js") return 1;
      return a.localeCompare(b);
    });

    if (!files[state.activeProjectFile]) {
      state.activeProjectFile = fileNames[0];
    }

    fileNames.forEach(fn => {
      const btn = document.createElement("button");
      btn.className = `file-chip ${fn === state.activeProjectFile ? "active" : ""}`;
      btn.textContent = fn;
      btn.setAttribute("data-file", fn);
      btn.addEventListener("click", () => {
        state.activeProjectFile = fn;
        codeFilePicker.querySelectorAll(".file-chip").forEach(c => c.classList.remove("active"));
        btn.classList.add("active");
        displayProjectFile(fn);
      });
      codeFilePicker.appendChild(btn);
    });

    displayProjectFile(state.activeProjectFile);
  }

  function displayProjectFile(filename) {
    const finfo = state.projectFiles[filename];
    if (!finfo) {
      updateCodeInspector();
      return;
    }

    if (finfo.is_binary) {
      codeInspectorContent.textContent = `[Binary file: ${filename} (${finfo.size.toLocaleString()} bytes)]`;
      codeInspectorContent.className = "language-text";
    } else {
      codeInspectorContent.textContent = finfo.content || "";
      const ext = filename.split(".").pop().toLowerCase();
      let lang = ext;
      if (ext === "js") lang = "javascript";
      codeInspectorContent.className = `language-${lang}`;
    }

    if (window.hljs) {
      hljs.highlightElement(codeInspectorContent);
    }
  }

  function updateCodeInspector() {
    if (Object.keys(state.projectFiles).length > 0 && state.activeProjectFile) {
      displayProjectFile(state.activeProjectFile);
      return;
    }

    const activeChip = document.querySelector(".file-chip.active");
    const fileType = activeChip ? activeChip.getAttribute("data-file") : "html";

    if (fileType === "html") {
      codeInspectorContent.textContent = state.currentHtml || "<!-- No HTML code block detected in output -->";
      codeInspectorContent.className = "language-html";
    } else {
      codeInspectorContent.textContent = state.currentCss || "/* No CSS code block detected in output */";
      codeInspectorContent.className = "language-css";
    }

    if (window.hljs) {
      hljs.highlightElement(codeInspectorContent);
    }
  }

  btnCopyInspectedCode.addEventListener("click", () => {
    navigator.clipboard.writeText(codeInspectorContent.textContent);
    btnCopyInspectedCode.textContent = "✓ Copied";
    setTimeout(() => (btnCopyInspectedCode.textContent = "📋 Copy Code"), 2000);
  });

  btnCopyDoc.addEventListener("click", () => {
    navigator.clipboard.writeText(docProse.innerText);
    btnCopyDoc.textContent = "✓ Copied";
    setTimeout(() => (btnCopyDoc.textContent = "📋 Copy Text"), 2000);
  });

  // ==========================================================================
  // Typography & Reading Ergonomics
  // ==========================================================================

  if (btnFontDec) {
    btnFontDec.addEventListener("click", () => {
      state.fontScale = Math.max(0.8, state.fontScale - 0.1);
      applyFontScale();
    });
  }

  if (btnFontInc) {
    btnFontInc.addEventListener("click", () => {
      state.fontScale = Math.min(1.4, state.fontScale + 0.1);
      applyFontScale();
    });
  }

  function applyFontScale() {
    document.documentElement.style.setProperty("--font-scale", state.fontScale);
    if (fontLabel) fontLabel.textContent = `${Math.round(state.fontScale * 100)}%`;
  }

  if (widthButtons && widthButtons.length > 0) {
    widthButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        widthButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const width = btn.getAttribute("data-width");
        document.body.className = document.body.className.replace(/width-\w+/g, "") + ` width-${width}`;
      });
    });
  }

  // Search within content (if searchInput exists)
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      const query = searchInput.value.trim().toLowerCase();
      if (!query) {
        if (searchCount) searchCount.textContent = "";
        clearSearchHighlights();
        return;
      }

      let matches = 0;
      const bodyElements = document.querySelectorAll(".markdown-body p, .markdown-body li, .markdown-body h1, .markdown-body h2, .markdown-body h3");
      
      clearSearchHighlights();

      bodyElements.forEach(el => {
        const text = el.innerText;
        if (text.toLowerCase().includes(query)) {
          const regex = new RegExp(`(${escapeRegex(query)})`, "gi");
          el.innerHTML = el.innerHTML.replace(regex, `<mark class="search-highlight">$1</mark>`);
          matches++;
        }
      });

      if (searchCount) searchCount.textContent = matches > 0 ? `${matches} found` : "0";
    });
  }

  function clearSearchHighlights() {
    document.querySelectorAll("mark.search-highlight").forEach(m => {
      const parent = m.parentNode;
      parent.replaceChild(document.createTextNode(m.textContent), m);
      parent.normalize();
    });
  }

  // ==========================================================================
  // Fullscreen Code Inspection Modal
  // ==========================================================================

  function openCodeModal(title, code, lang) {
    codeModalTitle.textContent = title;
    codeModalContent.textContent = code;
    codeModalContent.className = `language-${lang}`;
    if (window.hljs) {
      hljs.highlightElement(codeModalContent);
    }
    codeModal.classList.add("active");
  }

  if (btnCloseCodeModal && codeModal) {
    btnCloseCodeModal.addEventListener("click", () => codeModal.classList.remove("active"));
  }
  if (btnCopyModalCode && codeModalContent) {
    btnCopyModalCode.addEventListener("click", () => {
      navigator.clipboard.writeText(codeModalContent.textContent);
      btnCopyModalCode.textContent = "✓ Copied";
      setTimeout(() => (btnCopyModalCode.textContent = "📋 Copy Code"), 2000);
    });
  }

  // ==========================================================================
  // Artifacts Drawer
  // ==========================================================================

  btnArtifacts.addEventListener("click", () => {
    fetchArtifacts();
    artifactsDrawer.classList.add("active");
    drawerOverlay.classList.add("active");
  });

  function closeDrawer() {
    artifactsDrawer.classList.remove("active");
    drawerOverlay.classList.remove("active");
  }

  btnCloseDrawer.addEventListener("click", closeDrawer);
  drawerOverlay.addEventListener("click", closeDrawer);

  async function fetchArtifacts() {
    try {
      const res = await fetch("/api/artifacts");
      if (!res.ok) return;
      const data = await res.json();
      artifactCountBadge.textContent = data.count || 0;

      if (data.artifacts && data.artifacts.length > 0) {
        drawerList.innerHTML = data.artifacts.map(f => {
          const dateStr = new Date(f.mtime * 1000).toLocaleTimeString();
          const sizeKb = (f.size / 1024).toFixed(1);
          return `
            <div class="artifact-chip" style="margin-bottom:6px;">
              <div>
                <strong class="art-name">${f.name}</strong>
                <div style="font-size:0.7rem;color:#64748b;">${sizeKb} KB • ${dateStr}</div>
              </div>
              <div class="art-actions">
                ${f.type === 'html' ? `<button class="tool-chip drawer-preview-btn" data-url="${f.url}">Preview</button>` : ''}
                <a href="${f.url}" download class="tool-chip">Download</a>
              </div>
            </div>
          `;
        }).join("");

        drawerList.querySelectorAll(".drawer-preview-btn").forEach(btn => {
          btn.addEventListener("click", () => {
            const url = btn.getAttribute("data-url");
            closeDrawer();
            openSplitView();
            switchTab("previewView");
            previewIframe.src = url;
          });
        });
      } else {
        drawerList.innerHTML = `<div style="text-align:center;color:#64748b;padding:2rem;">No saved artifacts yet.</div>`;
      }
    } catch (e) {
      console.error("Failed to fetch artifacts:", e);
    }
  }

  // ==========================================================================
  // Settings Modal & Config
  // ==========================================================================

  btnSettings.addEventListener("click", () => settingsModal.classList.add("active"));
  btnCloseSettings.addEventListener("click", () => settingsModal.classList.remove("active"));
  btnCancelSettings.addEventListener("click", () => settingsModal.classList.remove("active"));

  // Settings Tabs Switching
  if (tabSettingsStudio) {
    tabSettingsStudio.addEventListener("click", () => switchSettingsTab("panelSettingsStudio"));
  }
  if (tabSettingsChat) {
    tabSettingsChat.addEventListener("click", () => switchSettingsTab("panelSettingsChat"));
  }
  if (tabSettingsObservability) {
    tabSettingsObservability.addEventListener("click", () => switchSettingsTab("panelSettingsObservability"));
  }

  function switchSettingsTab(targetPanelId) {
    if (tabSettingsStudio) tabSettingsStudio.classList.toggle("active", targetPanelId === "panelSettingsStudio");
    if (tabSettingsChat) tabSettingsChat.classList.toggle("active", targetPanelId === "panelSettingsChat");
    if (tabSettingsObservability) tabSettingsObservability.classList.toggle("active", targetPanelId === "panelSettingsObservability");
    if (panelSettingsStudio) panelSettingsStudio.style.display = targetPanelId === "panelSettingsStudio" ? "block" : "none";
    if (panelSettingsChat) panelSettingsChat.style.display = targetPanelId === "panelSettingsChat" ? "block" : "none";
    if (panelSettingsObservability) panelSettingsObservability.style.display = targetPanelId === "panelSettingsObservability" ? "block" : "none";
  }

  function updateObservabilityUI(obs) {
    if (!obs) return;
    const isEn = Boolean(obs.enabled);
    if (cfgLangSmithEnabled) cfgLangSmithEnabled.checked = isEn;
    if (observabilityTabStatusPill) {
      observabilityTabStatusPill.textContent = isEn ? "ON" : "OFF";
      observabilityTabStatusPill.classList.toggle("active", isEn);
    }
    if (observabilityLiveStatus) {
      observabilityLiveStatus.textContent = isEn ? "ACTIVE" : (obs.available ? "DISABLED" : "NO SDK");
      observabilityLiveStatus.classList.toggle("active", isEn);
    }
    if (obs.masked_key && cfgLangSmithKeyHint) {
      cfgLangSmithKeyHint.textContent = `Configured key: ${obs.masked_key} (leave blank to keep)`;
    }
    if (obs.project && cfgLangSmithProject && !cfgLangSmithProject.value) {
      cfgLangSmithProject.value = obs.project;
    }
    if (obs.endpoint && cfgLangSmithEndpoint && !cfgLangSmithEndpoint.value) {
      cfgLangSmithEndpoint.value = obs.endpoint;
    }
    if (obs.agent_id && cfgLangSmithAgentId) {
      cfgLangSmithAgentId.value = obs.agent_id;
    }
    if (obs.agent_environment && cfgLangSmithAgentEnv) {
      cfgLangSmithAgentEnv.value = obs.agent_environment;
    }
    if (obs.dashboard_url && linkLangSmithDashboard) {
      linkLangSmithDashboard.href = obs.dashboard_url;
    }
  }

  if (btnToggleLangSmithKey && cfgLangSmithApiKey) {
    btnToggleLangSmithKey.addEventListener("click", () => {
      if (cfgLangSmithApiKey.type === "password") {
        cfgLangSmithApiKey.type = "text";
        btnToggleLangSmithKey.textContent = "🙈";
      } else {
        cfgLangSmithApiKey.type = "password";
        btnToggleLangSmithKey.textContent = "👁️";
      }
    });
  }

  // Open settings directly to Chat Pipeline from Composer Chat Pill
  if (btnComposerChatOnlyBadge) {
    btnComposerChatOnlyBadge.addEventListener("click", () => {
      switchSettingsTab("panelSettingsChat");
      settingsModal.classList.add("active");
    });
  }

  // Chat Only Mode Pill Toggle Switch Handler
  if (btnChatOnlyPillToggle) {
    btnChatOnlyPillToggle.addEventListener("click", () => {
      setChatOnlyMode(!state.chatOnlyMode);
    });
  }

  function setChatOnlyMode(enabled) {
    state.chatOnlyMode = enabled;
    if (btnChatOnlyPillToggle) {
      btnChatOnlyPillToggle.classList.toggle("active", enabled);
    }
    if (pillToggleLabel) {
      pillToggleLabel.innerHTML = enabled
        ? `<span class="pill-label-title">Chat Only</span><span class="pill-state-tag on">ON</span>`
        : `<span class="pill-label-title">Chat Only</span><span class="pill-state-tag off">OFF</span>`;
    }
    if (chatTabStatusPill) {
      chatTabStatusPill.textContent = enabled ? "ON" : "OFF";
      chatTabStatusPill.classList.toggle("active", enabled);
    }
    if (btnComposerChatOnlyBadge) {
      btnComposerChatOnlyBadge.style.display = enabled ? "inline-flex" : "none";
      if (composerChatPillText) {
        composerChatPillText.textContent = `💬 Chat Only (${state.chatOnlyModel.includes("3.1") ? "3.1 Lite" : "3.5 Lite"})`;
      }
    }
    if (chatControlsSubpanel) {
      chatControlsSubpanel.classList.toggle("disabled", !enabled);
    }

    // Update Send Button Label and placeholder
    if (enabled) {
      sendBtnLabel.textContent = "Chat";
      promptInput.placeholder = "Chat, ask questions, learn concepts, or generate HTML/CSS components...";
    } else {
      sendBtnLabel.textContent = state.isModifierMode ? "Modify & Upgrade" : "Generate";
      promptInput.placeholder = state.isModifierMode
        ? `Describe specific changes or additions for ${state.activeProjectId} (updates existing project in-place)...`
        : "Ask anything, attach designs/screenshots, or request complex multi-file apps... (Enter to send, Shift+Enter for new line)";
    }
  }

  // Chat-Only Model & Sliders
  if (cfgChatOnlyModel) {
    cfgChatOnlyModel.addEventListener("change", (e) => {
      state.chatOnlyModel = e.target.value;
      if (composerChatPillText) {
        composerChatPillText.textContent = `💬 Chat Only (${state.chatOnlyModel.includes("3.1") ? "3.1 Lite" : "3.5 Lite"})`;
      }
    });
  }

  if (cfgChatOnlyBudget) {
    cfgChatOnlyBudget.addEventListener("input", () => {
      const val = Number(cfgChatOnlyBudget.value);
      state.chatOnlyBudget = val;
      if (cfgChatBudgetValue) {
        cfgChatBudgetValue.textContent = val === 0 ? "0 (Instant)" : `${val.toLocaleString()} tokens`;
      }
    });
  }

  if (cfgChatOnlyTemp) {
    cfgChatOnlyTemp.addEventListener("input", () => {
      const val = Number(cfgChatOnlyTemp.value);
      state.chatOnlyTemp = val;
      if (cfgChatTempValue) {
        cfgChatTempValue.textContent = val.toFixed(2);
      }
    });
  }

  // Studio Sliders
  cfgBudget.addEventListener("input", () => {
    const val = Number(cfgBudget.value);
    cfgBudgetValue.textContent = val.toLocaleString();
    state.thinkingBudget = val;
    if (budgetDisplay) budgetDisplay.textContent = `${val.toLocaleString()} tokens`;
  });

  cfgTemp.addEventListener("input", () => {
    const val = Number(cfgTemp.value);
    cfgTempValue.textContent = val.toFixed(2);
    state.temperature = val;
  });

  if (btnResetSettings) {
    btnResetSettings.addEventListener("click", async () => {
      // 1. Reset Studio inputs to defaults
      if (cfgComplexModel) cfgComplexModel.value = "gemini-4-hydrogen";
      if (headerComplexModelSelect) headerComplexModelSelect.value = "gemini-4-hydrogen";
      if (cfgLiteModel) cfgLiteModel.value = "gemini-3.5-flash-lite";
      if (headerLiteModelSelect) headerLiteModelSelect.value = "gemini-3.5-flash-lite";

      cfgBudget.value = 1024;
      cfgBudgetValue.textContent = "1,024";
      cfgTemp.value = 0.7;
      cfgTempValue.textContent = "0.70";

      // 2. Reset Chat-Only inputs to defaults
      if (cfgChatOnlyModel) cfgChatOnlyModel.value = "gemini-3.5-flash-lite";
      if (cfgChatOnlyBudget) cfgChatOnlyBudget.value = 0;
      if (cfgChatBudgetValue) cfgChatBudgetValue.textContent = "0 (Instant)";
      if (cfgChatOnlyTemp) cfgChatOnlyTemp.value = 0.70;
      if (cfgChatTempValue) cfgChatTempValue.textContent = "0.70";
      setChatOnlyMode(false);

      // 3. Update Live State
      state.complexModel = "gemini-3.7-flash";
      state.liteModel = "gemini-3.1-flash-lite";
      state.thinkingBudget = 2048;
      state.temperature = 1.0;
      state.chatOnlyMode = false;
      state.chatOnlyModel = "gemini-3.1-flash-lite";
      state.chatOnlyBudget = 0;
      state.chatOnlyTemp = 0.70;
      if (budgetDisplay) budgetDisplay.textContent = "2,048 tokens";

      // 4. Persist defaults to backend
      try {
        await fetch("/api/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            thinking_budget: 1024,
            temperature: 0.7,
            complex_model: "gemini-3.6-flash",
            lite_model: "gemini-3.1-flash-lite",
            chat_only: false,
            chat_model: "gemini-3.1-flash-lite",
            chat_temperature: 0.70,
            chat_budget: 0
          })
        });
        showToast("✓ Reset to default temperature, budget, and model controls");
      } catch (err) {
        console.error("Error saving reset settings:", err);
      }
    });
  }

  btnSaveSettings.addEventListener("click", async () => {
    state.thinkingBudget = Number(cfgBudget.value);
    state.temperature = Number(cfgTemp.value);
    if (cfgComplexModel) state.complexModel = cfgComplexModel.value;
    if (cfgLiteModel) state.liteModel = cfgLiteModel.value;
    if (cfgChatOnlyModel) state.chatOnlyModel = cfgChatOnlyModel.value;
    if (cfgChatOnlyBudget) state.chatOnlyBudget = Number(cfgChatOnlyBudget.value);
    if (cfgChatOnlyTemp) state.chatOnlyTemp = Number(cfgChatOnlyTemp.value);
    if (budgetDisplay) budgetDisplay.textContent = `${state.thinkingBudget.toLocaleString()} tokens`;

    try {
      await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thinking_budget: state.thinkingBudget,
          temperature: state.temperature,
          complex_model: state.complexModel,
          lite_model: state.liteModel,
          chat_only: state.chatOnlyMode,
          chat_model: state.chatOnlyModel,
          chat_temperature: state.chatOnlyTemp,
          chat_budget: state.chatOnlyBudget
        })
      });

      // Save LangSmith Observability Config
      try {
        const lsEnabled = cfgLangSmithEnabled ? cfgLangSmithEnabled.checked : false;
        const lsKey = cfgLangSmithApiKey ? cfgLangSmithApiKey.value.trim() : "";
        const lsProj = cfgLangSmithProject ? cfgLangSmithProject.value.trim() : "";
        const lsEndpoint = cfgLangSmithEndpoint ? cfgLangSmithEndpoint.value.trim() : "";
        const lsAgentId = cfgLangSmithAgentId ? cfgLangSmithAgentId.value.trim() : "";
        const lsAgentEnv = cfgLangSmithAgentEnv ? cfgLangSmithAgentEnv.value.trim() : "";
        const obsRes = await fetch("/api/observability/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            enabled: lsEnabled,
            api_key: lsKey || undefined,
            project: lsProj || undefined,
            endpoint: lsEndpoint || undefined,
            agent_id: lsAgentId || undefined,
            agent_environment: lsAgentEnv || undefined
          })
        });
        if (obsRes.ok) {
          const obsData = await obsRes.json();
          if (obsData.config) {
            updateObservabilityUI(obsData.config);
          }
        }
      } catch (err) {
        console.error("Observability config update error:", err);
      }

      showToast("✓ Settings updated & applied live");
    } catch (e) {
      console.error(e);
    }

    settingsModal.classList.remove("active");
  });

  // ==========================================================================
  // Gemini API Key Modal & Key Persistence Handlers
  // ==========================================================================

  if (btnApiKey) {
    btnApiKey.addEventListener("click", () => {
      openApiKeyModal();
    });
  }

  if (btnCloseApiKeyModal) {
    btnCloseApiKeyModal.addEventListener("click", closeApiKeyModal);
  }

  if (btnCancelApiKey) {
    btnCancelApiKey.addEventListener("click", closeApiKeyModal);
  }

  if (btnToggleKeyVis) {
    btnToggleKeyVis.addEventListener("click", () => {
      if (apiKeyInput.type === "password") {
        apiKeyInput.type = "text";
        btnToggleKeyVis.textContent = "🙈";
      } else {
        apiKeyInput.type = "password";
        btnToggleKeyVis.textContent = "👁️";
      }
    });
  }

  if (btnPasteClipboardKey) {
    btnPasteClipboardKey.addEventListener("click", async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text) {
          apiKeyInput.value = text.trim();
          btnPasteClipboardKey.textContent = "✓ Pasted";
          setTimeout(() => (btnPasteClipboardKey.textContent = "📋 Paste"), 1500);
        }
      } catch (err) {
        console.warn("Clipboard access denied or unavailable:", err);
      }
    });
  }

  function updateApiKeyUI(data) {
    if (!data) return;
    if (data.has_key) {
      if (activeKeyDisplay) activeKeyDisplay.textContent = data.masked_key || "Configured";
      if (keyBadgeText) keyBadgeText.textContent = "✓ Active";
      if (keyStatusIndicator) keyStatusIndicator.classList.remove("missing");
    } else {
      if (activeKeyDisplay) activeKeyDisplay.textContent = "No key configured";
      if (keyBadgeText) keyBadgeText.textContent = "Missing";
      if (keyStatusIndicator) keyStatusIndicator.classList.add("missing");
    }

    if (keySourceBadge) {
      if (data.source === "user") {
        keySourceBadge.textContent = "User Key (High Priority)";
        keySourceBadge.style.background = "rgba(16, 185, 129, 0.15)";
        keySourceBadge.style.color = "#34d399";
        keySourceBadge.style.borderColor = "rgba(52, 211, 153, 0.3)";
      } else {
        keySourceBadge.textContent = "Default .env Key";
        keySourceBadge.style.background = "rgba(99, 102, 241, 0.15)";
        keySourceBadge.style.color = "#818cf8";
        keySourceBadge.style.borderColor = "rgba(129, 140, 248, 0.3)";
      }
    }

    if (btnResetApiKey) {
      // Show reset button only if a custom user key is currently active
      btnResetApiKey.style.display = data.is_custom ? "inline-flex" : "none";
    }
  }

  function showToast(message) {
    const note = document.createElement("div");
    note.className = "toast-notification";
    note.textContent = message;
    document.body.appendChild(note);
    setTimeout(() => note.remove(), 3500);
  }

  if (btnSaveApiKey) {
    btnSaveApiKey.addEventListener("click", async () => {
      const newKey = apiKeyInput.value.trim();
      if (!newKey) {
        alert("Please paste or type a valid Gemini API key.");
        apiKeyInput.focus();
        return;
      }

      btnSaveApiKey.disabled = true;
      btnSaveApiKey.innerHTML = `<span>Saving...</span>`;

      try {
        const res = await fetch("/api/key/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: newKey })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Failed to set user API key");
        }

        updateApiKeyUI(data);
        apiKeyInput.value = "";
        closeApiKeyModal();

        showToast("✓ Custom Gemini API Key activated (takes priority over .env default)");
      } catch (err) {
        alert(`Error saving API key: ${err.message}`);
      } finally {
        btnSaveApiKey.disabled = false;
        btnSaveApiKey.innerHTML = `<span>Save & Apply Key</span>`;
      }
    });
  }

  if (btnResetApiKey) {
    btnResetApiKey.addEventListener("click", async () => {
      if (!confirm("Revert to the default GEMINI_API_KEY from .env?")) return;
      btnResetApiKey.disabled = true;
      try {
        const res = await fetch("/api/key/reset", { method: "POST" });
        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail || "Failed to reset key");
        }
        updateApiKeyUI(data);
        showToast("✓ User key cleared. Reverted to .env default key.");
        closeApiKeyModal();
      } catch (err) {
        alert(`Error resetting key: ${err.message}`);
      } finally {
        btnResetApiKey.disabled = false;
      }
    });
  }

  async function openApiKeyModal() {
    if (!apiKeyModal) return;
    apiKeyModal.style.display = "flex";
    apiKeyModal.classList.add("active");
    if (apiKeyInput) {
      apiKeyInput.value = "";
      apiKeyInput.focus();
    }
    // Refresh status
    try {
      const res = await fetch("/api/key/status");
      if (res.ok) {
        const data = await res.json();
        updateApiKeyUI(data);
      }
    } catch (e) {
      console.error(e);
    }
  }

  function closeApiKeyModal() {
    if (!apiKeyModal) return;
    apiKeyModal.style.display = "none";
    apiKeyModal.classList.remove("active");
  }

  async function fetchInitialState() {
    try {
      const res = await fetch("/api/state");
      if (res.ok) {
        const data = await res.json();
        state.thinkingBudget = data.thinking_budget !== undefined ? data.thinking_budget : 1024;
        state.temperature = data.temperature !== undefined ? data.temperature : 0.7;

        if (data.complex_model) {
          state.complexModel = data.complex_model;
          if (headerComplexModelSelect) headerComplexModelSelect.value = data.complex_model;
          if (cfgComplexModel) cfgComplexModel.value = data.complex_model;
        }

        if (data.lite_model) {
          state.liteModel = data.lite_model;
          if (headerLiteModelSelect) headerLiteModelSelect.value = data.lite_model;
          if (cfgLiteModel) cfgLiteModel.value = data.lite_model;
        }

        // Manage welcome screen vs chat feed
        if (data.history_count && data.history_count > 0) {
          await loadChatHistory();
        } else {
          if (welcomeScreen) welcomeScreen.style.display = "flex";
          if (chatFeed) {
            chatFeed.innerHTML = "";
            chatFeed.style.display = "none";
          }
        }

        // Key Status & Source
        updateApiKeyUI(data);

        if (data.chat_model) {
          state.chatOnlyModel = data.chat_model;
          if (cfgChatOnlyModel) cfgChatOnlyModel.value = data.chat_model;
        }
        if (data.chat_budget !== undefined) {
          state.chatOnlyBudget = Number(data.chat_budget);
          if (cfgChatOnlyBudget) cfgChatOnlyBudget.value = state.chatOnlyBudget;
          if (cfgChatBudgetValue) cfgChatBudgetValue.textContent = state.chatOnlyBudget === 0 ? "0 (Instant)" : `${state.chatOnlyBudget.toLocaleString()} tokens`;
        }
        if (data.chat_temperature !== undefined) {
          state.chatOnlyTemp = Number(data.chat_temperature);
          if (cfgChatOnlyTemp) cfgChatOnlyTemp.value = state.chatOnlyTemp;
          if (cfgChatTempValue) cfgChatTempValue.textContent = state.chatOnlyTemp.toFixed(2);
        }
        if (data.chat_only !== undefined) {
          setChatOnlyMode(Boolean(data.chat_only));
        }

        budgetDisplay.textContent = `${state.thinkingBudget.toLocaleString()} tokens`;
        cfgBudget.value = state.thinkingBudget;
        cfgBudgetValue.textContent = state.thinkingBudget.toLocaleString();
        cfgTemp.value = state.temperature;
        cfgTempValue.textContent = Number(state.temperature).toFixed(2);
        drawerDirPath.textContent = data.output_dir || "output/";

        // LangSmith Observability config
        if (data.observability) {
          updateObservabilityUI(data.observability);
        }
      }
    } catch (e) {
      console.error("Failed to load initial state:", e);
    }
  }

  async function loadChatHistory() {
    try {
      const res = await fetch("/api/history");
      if (!res.ok) return;
      const data = await res.json();
      const messages = data.messages || [];
      if (messages.length > 0) {
        if (welcomeScreen) welcomeScreen.style.display = "none";
        if (chatFeed) {
          chatFeed.innerHTML = "";
          chatFeed.style.display = "flex";
          messages.forEach(msg => {
            if (msg.role === "user") {
              appendUserMessage(msg.content);
            } else {
              const modelMsgEl = createModelMessageElement();
              chatFeed.appendChild(modelMsgEl);
              const contentBodyEl = modelMsgEl.querySelector(".message-body-content");
              const thoughtBodyEl = modelMsgEl.querySelector(".thought-body");
              const thoughtWordCountEl = modelMsgEl.querySelector(".thought-word-count");
              const thoughtAccordionEl = modelMsgEl.querySelector(".thought-accordion");
              const statusDotEl = modelMsgEl.querySelector(".status-dot");
              if (statusDotEl) statusDotEl.classList.remove("pulse");

              if (msg.model) {
                const modelBadgeTitle = modelMsgEl.querySelector(".model-badge-info h3");
                if (modelBadgeTitle) modelBadgeTitle.textContent = formatModelName(msg.model);
              }
              if (msg.thinking_budget !== undefined || msg.temperature !== undefined) {
                const budgetBadgeEl = modelMsgEl.querySelector(".budget-badge");
                if (budgetBadgeEl) {
                  const bVal = msg.thinking_budget !== undefined ? msg.thinking_budget : state.thinkingBudget;
                  const tVal = msg.temperature !== undefined ? msg.temperature : state.temperature;
                  budgetBadgeEl.textContent = `${Number(bVal).toLocaleString()} tok | T=${Number(tVal).toFixed(2)}`;
                }
              }

              renderMarkdownToElement(contentBodyEl, msg.content || "");
              decorateCodeBlocks(contentBodyEl);

              if (msg.thought) {
                thoughtAccordionEl.style.display = "block";
                thoughtBodyEl.textContent = msg.thought;
                const words = msg.thought.split(/\s+/).filter(Boolean).length;
                thoughtWordCountEl.textContent = `${words.toLocaleString()} words of deep reasoning`;
              }
            }
          });
          // Populate Reader Desk with latest model output from history
          const modelMsgs = messages.filter(m => m.role === "model");
          if (modelMsgs.length > 0) {
            const latestModel = modelMsgs[modelMsgs.length - 1];
            state.currentRawText = latestModel.content || "";
            updateReaderDesk(latestModel.content || "", latestModel.thought || "");
          }

          chatFeed.scrollTop = chatFeed.scrollHeight;
        }
      } else {
        if (welcomeScreen) welcomeScreen.style.display = "flex";
        if (chatFeed) {
          chatFeed.innerHTML = "";
          chatFeed.style.display = "none";
        }
      }
    } catch (e) {
      console.error("Failed to load chat history:", e);
      if (welcomeScreen) welcomeScreen.style.display = "flex";
      if (chatFeed) chatFeed.style.display = "none";
    }
  }

  // Helpers
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function escapeRegex(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }
});
