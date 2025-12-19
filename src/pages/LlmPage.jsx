import React, { useEffect, useRef, useState } from "react";

const API_BASE = "";

const LlmPage = () => {
  const [status, setStatus] = useState("Ready to start");
  const [messages, setMessages] = useState([]);
  const [toolCalls, setToolCalls] = useState([]);
  const [dataPreview, setDataPreview] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isConfigured, setIsConfigured] = useState(false);
  const [hasData, setHasData] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const eventSourceRef = useRef(null);
  const messagesEndRef = useRef(null);
  const toolCallsEndRef = useRef(null);
  const fileInputRef = useRef(null);

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
    } catch (err) {
      setUploadStatus(`Error: ${err.message}`);
      setHasData(false);
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
    setDataPreview([]);
    setStatus("Connecting to cleaning agent...");
    setIsRunning(true);

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
            onClick={() => fileInputRef.current?.click()}
            disabled={!isConfigured || isRunning}
          >
            📁 Upload CSV
          </button>
          <button
            className="primary-button"
            onClick={startCleaning}
            disabled={isRunning || !isConfigured || !hasData}
          >
            {isRunning ? "Running..." : "Start Agent"}
          </button>
        </div>
      </div>

      {uploadStatus && (
        <div
          className={`upload-status ${
            uploadStatus.startsWith("✓")
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
                <p>No data to preview yet. Start the agent to see results.</p>
              </div>
            )}
          </div>
        </section>

        {/* Sidebar */}
        <aside className="llm-sidebar">
          <div className="sidebar-section">
            <div className="sidebar-header">
              <span className="sidebar-icon">💬</span>
              <h3>Agent Messages</h3>
              <span className="badge">{messages.length}</span>
            </div>
            <div className="sidebar-content messages-content">
              {messages.length > 0 ? (
                <>
                  {messages.map((m, i) => (
                    <div key={i} className="message-item">
                      <div className="message-header">
                        <span className="message-icon">🤖</span>
                        <span className="message-time">
                          {new Date().toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="message-text">{m}</div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </>
              ) : (
                <div className="empty-sidebar">
                  <p>Agent messages will appear here</p>
                </div>
              )}
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-header">
              <span className="sidebar-icon">🔧</span>
              <h3>Tool Calls</h3>
              <span className="badge">{toolCalls.length}</span>
            </div>
            <div className="sidebar-content tools-content">
              {toolCalls.length > 0 ? (
                <>
                  {toolCalls.map((call, i) => (
                    <div key={i} className="tool-item">
                      <div className="tool-header">
                        <span className="tool-name">{call.tool}</span>
                        <span className="tool-badge">Call #{i + 1}</span>
                      </div>
                      <div className="tool-params">
                        <pre>{JSON.stringify(call.params, null, 2)}</pre>
                      </div>
                    </div>
                  ))}
                  <div ref={toolCallsEndRef} />
                </>
              ) : (
                <div className="empty-sidebar">
                  <p>Tool executions will appear here</p>
                </div>
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default LlmPage;
