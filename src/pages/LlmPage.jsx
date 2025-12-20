import React, { useEffect, useRef, useState } from "react";

const API_BASE = "http://localhost:8000";

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

  // Load conversation from sessionStorage
  const [conversationItems, setConversationItems] = useState(() => {
    const saved = sessionStorage.getItem("conversation_items");
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error("Failed to parse saved conversation:", e);
      }
    }
    return [];
  });

  const [dataPreview, setDataPreview] = useState([]);
  const [visualizations, setVisualizations] = useState([]);
  const [currentAgentType, setCurrentAgentType] = useState(null); // 'cleaner' or 'visualizer'
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
  const [versionStatus, setVersionStatus] = useState("");
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [versionDescription, setVersionDescription] = useState("");
  const [waitingForUser, setWaitingForUser] = useState(false);
  const [canSaveVersion, setCanSaveVersion] = useState(false);

  // Model config state - load from localStorage
  const [provider, setProvider] = useState(() => {
    return localStorage.getItem("llm_provider") || "google";
  });
  const [modelName, setModelName] = useState(() => {
    return localStorage.getItem("llm_model") || "gemini-2.0-flash-exp";
  });
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem("llm_api_key") || "";
  });

  // Database config state - load from localStorage
  const [db, setDb] = useState(() => {
    const savedDb = localStorage.getItem("db_config");
    if (savedDb) {
      try {
        return JSON.parse(savedDb);
      } catch (e) {
        console.error("Failed to parse saved db config:", e);
      }
    }
    return {
      host: "localhost",
      database: "preprocessing_logs",
      user: "postgres",
      password: "",
      port: 5432,
      csv_path: "deleted_data.csv",
    };
  });

  const eventSourceRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const chatInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Save model config to localStorage when it changes
  useEffect(() => {
    localStorage.setItem("llm_provider", provider);
  }, [provider]);

  useEffect(() => {
    localStorage.setItem("llm_model", modelName);
  }, [modelName]);

  useEffect(() => {
    if (apiKey) {
      localStorage.setItem("llm_api_key", apiKey);
    }
  }, [apiKey]);

  // Save database config to localStorage when it changes
  useEffect(() => {
    localStorage.setItem("db_config", JSON.stringify(db));
  }, [db]);

  // Save conversation to sessionStorage (cleared when browser closes)
  useEffect(() => {
    if (conversationItems.length > 0) {
      sessionStorage.setItem(
        "conversation_items",
        JSON.stringify(conversationItems)
      );
    }
  }, [conversationItems]);

  useEffect(() => {
    scrollToBottom();
  }, [conversationItems]);

  // Clear all storage when the window/tab is closed or refreshed
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      // Clear all localStorage data
      localStorage.removeItem("llm_provider");
      localStorage.removeItem("llm_model");
      localStorage.removeItem("llm_api_key");
      localStorage.removeItem("db_config");

      // Clear all sessionStorage data
      sessionStorage.removeItem("conversation_items");

      // Optional: You can also clear everything with these commands
      // localStorage.clear();
      // sessionStorage.clear();
    };

    // Add event listener for beforeunload (triggered when closing/refreshing)
    window.addEventListener("beforeunload", handleBeforeUnload);

    // Cleanup: Remove event listener when component unmounts
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  // Check configuration status on mount
  useEffect(() => {
    checkHealth();
    loadDataPreview();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      const data = await res.json();
      setIsConfigured(data.configured);
      setHasData(data.has_data);

      if (!data.configured) {
        setStatus("⚠️ Please configure the system first in Configuration page");
      } else if (data.has_data && data.data_info) {
        setUploadStatus(
          `✓ Data loaded: ${data.data_info.rows} rows, ${data.data_info.columns} columns`
        );
        if (data.db_configured) {
          setStatus("Ready to start");
        } else {
          setStatus(
            "⚠️ Database not configured - configure in Configuration page to save logs/versions"
          );
        }
      } else {
        setStatus("Ready - upload data to begin");
      }
    } catch (err) {
      console.error("Health check failed:", err);
      setStatus("Error checking system status");
    }
  };

  const loadDataPreview = async () => {
    try {
      const res = await fetch(`${API_BASE}/data-preview`);
      const data = await res.json();

      if (data.status === "success" && data.preview) {
        setDataPreview(data.preview);
      }
    } catch (err) {
      console.error("Failed to load data preview:", err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    console.log("File selected:", file);

    if (!file) {
      console.log("No file selected");
      return;
    }

    if (!isConfigured) {
      setUploadStatus("⚠️ Please configure the system first");
      return;
    }

    setUploadStatus("Uploading...");
    const formData = new FormData();
    formData.append("file", file);

    console.log("FormData created, uploading to:", `${API_BASE}/upload`);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      console.log("Upload response status:", res.status);
      const data = await res.json();
      console.log("Upload response data:", data);

      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }

      setHasData(true);
      setUploadStatus(`✓ Uploaded: ${data.rows} rows, ${data.columns} columns`);
      setStatus("Ready to start");

      // Display preview if available
      if (data.preview && data.preview.length > 0) {
        setDataPreview(data.preview);
      }

      // Reset file input to allow re-uploading the same file
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      console.error("Upload error:", err);
      setUploadStatus(`Error: ${err.message}`);
      setHasData(false);

      // Reset file input on error
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
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
    setConversationItems([]);
    // Don't clear data preview to avoid black screen
    setStatus("Connecting to cleaning agent...");
    setIsRunning(true);
    // Open sidebar automatically when starting agent
    setIsSidebarOpen(true);

    const es = new EventSource(`${API_BASE}/clean`);
    eventSourceRef.current = es;

    es.addEventListener("message", (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.node === "cleaner_node") {
          if (payload.last_message && payload.tool_call) {
            // Add message with its associated tools
            setConversationItems((prev) => [
              ...prev,
              {
                message: payload.last_message,
                tools: payload.tool_call,
                waiting_for_user: payload.waiting_for_user || false,
              },
            ]);
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
    });

    es.addEventListener("waiting", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setWaitingForUser(true);
        setCanSaveVersion(payload.can_save || false);
        setStatus(payload.message || "Waiting for your action...");
        setIsRunning(false); // Stop the running indicator
      } catch (e) {
        console.error("Bad waiting event payload", e);
      }
    });

    es.addEventListener("complete", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setStatus(payload.message || "Cleaning completed");
        setIsRunning(false);
        setWaitingForUser(false);
        es.close();
        eventSourceRef.current = null;
      } catch (e) {
        console.error("Bad complete event payload", e);
      }
    });

    es.onerror = (error) => {
      console.error("EventSource error:", error);
      setStatus("Cleaning completed");
      setIsRunning(false);
      es.close();
      eventSourceRef.current = null;
    };
  };

  const startVisualization = () => {
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

    setConversationItems([]);
    setVisualizations([]);
    setCurrentAgentType("visualizer");
    setStatus("Connecting to visualizer agent...");
    setIsRunning(true);
    setIsSidebarOpen(true);

    const es = new EventSource(`${API_BASE}/visualization`);
    eventSourceRef.current = es;

    es.addEventListener("message", (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.node === "visualizer_node") {
          if (payload.last_message) {
            setConversationItems((prev) => [
              ...prev,
              {
                message: payload.last_message,
                tools: payload.tool_call,
                waiting_for_user: payload.waiting_for_user || false,
              },
            ]);
          }

          // Update visualizations if provided
          if (payload.summary && payload.summary.visualizations) {
            setVisualizations(payload.summary.visualizations);
          }

          setStatus("Visualizer is processing...");
        }
      } catch (e) {
        console.error("Bad SSE payload", e);
        setStatus("Error processing visualizer response");
      }
    });

    es.addEventListener("complete", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setStatus(payload.message || "Visualization completed");
        setIsRunning(false);
        es.close();
        eventSourceRef.current = null;
      } catch (e) {
        console.error("Bad complete event payload", e);
      }
    });

    es.onerror = (error) => {
      console.error("EventSource error:", error);
      setStatus("Visualization completed");
      setIsRunning(false);
      es.close();
      eventSourceRef.current = null;
    };
  };

  const continueCleaning = async () => {
    if (!waitingForUser) {
      return;
    }

    setIsRunning(true);
    setWaitingForUser(false);
    setStatus("Continuing cleaning process...");

    try {
      const response = await fetch(`${API_BASE}/continue-cleaning`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            try {
              const payload = JSON.parse(data);

              if (payload.node === "cleaner_node") {
                if (payload.last_message && payload.tool_call) {
                  setConversationItems((prev) => [
                    ...prev,
                    {
                      message: payload.last_message,
                      tools: payload.tool_call,
                      waiting_for_user: payload.waiting_for_user || false,
                    },
                  ]);
                }
                if (payload.summary?.data_preview) {
                  setDataPreview(payload.summary.data_preview);
                }
                setStatus("Agent is processing...");
              }
            } catch (e) {
              // Not JSON, might be event type line
            }
          } else if (line.startsWith("event: waiting")) {
            // Next line will have the data
            setWaitingForUser(true);
            setIsRunning(false);
            setStatus("Waiting for your action...");
          } else if (line.startsWith("event: complete")) {
            setIsRunning(false);
            setWaitingForUser(false);
            setStatus("Cleaning completed");
            break;
          }
        }
      }
    } catch (error) {
      console.error("Error continuing cleaning:", error);
      setStatus("Error continuing cleaning");
      setIsRunning(false);
      setWaitingForUser(false);
    }
  };

  const saveVersionAndContinue = async () => {
    if (!waitingForUser) {
      return;
    }

    // First save the version
    const description = prompt("Enter a description for this version:");
    if (!description) {
      return; // User cancelled
    }

    try {
      const response = await fetch(`${API_BASE}/save-version`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool_details: description }),
      });

      if (!response.ok) {
        const error = await response.json();
        setVersionStatus(`Error: ${error.detail}`);
        return;
      }

      const result = await response.json();
      setVersionStatus(`Version saved: ${result.timestamp}`);

      // Then continue cleaning
      setTimeout(() => {
        setVersionStatus("");
        continueCleaning();
      }, 1000);
    } catch (error) {
      setVersionStatus(`Error: ${error.message}`);
    }
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

    // For now, only cleaner, visualizer and full pipeline work
    if (agentType === "cleaner" || agentType === "full") {
      startCleaning();
    } else if (agentType === "visualizer") {
      startVisualization();
    } else {
      setStatus(`⚠️ ${agentType} agent coming soon...`);
      // Placeholder for future implementation
      console.log(`Running ${agentType} agent...`);
    }
  };

  const handleSaveVersion = async (e) => {
    e.preventDefault();
    if (!versionDescription.trim()) {
      setVersionStatus("Please enter a description");
      return;
    }

    setVersionStatus("Saving version...");
    try {
      const res = await fetch(`${API_BASE}/save-version`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool_details: versionDescription,
        }),
      });

      // Get response text first (can only read once)
      const responseText = await res.text();

      // First check if response is ok
      if (!res.ok) {
        // Try to parse as JSON for error details
        let errorMsg = "Failed to save version";
        try {
          const errorData = JSON.parse(responseText);
          errorMsg = errorData.detail || errorMsg;
        } catch (jsonError) {
          // If not JSON, use the raw text
          errorMsg = responseText || errorMsg;
        }
        throw new Error(errorMsg);
      }

      // Parse the successful response
      const data = JSON.parse(responseText);
      setVersionStatus(
        `✓ Version saved successfully at ${new Date(
          data.timestamp
        ).toLocaleString()}`
      );
      setTimeout(() => {
        setShowVersionModal(false);
        setVersionDescription("");
        setVersionStatus("");
      }, 2000);
    } catch (err) {
      console.error("Save version error:", err);
      setVersionStatus(`Error: ${err.message}`);
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
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              style={{ marginRight: "6px" }}
            >
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
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              style={{ marginRight: "6px" }}
            >
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
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ marginRight: "6px" }}
                    className="spinning-icon"
                  >
                    <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                  </svg>
                  Running...
                </>
              ) : (
                <>
                  <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ marginRight: "6px" }}
                  >
                    <circle cx="12" cy="12" r="10" />
                    <polygon
                      points="10 8 16 12 10 16 10 8"
                      fill="currentColor"
                    />
                  </svg>
                  Start Agent
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    style={{ marginLeft: "6px" }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </>
              )}
            </button>
            {showAgentDropdown && !isRunning && (
              <div className="agent-dropdown">
                <div
                  className="agent-option"
                  onClick={() => runAgent("cleaner")}
                >
                  <div className="agent-option-icon">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                    </svg>
                  </div>
                  <div className="agent-option-content">
                    <h4>Cleaner Agent</h4>
                    <p>Clean and preprocess your data</p>
                  </div>
                  <button
                    className="agent-run-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      runAgent("cleaner");
                    }}
                  >
                    Run Now
                  </button>
                </div>
                <div
                  className="agent-option"
                  onClick={() => runAgent("analyser")}
                >
                  <div className="agent-option-icon">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <line x1="12" y1="20" x2="12" y2="10" />
                      <line x1="18" y1="20" x2="18" y2="4" />
                      <line x1="6" y1="20" x2="6" y2="16" />
                    </svg>
                  </div>
                  <div className="agent-option-content">
                    <h4>Analyser Agent</h4>
                    <p>Analyze patterns and insights</p>
                  </div>
                  <button
                    className="agent-run-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      runAgent("analyser");
                    }}
                  >
                    Run Now
                  </button>
                </div>
                <div
                  className="agent-option"
                  onClick={() => runAgent("visualizer")}
                >
                  <div className="agent-option-icon">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                    </svg>
                  </div>
                  <div className="agent-option-content">
                    <h4>Visualizer Agent</h4>
                    <p>Create charts and visualizations</p>
                  </div>
                  <button
                    className="agent-run-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      runAgent("visualizer");
                    }}
                  >
                    Run Now
                  </button>
                </div>
                <div className="agent-option" onClick={() => runAgent("full")}>
                  <div className="agent-option-icon">
                    <svg
                      width="20"
                      height="20"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
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
                  <button
                    className="agent-run-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      runAgent("full");
                    }}
                  >
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
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              style={{ marginRight: "6px" }}
            >
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            Chat
          </button>
          <button
            className="secondary-button"
            onClick={() => setShowVersionModal(true)}
            disabled={!hasData}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#10b981"
              strokeWidth="2"
              style={{ marginRight: "6px" }}
            >
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            Save Version
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
            {currentAgentType === "visualizer" && visualizations.length > 0 ? (
              <div className="visualizations-wrapper">
                {visualizations.map((viz, idx) => (
                  <div key={`viz-${idx}`} className="visualization-card">
                    <h4>{viz.title || `Visualization ${idx + 1}`}</h4>
                    {viz.type === "image" || typeof viz.data === "string" ? (
                      // Assume base64 image or URL
                      <img
                        src={
                          viz.data.startsWith("data:")
                            ? viz.data
                            : `data:image/png;base64,${viz.data}`
                        }
                        alt={viz.title || `viz-${idx}`}
                        style={{ maxWidth: "100%", height: "auto" }}
                      />
                    ) : (
                      // Fallback: render JSON spec
                      <pre style={{ whiteSpace: "pre-wrap" }}>
                        {JSON.stringify(viz.data, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            ) : dataPreview.length > 0 ? (
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
                <p>
                  {isRunning
                    ? "Processing data..."
                    : "No data to preview yet. Start the agent to see results."}
                </p>
              </div>
            )}
          </div>
        </section>

        {/* Sidebar - VS Code Copilot Style */}
        <aside
          className={`copilot-sidebar ${isSidebarOpen ? "open" : "collapsed"}`}
        >
          <button
            className="sidebar-toggle-btn"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              {isSidebarOpen ? (
                <path d="M9 18l6-6-6-6" />
              ) : (
                <path d="M15 18l-6-6 6-6" />
              )}
            </svg>
          </button>

          <div className="copilot-header">
            <div className="copilot-badge">{conversationItems.length}</div>
          </div>

          <div className="copilot-messages">
            {conversationItems.length === 0 ? (
              <div className="copilot-empty">
                <svg
                  width="64"
                  height="64"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1"
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                </svg>
                <h4>Welcome to Agent Chat</h4>
                <p>
                  Upload a dataset and start the agent, or ask me anything about
                  your data analysis.
                </p>
              </div>
            ) : (
              <>
                {conversationItems.map((item, i) => (
                  <React.Fragment key={`item-${i}`}>
                    <div className="copilot-message agent-message">
                      <div className="message-avatar agent-avatar">
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="currentColor"
                        >
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                        </svg>
                      </div>
                      <div className="message-bubble">
                        <div className="message-role">Agent</div>
                        <div className="message-body">{item.message}</div>
                      </div>
                    </div>

                    {item.tools &&
                      item.tools.map((tool, toolIdx) => (
                        <div
                          className="copilot-message tool-message"
                          key={`tool-${i}-${toolIdx}`}
                        >
                          <div className="message-avatar tool-avatar">
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2.5"
                            >
                              <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                            </svg>
                          </div>
                          <div className="message-bubble tool-bubble">
                            <div className="message-role">🔧 {tool.tool}</div>
                            <div className="tool-details">
                              <pre>{JSON.stringify(tool.params, null, 2)}</pre>
                            </div>
                          </div>
                        </div>
                      ))}
                  </React.Fragment>
                ))}
                <div ref={messagesEndRef} />

                {/* Action buttons when waiting for user */}
                {waitingForUser && (
                  <div
                    style={{
                      padding: "16px",
                      marginTop: "12px",
                      background: "#f0fdf4",
                      border: "1px solid #86efac",
                      borderRadius: "8px",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "0.875rem",
                        color: "#166534",
                        fontWeight: "600",
                        marginBottom: "12px",
                      }}
                    >
                      ⏸️ Agent is paused - Choose an action:
                    </div>
                    <div
                      style={{
                        display: "flex",
                        gap: "8px",
                        flexDirection: "column",
                      }}
                    >
                      {canSaveVersion && (
                        <button
                          onClick={saveVersionAndContinue}
                          style={{
                            padding: "10px 16px",
                            background: "#10b981",
                            color: "white",
                            border: "none",
                            borderRadius: "6px",
                            fontSize: "0.875rem",
                            fontWeight: "500",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            justifyContent: "center",
                          }}
                        >
                          <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                          >
                            <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                            <polyline points="17 21 17 13 7 13 7 21" />
                            <polyline points="7 3 7 8 15 8" />
                          </svg>
                          Save Version & Continue
                        </button>
                      )}
                      <button
                        onClick={continueCleaning}
                        style={{
                          padding: "10px 16px",
                          background: "#3b82f6",
                          color: "white",
                          border: "none",
                          borderRadius: "6px",
                          fontSize: "0.875rem",
                          fontWeight: "500",
                          cursor: "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          justifyContent: "center",
                        }}
                      >
                        <svg
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
                          <polygon points="5 3 19 12 5 21 5 3" />
                        </svg>
                        Continue Without Saving
                      </button>
                    </div>
                    {versionStatus && (
                      <div
                        style={{
                          marginTop: "8px",
                          fontSize: "0.75rem",
                          color: "#059669",
                        }}
                      >
                        {versionStatus}
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          <form
            className="copilot-input-container"
            onSubmit={handleSendMessage}
          >
            <div className="input-wrapper">
              <textarea
                ref={chatInputRef}
                className="copilot-input"
                placeholder="Ask about your data..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
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
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2"
                >
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
                  <button className="modal-close" onClick={closeConfigModal}>
                    ×
                  </button>
                </div>
                <div className="modal-body">
                  <p className="modal-description">
                    Choose what you want to configure:
                  </p>
                  <div className="config-options">
                    <button
                      className="config-option-card"
                      onClick={() => openConfigModal("model")}
                    >
                      <div className="option-icon">
                        <svg
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
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
                      onClick={() => openConfigModal("database")}
                    >
                      <div className="option-icon">
                        <svg
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                        >
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
            ) : configType === "model" ? (
              <>
                <div className="modal-header">
                  <h3>Model Configuration</h3>
                  <button className="modal-close" onClick={closeConfigModal}>
                    ×
                  </button>
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
                    <small className="form-hint">
                      Only Google Gemini is currently supported
                    </small>
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
                    <div
                      className={`config-status ${
                        configStatus.includes("✓")
                          ? "success"
                          : configStatus.includes("⚠️") ||
                            configStatus.includes("Error")
                          ? "error"
                          : ""
                      }`}
                    >
                      {configStatus}
                    </div>
                  )}

                  <div className="modal-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={closeConfigModal}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="2"
                        style={{ marginRight: "6px" }}
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                      Cancel
                    </button>
                    <button type="submit" className="primary-button">
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="white"
                        strokeWidth="2"
                        style={{ marginRight: "6px" }}
                      >
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
                  <button className="modal-close" onClick={closeConfigModal}>
                    ×
                  </button>
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
                    <small className="form-hint">
                      Only PostgreSQL is currently supported
                    </small>
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
                        onChange={(e) =>
                          setDb({
                            ...db,
                            port: parseInt(e.target.value, 10) || 5432,
                          })
                        }
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
                      onChange={(e) =>
                        setDb({ ...db, database: e.target.value })
                      }
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
                      onChange={(e) =>
                        setDb({ ...db, password: e.target.value })
                      }
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
                      onChange={(e) =>
                        setDb({ ...db, csv_path: e.target.value })
                      }
                    />
                  </div>

                  {configStatus && (
                    <div
                      className={`config-status ${
                        configStatus.includes("✓")
                          ? "success"
                          : configStatus.includes("⚠️") ||
                            configStatus.includes("Error")
                          ? "error"
                          : ""
                      }`}
                    >
                      {configStatus}
                    </div>
                  )}

                  <div className="modal-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={closeConfigModal}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#10b981"
                        strokeWidth="2"
                        style={{ marginRight: "6px" }}
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                      Cancel
                    </button>
                    <button type="submit" className="primary-button">
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="white"
                        strokeWidth="2"
                        style={{ marginRight: "6px" }}
                      >
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

      {/* Version Modal */}
      {showVersionModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowVersionModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>💾 Save Data Version</h3>
              <button
                className="modal-close"
                onClick={() => setShowVersionModal(false)}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <form onSubmit={handleSaveVersion}>
              <div className="form-group">
                <label htmlFor="version-description">Version Description</label>
                <input
                  id="version-description"
                  className="form-input"
                  value={versionDescription}
                  onChange={(e) => setVersionDescription(e.target.value)}
                  placeholder="E.g., After cleaning missing values, Before removing outliers"
                  required
                  autoFocus
                />
                <small
                  style={{
                    color: "#666",
                    fontSize: "0.85rem",
                    marginTop: "4px",
                    display: "block",
                  }}
                >
                  Describe what this version represents (tool used, changes
                  made, etc.)
                </small>
              </div>

              {versionStatus && (
                <div
                  className={`config-status ${
                    versionStatus.includes("✓")
                      ? "success"
                      : versionStatus.includes("Error")
                      ? "error"
                      : ""
                  }`}
                >
                  {versionStatus}
                </div>
              )}

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowVersionModal(false)}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2"
                    style={{ marginRight: "6px" }}
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="white"
                    strokeWidth="2"
                    style={{ marginRight: "6px" }}
                  >
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                    <polyline points="17 21 17 13 7 13 7 21" />
                    <polyline points="7 3 7 8 15 8" />
                  </svg>
                  Save Version
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Version Save Modal */}
      {showVersionModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowVersionModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Save Data Version</h3>
              <button
                className="modal-close"
                onClick={() => setShowVersionModal(false)}
              >
                ×
              </button>
            </div>
            <form onSubmit={handleSaveVersion} className="modal-body">
              <p
                style={{
                  marginBottom: "16px",
                  color: "#666",
                  fontSize: "0.9rem",
                }}
              >
                Create a snapshot of the current data state. You can revert to
                this version later.
              </p>
              <div className="form-group">
                <label htmlFor="version-description">Version Description</label>
                <input
                  id="version-description"
                  type="text"
                  className="form-input"
                  value={versionDescription}
                  onChange={(e) => setVersionDescription(e.target.value)}
                  placeholder="e.g., After removing duplicates, Before feature engineering..."
                  required
                  autoFocus
                />
                <small className="form-hint">
                  Describe what this version represents or what changes were
                  made
                </small>
              </div>

              {versionStatus && (
                <div
                  className={`config-status ${
                    versionStatus.includes("✓")
                      ? "success"
                      : versionStatus.includes("Error")
                      ? "error"
                      : ""
                  }`}
                >
                  {versionStatus}
                </div>
              )}

              <div className="modal-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => setShowVersionModal(false)}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#10b981"
                    strokeWidth="2"
                    style={{ marginRight: "6px" }}
                  >
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="white"
                    strokeWidth="2"
                    style={{ marginRight: "6px" }}
                  >
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                    <polyline points="17 21 17 13 7 13 7 21" />
                  </svg>
                  Save Version
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default LlmPage;
