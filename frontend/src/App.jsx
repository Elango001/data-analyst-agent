import { useEffect, useMemo, useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const MODEL_OPTIONS = {
  google: ["gemini-2.5-flash", "gemini-1.5-pro"],
  openai: ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
  claude: ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
};

function App() {
  const [page, setPage] = useState("config");
  const [configForm, setConfigForm] = useState({
    llm_provider: "google",
    llm_model: "gemini-2.5-flash",
    llm_api_key: "",
    db_host: "localhost",
    db_database: "preprocessing_logs",
    db_user: "postgres",
    db_password: "",
    db_port: 5432,
  });
  const [configStatus, setConfigStatus] = useState("");
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadInfo, setUploadInfo] = useState(null);
  const [logs, setLogs] = useState({ tools: [], agents: [], code: [] });
  const [logStatus, setLogStatus] = useState("");
  const [runStatus, setRunStatus] = useState("");
  const [events, setEvents] = useState([]);
  const [lastState, setLastState] = useState(null);
  const [maxIterations, setMaxIterations] = useState(10);
  const [maxTotalIterations, setMaxTotalIterations] = useState("");
  const [activeStream, setActiveStream] = useState(null);
  const [theme, setTheme] = useState("dark");
  const [showConfigModal, setShowConfigModal] = useState(false);

  const modelOptions = useMemo(
    () => MODEL_OPTIONS[configForm.llm_provider] || [],
    [configForm.llm_provider],
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const handleConfigChange = (key, value) => {
    setConfigForm((prev) => ({ ...prev, [key]: value }));
  };

  const pushEvent = (type, payload) => {
    setEvents((prev) => [
      { type, payload, ts: new Date().toISOString() },
      ...prev,
    ]);
  };

  const handleSetConfig = async () => {
    setConfigStatus("Saving configuration...");
    try {
      const response = await fetch(`${API_BASE}/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(configForm),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Configuration failed");
      }
      setConfigStatus("Configuration saved successfully.");
    } catch (error) {
      setConfigStatus(`Config error: ${error.message}`);
    }
  };

  const handleUpload = async (file) => {
    if (!file) {
      setUploadStatus("Please select a CSV file.");
      return;
    }
    setUploadStatus("Uploading dataset...");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(`${API_BASE}/data/upload`, {
        method: "POST",
        body: formData,
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Upload failed");
      }
      setUploadInfo(result);
      setUploadStatus(`Upload complete. ${result.rows} rows loaded.`);
    } catch (error) {
      setUploadStatus(`Upload error: ${error.message}`);
    }
  };

  const fetchLogs = async () => {
    setLogStatus("Fetching logs...");
    try {
      const [toolsRes, agentsRes, codeRes] = await Promise.all([
        fetch(`${API_BASE}/logs/tools`),
        fetch(`${API_BASE}/logs/agents`),
        fetch(`${API_BASE}/logs/code`),
      ]);
      const [tools, agents, code] = await Promise.all([
        toolsRes.json(),
        agentsRes.json(),
        codeRes.json(),
      ]);
      if (!toolsRes.ok || !agentsRes.ok || !codeRes.ok) {
        throw new Error("Failed to fetch logs.");
      }
      setLogs({ tools: tools.logs, agents: agents.logs, code: code.logs });
      setLogStatus("Logs updated.");
    } catch (error) {
      setLogStatus(`Log error: ${error.message}`);
    }
  };

  const streamSse = async (endpoint, payload) => {
    if (activeStream) {
      activeStream.abort();
    }
    setEvents([]);
    setRunStatus("Running...");
    const controller = new AbortController();
    setActiveStream(controller);

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Run failed");
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";
        chunks.forEach((chunk) => {
          const lines = chunk.split("\n");
          let eventType = "message";
          let data = "";
          lines.forEach((line) => {
            if (line.startsWith("event:")) {
              eventType = line.replace("event:", "").trim();
            } else if (line.startsWith("data:")) {
              data += line.replace("data:", "").trim();
            }
          });
          if (!data) return;
          let payloadData = data;
          try {
            payloadData = JSON.parse(data);
          } catch (_) {
            payloadData = data;
          }
          if (eventType === "state") {
            setLastState(payloadData);
          }
          if (eventType === "done" && payloadData.state) {
            setLastState(payloadData.state);
            setRunStatus("Completed.");
          }
          pushEvent(eventType, payloadData);
        });
      }
    } catch (error) {
      if (error.name === "AbortError") {
        setRunStatus("Run cancelled.");
      } else {
        setRunStatus(`Run error: ${error.message}`);
      }
    } finally {
      setActiveStream(null);
    }
  };

  const handleRun = (endpoint) => {
    const payload = {
      max_iterations: Number(maxIterations) || 10,
    };
    if (endpoint === "/pipeline/run" && maxTotalIterations) {
      payload.max_total_iterations = Number(maxTotalIterations);
    }
    streamSse(endpoint, payload);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">VI</div>
          <div>
            <h1>Verdant Insight</h1>
            <p>Data Analyst Agent</p>
          </div>
        </div>
        <button
          className="btn btn-outline-success theme-toggle"
          onClick={() =>
            setTheme((prev) => (prev === "dark" ? "light" : "dark"))
          }
          type="button"
        >
          {theme === "dark" ? "Switch to Light" : "Switch to Dark"}
        </button>
        <nav className="nav flex-column">
          <button
            className={`nav-link ${page === "config" ? "active" : ""}`}
            onClick={() => setPage("config")}
          >
            Configuration + Upload
          </button>
          <button
            className={`nav-link ${page === "logs" ? "active" : ""}`}
            onClick={() => setPage("logs")}
          >
            Logs
          </button>
          <button
            className={`nav-link ${page === "pipeline" ? "active" : ""}`}
            onClick={() => setPage("pipeline")}
          >
            Pipeline Runner
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="status-pill">API: {API_BASE}</div>
          <div className="status-pill">Theme: Green / Graphite</div>
        </div>
      </aside>

      <main className="content">
        <header className="page-header">
          <div>
            <h2>
              {page === "config"
                ? "Configuration & Data Upload"
                : page === "logs"
                  ? "Execution Logs"
                  : "Pipeline Console"}
            </h2>
            <p>
              Manage model + database settings, inspect logs, and run the agent
              pipeline.
            </p>
          </div>
          {page === "logs" && (
            <button className="btn btn-outline-success" onClick={fetchLogs}>
              Refresh Logs
            </button>
          )}
        </header>

        {page === "config" && (
          <section className="grid-two">
            <div className="card panel full-width">
              <div className="panel-header">
                <div>
                  <h3>Configuration</h3>
                  <p className="muted">Open the popup to set model and DB.</p>
                </div>
                <button
                  className="btn btn-success"
                  onClick={() => setShowConfigModal(true)}
                  type="button"
                >
                  Configure
                </button>
              </div>
              <div className="status-box">
                {configStatus || "Awaiting configuration update."}
              </div>
            </div>

            <div className="card panel full-width">
              <div className="panel-header">
                <div>
                  <h3>Upload Dataset</h3>
                  <p className="muted">
                    Upload a CSV to load into the pipeline.
                  </p>
                </div>
                <input
                  type="file"
                  accept=".csv"
                  className="form-control file-input"
                  onChange={(e) => handleUpload(e.target.files?.[0])}
                />
              </div>
              <div className="status-box">
                {uploadStatus || "No dataset uploaded yet."}
              </div>
              {uploadInfo && (
                <div className="pill-row">
                  <span className="pill">Rows: {uploadInfo.rows}</span>
                  <span className="pill">
                    Columns: {uploadInfo.columns.length}
                  </span>
                </div>
              )}
            </div>
          </section>
        )}

        {page === "logs" && (
          <section className="grid-two">
            <div className="card panel full-width">
              <div className="panel-header">
                <div>
                  <h3>Log Streams</h3>
                  <p className="muted">
                    Latest tool, agent, and code execution records.
                  </p>
                </div>
                <span className="status-pill">{logStatus || "Idle"}</span>
              </div>
            </div>
            <div className="card panel full-width">
              <h4>Tool Logs</h4>
              <pre className="log-box">
                {JSON.stringify(logs.tools, null, 2)}
              </pre>
            </div>
            <div className="card panel full-width">
              <h4>Agent Logs</h4>
              <pre className="log-box">
                {JSON.stringify(logs.agents, null, 2)}
              </pre>
            </div>
            <div className="card panel full-width">
              <h4>Code Logs</h4>
              <pre className="log-box">
                {JSON.stringify(logs.code, null, 2)}
              </pre>
            </div>
          </section>
        )}

        {page === "pipeline" && (
          <section className="grid-two">
            <div className="panel full-width">
              <div className="row g-4">
                <div className="col-12 col-lg-6">
                  <div className="card panel h-100">
                    <h3>Execution Controls</h3>
                    <div className="row g-3">
                      <div className="col-12">
                        <label className="form-label">
                          Max iterations per stage
                        </label>
                        <input
                          type="number"
                          className="form-control"
                          value={maxIterations}
                          onChange={(e) => setMaxIterations(e.target.value)}
                        />
                      </div>
                      <div className="col-12">
                        <label className="form-label">
                          Total iterations (pipeline only)
                        </label>
                        <input
                          type="number"
                          className="form-control"
                          value={maxTotalIterations}
                          onChange={(e) =>
                            setMaxTotalIterations(e.target.value)
                          }
                          placeholder="Optional"
                        />
                      </div>
                    </div>
                    <div className="btn-group mt-3 w-100">
                      <button
                        className="btn btn-outline-success"
                        onClick={() => handleRun("/cleaner/run")}
                      >
                        Run Cleaner
                      </button>
                      <button
                        className="btn btn-outline-success"
                        onClick={() => handleRun("/analyser/run")}
                      >
                        Run Analyser
                      </button>
                      <button
                        className="btn btn-outline-success"
                        onClick={() => handleRun("/visualizer/run")}
                      >
                        Run Visualizer
                      </button>
                    </div>
                    <button
                      className="btn btn-success mt-3 w-100"
                      onClick={() => handleRun("/pipeline/run")}
                    >
                      Run Full Pipeline
                    </button>
                    <button
                      className="btn btn-outline-secondary mt-2 w-100"
                      onClick={() => activeStream?.abort()}
                      disabled={!activeStream}
                    >
                      Stop Stream
                    </button>
                  </div>
                </div>

                <div className="col-12 col-lg-6">
                  <div className="card panel h-100">
                    <h3>Run Status</h3>
                    <div className="status-box">{runStatus || "Idle"}</div>
                    <h4 className="mt-3">Latest State Snapshot</h4>
                    <pre className="log-box">
                      {JSON.stringify(lastState, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>

            <div className="card panel full-width">
              <div className="panel-header">
                <h3>Streaming Output</h3>
                <span className="status-pill">{events.length} events</span>
              </div>
              <div className="event-feed">
                {events.length === 0 && <p className="muted">No events yet.</p>}
                {events.map((event, index) => (
                  <div key={`${event.ts}-${index}`} className="event-item">
                    <div className="event-meta">
                      <span className="badge bg-success-subtle text-success">
                        {event.type}
                      </span>
                      <span className="timestamp">{event.ts}</span>
                    </div>
                    <pre>{JSON.stringify(event.payload, null, 2)}</pre>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}

        {showConfigModal && (
          <div className="config-modal-backdrop">
            <div className="config-modal">
              <div className="panel-header">
                <div>
                  <h3>Model + Database Configuration</h3>
                  <p className="muted">Enter credentials and save.</p>
                </div>
                <button
                  className="btn btn-outline-secondary"
                  onClick={() => setShowConfigModal(false)}
                  type="button"
                >
                  Close
                </button>
              </div>

              <div className="row g-4">
                <div className="col-12 col-lg-6">
                  <div className="card panel h-100">
                    <h4>Model Configuration</h4>
                    <div className="row g-3">
                      <div className="col-12">
                        <label className="form-label">Provider</label>
                        <select
                          className="form-select"
                          value={configForm.llm_provider}
                          onChange={(e) =>
                            handleConfigChange("llm_provider", e.target.value)
                          }
                        >
                          <option value="google">Google</option>
                          <option value="openai">OpenAI</option>
                          <option value="claude">Claude</option>
                        </select>
                      </div>
                      <div className="col-12">
                        <label className="form-label">Model</label>
                        <select
                          className="form-select"
                          value={configForm.llm_model}
                          onChange={(e) =>
                            handleConfigChange("llm_model", e.target.value)
                          }
                        >
                          {modelOptions.map((model) => (
                            <option key={model} value={model}>
                              {model}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="col-12">
                        <label className="form-label">API Key</label>
                        <input
                          type="password"
                          className="form-control"
                          value={configForm.llm_api_key}
                          onChange={(e) =>
                            handleConfigChange("llm_api_key", e.target.value)
                          }
                          placeholder="Paste your API key"
                        />
                      </div>
                    </div>
                  </div>
                </div>
                <div className="col-12 col-lg-6">
                  <div className="card panel h-100">
                    <h4>Database Configuration</h4>
                    <div className="row g-3">
                      <div className="col-12">
                        <label className="form-label">Host</label>
                        <input
                          className="form-control"
                          value={configForm.db_host}
                          onChange={(e) =>
                            handleConfigChange("db_host", e.target.value)
                          }
                        />
                      </div>
                      <div className="col-12">
                        <label className="form-label">Database</label>
                        <input
                          className="form-control"
                          value={configForm.db_database}
                          onChange={(e) =>
                            handleConfigChange("db_database", e.target.value)
                          }
                        />
                      </div>
                      <div className="col-12">
                        <label className="form-label">User</label>
                        <input
                          className="form-control"
                          value={configForm.db_user}
                          onChange={(e) =>
                            handleConfigChange("db_user", e.target.value)
                          }
                        />
                      </div>
                      <div className="col-12">
                        <label className="form-label">Password</label>
                        <input
                          type="password"
                          className="form-control"
                          value={configForm.db_password}
                          onChange={(e) =>
                            handleConfigChange("db_password", e.target.value)
                          }
                        />
                      </div>
                      <div className="col-12">
                        <label className="form-label">Port</label>
                        <input
                          type="number"
                          className="form-control"
                          value={configForm.db_port}
                          onChange={(e) =>
                            handleConfigChange(
                              "db_port",
                              Number(e.target.value),
                            )
                          }
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <div className="status-box">
                  {configStatus || "Awaiting configuration update."}
                </div>
                <button
                  className="btn btn-success"
                  onClick={handleSetConfig}
                  type="button"
                >
                  Save Configuration
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
