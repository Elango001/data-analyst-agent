import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

const RollbackPage = () => {
  const [activeTab, setActiveTab] = useState("logs"); // 'logs' or 'versions'
  const [logs, setLogs] = useState([]);
  const [versions, setVersions] = useState([]);
  const [status, setStatus] = useState("");
  const [versionStatus, setVersionStatus] = useState("");

  useEffect(() => {
    loadLogs();
    loadVersions();
  }, []);

  const loadLogs = async () => {
    setStatus("Loading tool logs...");
    try {
      const res = await fetch(`${API_BASE}/tool-logs`);

      if (!res.ok) {
        const errorText = await res.text();
        let errorMsg = "Failed to load logs";
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.detail || errorMsg;
        } catch {
          errorMsg = errorText || errorMsg;
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      setLogs(data.logs || []);
      setStatus(
        data.logs && data.logs.length > 0
          ? `Loaded ${data.logs.length} tool execution(s)`
          : "No tool executions found"
      );
    } catch (err) {
      console.error("Logs error:", err);
      setStatus(`Error: ${err.message}`);
      setLogs([]);
    }
  };

  const loadVersions = async () => {
    setVersionStatus("Loading versions...");
    try {
      const res = await fetch(`${API_BASE}/versions`);

      if (!res.ok) {
        const errorText = await res.text();
        let errorMsg = "Failed to load versions";
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.detail || errorMsg;
        } catch {
          errorMsg = errorText || errorMsg;
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      setVersions(data.versions || []);
      setVersionStatus(
        data.versions && data.versions.length > 0
          ? `Loaded ${data.versions.length} version(s)`
          : "No versions found"
      );
    } catch (err) {
      console.error("Versions error:", err);
      setVersionStatus(`Error: ${err.message}`);
      setVersions([]);
    }
  };

  const handleRevert = async (version) => {
    if (
      !confirm(
        `Are you sure you want to revert to this version?\n\nDescription: ${
          version.tool_details
        }\nTimestamp: ${new Date(
          version.timestamp
        ).toLocaleString()}\n\nThis will save the current data as a new version and then load the selected version.`
      )
    ) {
      return;
    }

    setVersionStatus("Reverting to version...");

    try {
      // Step 1: Save current data as a new version before reverting
      const saveRes = await fetch(`${API_BASE}/save-version`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tool_details: `Auto-backup before reverting to: ${version.tool_details}`,
        }),
      });

      if (!saveRes.ok) {
        const errorData = await saveRes.json();
        throw new Error(errorData.detail || "Failed to backup current data");
      }

      // Step 2: Revert to the selected version
      const revertRes = await fetch(`${API_BASE}/revert-version`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timestamp: version.timestamp }),
      });

      if (!revertRes.ok) {
        const errorData = await revertRes.json();
        throw new Error(errorData.detail || "Revert failed");
      }

      const data = await revertRes.json();
      setVersionStatus(
        `Successfully reverted! Rows: ${data.rows}, Columns: ${data.columns}`
      );

      // Reload versions to show the new backup version
      loadVersions();
    } catch (err) {
      console.error("Revert error:", err);
      setVersionStatus(`Error: ${err.message}`);
      alert(`Failed to revert: ${err.message}`);
    }
  };

  return (
    <div className="page rollback-page">
      <div className="page-header-compact">
        <h2>Rollback & Version Control</h2>
        <p style={{ margin: "8px 0 0 0", color: "#666", fontSize: "0.9rem" }}>
          View tool execution logs and manage data versions
        </p>
      </div>

      {/* Tab Navigation */}
      <div
        style={{
          display: "flex",
          gap: "8px",
          borderBottom: "2px solid #eaeaea",
          marginBottom: "20px",
          marginTop: "20px",
        }}
      >
        <button
          onClick={() => setActiveTab("logs")}
          style={{
            padding: "12px 24px",
            background: activeTab === "logs" ? "#fff" : "transparent",
            border: "none",
            borderBottom:
              activeTab === "logs"
                ? "3px solid #10b981"
                : "3px solid transparent",
            cursor: "pointer",
            fontSize: "0.95rem",
            fontWeight: activeTab === "logs" ? "600" : "400",
            color: activeTab === "logs" ? "#10b981" : "#666",
            transition: "all 0.2s",
          }}
        >
          📋 Tool Logs
        </button>
        <button
          onClick={() => setActiveTab("versions")}
          style={{
            padding: "12px 24px",
            background: activeTab === "versions" ? "#fff" : "transparent",
            border: "none",
            borderBottom:
              activeTab === "versions"
                ? "3px solid #10b981"
                : "3px solid transparent",
            cursor: "pointer",
            fontSize: "0.95rem",
            fontWeight: activeTab === "versions" ? "600" : "400",
            color: activeTab === "versions" ? "#10b981" : "#666",
            transition: "all 0.2s",
          }}
        >
          💾 Data Versions
        </button>
      </div>

      {/* Logs Tab */}
      {activeTab === "logs" && (
        <div>
          <div className="status-bar">{status}</div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Timestamp</th>
                  <th>Tool Name</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td
                      colSpan="3"
                      style={{
                        textAlign: "center",
                        padding: "40px",
                        color: "#999",
                      }}
                    >
                      {status.includes("Error") ||
                      status.includes("not configured")
                        ? status
                        : "No logs available yet. Run the agent to see execution logs."}
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id}>
                      <td>{log.id}</td>
                      <td>{new Date(log.timestamp).toLocaleString()}</td>
                      <td>{log.tool_name}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Versions Tab */}
      {activeTab === "versions" && (
        <div>
          <div className="status-bar">{versionStatus}</div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Description / Name</th>
                  <th>Timestamp</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {versions.length === 0 ? (
                  <tr>
                    <td
                      colSpan="3"
                      style={{
                        textAlign: "center",
                        padding: "40px",
                        color: "#999",
                      }}
                    >
                      {versionStatus.includes("Error") ||
                      versionStatus.includes("not configured")
                        ? versionStatus
                        : "No versions saved yet. Save a version to create a checkpoint."}
                    </td>
                  </tr>
                ) : (
                  versions.map((version, index) => (
                    <tr key={index}>
                      <td>
                        <strong>{version.tool_details}</strong>
                      </td>
                      <td style={{ fontSize: "0.9rem" }}>
                        {new Date(version.timestamp).toLocaleString()}
                      </td>
                      <td>
                        <button
                          className="secondary-button"
                          onClick={() => handleRevert(version)}
                          style={{
                            fontSize: "0.85rem",
                            padding: "8px 16px",
                            borderColor: "#10b981",
                            color: "#10b981",
                          }}
                        >
                          <svg
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="#10b981"
                            strokeWidth="2"
                            style={{ marginRight: "4px" }}
                          >
                            <polyline points="1 4 1 10 7 10" />
                            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                          </svg>
                          Revert
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default RollbackPage;
