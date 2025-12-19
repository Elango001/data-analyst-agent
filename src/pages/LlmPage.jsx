import React, { useEffect, useRef, useState } from "react";

const API_BASE = "";

const MODEL_OPTIONS = {
  google: [
    { value: "gemini-2.0-flash-exp", label: "Gemini 2.0 Flash (Experimental)" },
    { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
    { value: "gemini-1.5-flash-8b", label: "Gemini 1.5 Flash-8B" },
    { value: "gemini-1.5-pro", label: "Gemini 1.5 Pro" },
    { value: "gemini-1.0-pro", label: "Gemini 1.0 Pro" },
  ],
};

const LlmPage = () => {
  const [status, setStatus] = useState("Ready to start");
  const [messages, setMessages] = useState([]);
  const [toolCalls, setToolCalls] = useState([]);
  const [dataPreview, setDataPreview] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  const [hasData, setHasData] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [configType, setConfigType] = useState(null); // 'model' or 'database'
  const [configStatus, setConfigStatus] = useState("");
  const [showAgentDropdown, setShowAgentDropdown] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);

  // Model config state
  const [provider, setProvider] = useState("google");
  const [modelName, setModelName] = useState("gemini-2.0-flash-exp");
  const [apiKey, setApiKey] = useState("");

  // Database config state
  const [db, setDb] = useState({
    host: "localhost",
    database: "preprocessing_logs",
    user: "postgres",
    password: "",
    port: 5432,
    csv_path: "deleted_data.csv",
  });

  const eventSourceRef = useRef(null);
  const messagesEndRef = useRef(null);
  const toolCallsEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const chatInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    toolCallsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, toolCalls]);

  // Check configuration status on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setIsConfigured(data.configured);
      if (!data.configured) {
        setStatus("⚠️ Please configure the system first in Configuration page");
      }
    } catch (err) {
      console.error("Health check failed:", err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!isConfigured) {
      setUploadStatus("⚠️ Please configure the system first");
      return;
    }

    setUploadStatus("Uploading...");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setHasData(true);
      setUploadStatus(`✓ Uploaded: ${data.rows} rows, ${data.columns} columns`);
      setStatus("Ready to start cleaning");

      // Display preview if available
      if (data.preview && data.preview.length > 0) {
        setDataPreview(data.preview);
      }
    } catch (err) {
      setUploadStatus(`Error: ${err.message}`);
      setHasData(false);
    }
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    // TODO: Backend integration for user queries
    console.log("User query:", chatInput);

    // Clear input
    setChatInput("");
  };

  const openConfigModal = (type) => {
    setConfigType(type);
    setShowConfigModal(true);
    setConfigStatus("");
  };

  const closeConfigModal = () => {
    setShowConfigModal(false);
    setConfigType(null);
    setConfigStatus("");
  };

  const handleConfigureLLM = async (e) => {
    e.preventDefault();
    setConfigStatus("Configuring LLM...");
    try {
      const res = await fetch(`${API_BASE}/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider,
          model_name: modelName,
          api_key: apiKey,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to configure LLM");
      setConfigStatus(`✓ ${data.message}`);
      setIsConfigured(true);
      setTimeout(() => closeConfigModal(), 1500);
      checkHealth();
    } catch (err) {
      setConfigStatus(`Error: ${err.message}`);
    }
  };

  const handleConfigureDb = async (e) => {
    e.preventDefault();
    setConfigStatus("Configuring database...");
    try {
      const res = await fetch(`${API_BASE}/configure-db`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...db, type: "postgresql" }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to configure DB");
      setConfigStatus(`✓ ${data.message}`);
      setTimeout(() => closeConfigModal(), 1500);
    } catch (err) {
      setConfigStatus(`Error: ${err.message}`);
    }
  };

  const startCleaning = () => {
    if (!isConfigured) {
      setStatus("⚠️ Please configure the system first");
      return;
    }

    if (!hasData) {
      setStatus("⚠️ Please upload a CSV file first");
      return;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setMessages([]);
    setToolCalls([]);
    // Don't clear data preview to avoid black screen
    setStatus("Connecting to cleaning agent...");
    setIsRunning(true);
    // Open sidebar automatically when starting agent
    setIsSidebarOpen(true);
    setIsSidebarOpen(true);

    const es = new EventSource(`${API_BASE}/clean`);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.node === "cleaner_node") {
          if (payload.last_message) {
            setMessages((prev) => [...prev, payload.last_message]);
          }
          if (payload.tool_call) {
            setToolCalls((prev) => [...prev, ...payload.tool_call]);
          }
          if (payload.summary?.data_preview) {
            setDataPreview(payload.summary.data_preview);
          }
          setStatus("Agent is processing...");
        }
      } catch (e) {
        console.error("Bad SSE payload", e);
        setStatus("Error processing agent response");
      }
    };

    es.onerror = (error) => {
      console.error("EventSource error:", error);
      setStatus("Cleaning completed");
      setIsRunning(false);
      es.close();
      eventSourceRef.current = null;
    };
  };

  const runAgent = (agentType) => {
    setShowAgentDropdown(false);

    if (!isConfigured) {
      setStatus("⚠️ Please configure the system first");
      return;
    }

    if (!hasData) {
      setStatus("⚠️ Please upload a CSV file first");
      return;
    }

    // For now, only cleaner agent and full pipeline work
    if (agentType === 'cleaner' || agentType === 'full') {
      startCleaning();
    } else {
      setStatus(`⚠️ ${agentType} agent coming soon...`);
      // Placeholder for future implementation
      console.log(`Running ${agentType} agent...`);
    }
  };

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="page llm-page">
      <div className="llm-header">
        <div className="llm-header-content">
          <h2>AI Agent Interface</h2>
          <p className="llm-subtitle">
            Interact with data cleaning and analysis agents
          </p>
        </div>
        <div className="header-actions">
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            style={{ display: "none" }}
          />
          <button
            className="secondary-button"
            onClick={() => setShowConfigModal(!showConfigModal)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ marginRight: '6px' }}>
              <circle cx="12" cy="12" r="3" />
              <path d="M12 1v6m0 6v6m6-12l-3 5.2m0 5.6l3 5.2M6 1l3 5.2m0 5.6L6 17" />
            </svg>
            Configure
          </button>
          <button
            className="secondary-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={!isConfigured || isRunning}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ marginRight: '6px' }}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            Upload CSV
          </button>
          <div className="agent-dropdown-container">
            <button
              className="primary-button"
              onClick={() => setShowAgentDropdown(!showAgentDropdown)}
              disabled={isRunning || !isConfigured || !hasData}
            >
              {isRunning ? (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }} className="spinning-icon">
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </svg>
                  Running...
                </>
              ) : (
                <>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
                    <circle cx="12" cy="12" r="10" />
                    <polygon points="10 8 16 12 10 16 10 8" fill="currentColor" />
                  </svg>
                  Start Agent
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginLeft: '6px' }}>
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </>
              )}
            </button>
            {showAgentDropdown && !isRunning && (
              <div className="agent-dropdown">
                <div className="agent-option" onClick={() => runAgent('cleaner')}>
                  <div className="agent-option-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                    </svg>
                  </div>
                  <div className="agent-option-content">
                    <h4>Cleaner Agent</h4>
                    <p>Clean and preprocess your data</p>
                  </div>
                  <button className="agent-run-btn" onClick={(e) => { e.stopPropagation(); runAgent('cleaner'); }}>
                    Run Now
                  </button>
                </div>
                <div className="agent-option" onClick={() => runAgent('analyser')}>
                  <div className="agent-option-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="12" y1="20" x2="12" y2="10" />
                      <line x1="18" y1="20" x2="18" y2="4" />
                      <line x1="6" y1="20" x2="6" y2="16" />
                    </svg>
                  </div>
                  <div className="agent-option-content">
                    <h4>Analyser Agent</h4>
                    <p>Analyze patterns and insights</p>
                  </div>
                  <button className="agent-run-btn" onClick={(e) => { e.stopPropagation(); runAgent('analyser'); }}>
                    Run Now
                  </button>
                </div>
                <div className="agent-option" onClick={() => runAgent('visualizer')}>
                  <div className="agent-option-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                    </svg>
                  </div>
                  <div className="agent-option-content">
                    <h4>Visualizer Agent</h4>
                    <p>Create charts and visualizations</p>
                  </div>
                  <button className="agent-run-btn" onClick={(e) => { e.stopPropagation(); runAgent('visualizer'); }}>
                    Run Now
                  </button>
                </div>
                <div className="agent-option" onClick={() => runAgent('full')}>
                  <div className="agent-option-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="12" cy="12" r="3" />
                      <path d="M12 1v6m0 6v6" />
                      <path d="m4.2 4.2 4.2 4.2m5.6 5.6 4.2 4.2" />
                      <path d="M1 12h6m6 0h6" />
                      <path d="m4.2 19.8 4.2-4.2m5.6-5.6 4.2-4.2" />
                    </svg>
                  </div>
                  <div className="agent-option-content">
                    <h4>Full Pipeline</h4>
                    <p>Run all agents sequentially</p>
                  </div>
                  <button className="agent-run-btn" onClick={(e) => { e.stopPropagation(); runAgent('full'); }}>
                    Run Now
                  </button>
                </div>
              </div>
            )}
          </div>
          <button
            className="secondary-button"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ marginRight: '6px' }}>
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Chat
          </button>
        </div>
      </div>

      {uploadStatus && (
        <div
          className={`upload-status ${uploadStatus.startsWith("✓")
            ? "success"
            : uploadStatus.startsWith("⚠️") ||
              uploadStatus.startsWith("Error")
              ? "warning"
              : ""
            }`}
        >
          {uploadStatus}
        </div>
      )}

      <div className="llm-layout">
        {/* Main Content Area */}
        <section className="llm-main">
          <div className="llm-status-bar">
            <span
              className={`status-indicator ${isRunning ? "active" : ""}`}
            ></span>
            {status}
          </div>

          <div className="data-preview-section">
            <h3>Data Preview</h3>
            {dataPreview.length > 0 ? (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      {dataPreview[0] &&
                        Object.keys(dataPreview[0]).map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                    </tr>
                  </thead>
                  <tbody>
                    {dataPreview.slice(0, 20).map((row, idx) => (
                      <tr key={idx}>
                        {Object.keys(row).map((col) => (
                          <td key={col}>{String(row[col])}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="empty-state">
                <p>{isRunning ? "Processing data..." : "No data to preview yet. Start the agent to see results."}</p>
              </div>
            )}
          </div>
        </section>

        {/* Sidebar - VS Code Copilot Style */}
        <aside className={`copilot-sidebar ${isSidebarOpen ? 'open' : 'collapsed'}`}>
          <button
            className="sidebar-toggle-btn"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {isSidebarOpen ? (
                <path d="M9 18l6-6-6-6" />
              ) : (
                <path d="M15 18l-6-6 6-6" />
              )}
            </svg>
          </button>

          <div className="copilot-header">
            <div className="copilot-badge">{messages.length + toolCalls.length}</div>
          </div>

          <div className="copilot-messages">
            {messages.length === 0 && toolCalls.length === 0 ? (
              <div className="copilot-empty">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                </svg>
                <h4>Welcome to Agent Chat</h4>
                <p>Upload a dataset and start the agent, or ask me anything about your data analysis.</p>
              </div>
            ) : (
              <>
                {messages.map((msg, i) => (
                  <React.Fragment key={`msg-${i}`}>
                    <div className="copilot-message agent-message">
                      <div className="message-avatar agent-avatar">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                        </svg>
                      </div>
                      <div className="message-bubble">
                        <div className="message-role">Agent</div>
                        <div className="message-body">{msg}</div>
                      </div>
                    </div>

                    {toolCalls[i] && (
                      <div className="copilot-message tool-message" key={`tool-${i}`}>
                        <div className="message-avatar tool-avatar">
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                            <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                          </svg>
                        </div>
                        <div className="message-bubble tool-bubble">
                          <div className="message-role">🔧 {toolCalls[i].tool}</div>
                          <div className="tool-details">
                            <pre>{JSON.stringify(toolCalls[i].params, null, 2)}</pre>
                          </div>
                        </div>
                      </div>
                    )}
                  </React.Fragment>
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          <form className="copilot-input-container" onSubmit={handleSendMessage}>
            <div className="input-wrapper">
              <textarea
                ref={chatInputRef}
                className="copilot-input"
                placeholder="Ask about your data..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage(e);
                  }
                }}
                rows={1}
                disabled={!isConfigured}
              />
              <button
                type="submit"
                className="send-button"
                disabled={!chatInput.trim() || !isConfigured}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                  <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                </svg>
              </button>
            </div>
            <div className="input-hint">
              Press Enter to send, Shift+Enter for new line
            </div>
          </form>
        </aside>
      </div>

      {/* Configuration Modal */}
      {showConfigModal && (
        <div className="modal-overlay" onClick={closeConfigModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {!configType ? (
              <>
                <div className="modal-header">
                  <h3>Configuration Options</h3>
                  <button className="modal-close" onClick={closeConfigModal}>×</button>
                </div>
                <div className="modal-body">
                  <p className="modal-description">Choose what you want to configure:</p>
                  <div className="config-options">
                    <button
                      className="config-option-card"
                      onClick={() => openConfigModal('model')}
                    >
                      <div className="option-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="3" y="3" width="7" height="7" />
                          <rect x="14" y="3" width="7" height="7" />
                          <rect x="14" y="14" width="7" height="7" />
                          <rect x="3" y="14" width="7" height="7" />
                        </svg>
                      </div>
                      <h4>Model Configuration</h4>
                      <p>Configure LLM provider and API settings</p>
                    </button>
                    <button
                      className="config-option-card"
                      onClick={() => openConfigModal('database')}
                    >
                      <div className="option-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <ellipse cx="12" cy="5" rx="9" ry="3" />
                          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                        </svg>
                      </div>
                      <h4>Database Configuration</h4>
                      <p>Configure database connection settings</p>
                    </button>
                  </div>
                </div>
              </>
            ) : configType === 'model' ? (
              <>
                <div className="modal-header">
                  <h3>Model Configuration</h3>
                  <button className="modal-close" onClick={closeConfigModal}>×</button>
                </div>
                <form onSubmit={handleConfigureLLM} className="modal-body">
                  <div className="form-group">
                    <label htmlFor="modal-provider">Provider</label>
                    <select
                      id="modal-provider"
                      className="form-select"
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                    >
                      <option value="google">Google Gemini</option>
                    </select>
                    <small className="form-hint">Only Google Gemini is currently supported</small>
                  </div>

                  <div className="form-group">
                    <label htmlFor="modal-model">Model</label>
                    <select
                      id="modal-model"
                      className="form-select"
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                    >
                      {MODEL_OPTIONS[provider]?.map((model) => (
                        <option key={model.value} value={model.value}>
                          {model.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="modal-apiKey">API Key</label>
                    <input
                      id="modal-apiKey"
                      type="password"
                      className="form-input"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Enter your API key"
                      required
                    />
                  </div>

                  {configStatus && (
                    <div className={`config-status ${configStatus.includes('✓') ? 'success' : configStatus.includes('⚠️') || configStatus.includes('Error') ? 'error' : ''}`}>
                      {configStatus}
                    </div>
                  )}

                  <div className="modal-actions">
                    <button type="button" className="secondary-button" onClick={closeConfigModal}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ marginRight: '6px' }}>
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                      Cancel
                    </button>
                    <button type="submit" className="primary-button">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" style={{ marginRight: '6px' }}>
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      Save Configuration
                    </button>
                  </div>
                </form>
              </>
            ) : (
              <>
                <div className="modal-header">
                  <h3>Database Configuration</h3>
                  <button className="modal-close" onClick={closeConfigModal}>×</button>
                </div>
                <form onSubmit={handleConfigureDb} className="modal-body">
                  <div className="form-group">
                    <label htmlFor="modal-dbType">Database Type</label>
                    <select
                      id="modal-dbType"
                      className="form-select"
                      value="postgresql"
                      disabled
                    >
                      <option value="postgresql">PostgreSQL</option>
                    </select>
                    <small className="form-hint">Only PostgreSQL is currently supported</small>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="modal-host">Host</label>
                      <input
                        id="modal-host"
                        className="form-input"
                        value={db.host}
                        onChange={(e) => setDb({ ...db, host: e.target.value })}
                        required
                      />
                    </div>
                    <div className="form-group">
                      <label htmlFor="modal-port">Port</label>
                      <input
                        id="modal-port"
                        type="number"
                        className="form-input"
                        value={db.port}
                        onChange={(e) => setDb({ ...db, port: parseInt(e.target.value, 10) || 5432 })}
                        required
                      />
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="modal-database">Database Name</label>
                    <input
                      id="modal-database"
                      className="form-input"
                      value={db.database}
                      onChange={(e) => setDb({ ...db, database: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="modal-user">Username</label>
                    <input
                      id="modal-user"
                      className="form-input"
                      value={db.user}
                      onChange={(e) => setDb({ ...db, user: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="modal-password">Password</label>
                    <input
                      id="modal-password"
                      type="password"
                      className="form-input"
                      value={db.password}
                      onChange={(e) => setDb({ ...db, password: e.target.value })}
                      placeholder="Enter database password"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="modal-csvPath">CSV Path</label>
                    <input
                      id="modal-csvPath"
                      className="form-input"
                      value={db.csv_path}
                      onChange={(e) => setDb({ ...db, csv_path: e.target.value })}
                    />
                  </div>

                  {configStatus && (
                    <div className={`config-status ${configStatus.includes('✓') ? 'success' : configStatus.includes('⚠️') || configStatus.includes('Error') ? 'error' : ''}`}>
                      {configStatus}
                    </div>
                  )}

                  <div className="modal-actions">
                    <button type="button" className="secondary-button" onClick={closeConfigModal}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ marginRight: '6px' }}>
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                      Cancel
                    </button>
                    <button type="submit" className="primary-button">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" style={{ marginRight: '6px' }}>
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      Save Configuration
                    </button>
                  </div>
                </form>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LlmPage;
