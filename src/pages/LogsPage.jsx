import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

const LogsPage = () => {
  const [activeTab, setActiveTab] = useState("logs"); // 'logs' or 'versions'
  const [logs, setLogs] = useState([]);
  const [versions, setVersions] = useState([]);
  const [status, setStatus] = useState("");
  const [versionStatus, setVersionStatus] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);
  const [deletedData, setDeletedData] = useState(null);
  const [loadingDeleted, setLoadingDeleted] = useState(false);

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

  const handleViewDeleted = async (logId) => {
    if (selectedLog === logId) {
      setSelectedLog(null);
      setDeletedData(null);
      return;
    }

    setSelectedLog(logId);
    setLoadingDeleted(true);
    try {
      const res = await fetch(`${API_BASE}/deleted-data/${logId}`);
      const data = await res.json();

      if (data.status === "success" && data.data) {
        setDeletedData(data.data);
      } else {
        setDeletedData(null);
      }
    } catch (err) {
      console.error("Error loading deleted data:", err);
      setDeletedData(null);
    } finally {
      setLoadingDeleted(false);
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

  const handleDeleteVersion = async (version) => {
    if (
      !confirm(
        `Are you sure you want to DELETE this version?\n\nDescription: ${
          version.tool_details
        }\nTimestamp: ${new Date(
          version.timestamp
        ).toLocaleString()}\n\nThis action cannot be undone! The CSV file and database record will be permanently deleted.`
      )
    ) {
      return;
    }

    setVersionStatus("Deleting version...");

    try {
      const deleteRes = await fetch(`${API_BASE}/delete-version`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timestamp: version.timestamp }),
      });

      if (!deleteRes.ok) {
        const errorData = await deleteRes.json();
        throw new Error(errorData.detail || "Delete failed");
      }

      const data = await deleteRes.json();
      setVersionStatus(`Successfully deleted version!`);
      loadVersions(); // Reload versions to update the list
    } catch (err) {
      console.error("Delete error:", err);
      setVersionStatus(`Error: ${err.message}`);
      alert(`Failed to delete: ${err.message}`);
    }
  };

  return (
    <div className="page llm-page">
      <div className="llm-header">
        <div className="llm-header-content">
          <h2>Logs & Version Control</h2>
          <p className="llm-subtitle">
            View tool execution logs, agent responses, and manage data versions
          </p>
        </div>
      </div>

      <div className="llm-content" style={{ padding: "20px" }}>
        {/* Tab Navigation */}
        <div
          style={{
            display: "flex",
            gap: "12px",
            marginBottom: "24px",
          }}
        >
          <button
            onClick={() => setActiveTab("logs")}
            className={
              activeTab === "logs" ? "primary-button" : "secondary-button"
            }
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke={activeTab === "logs" ? "currentColor" : "#10b981"}
              strokeWidth="2"
              style={{ marginRight: "6px" }}
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            Tool Logs
          </button>
          <button
            onClick={() => setActiveTab("versions")}
            className={
              activeTab === "versions" ? "primary-button" : "secondary-button"
            }
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke={activeTab === "versions" ? "currentColor" : "#10b981"}
              strokeWidth="2"
              style={{ marginRight: "6px" }}
            >
              <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
              <polyline points="17 21 17 13 7 13 7 21" />
              <polyline points="7 3 7 8 15 8" />
            </svg>
            Data Versions
          </button>
        </div>

        {/* Content Area */}
        <div
          style={{
            height: "calc(100vh - 250px)",
            overflow: "auto",
          }}
        >
          {/* Logs Tab - Professional Card Layout */}
          {activeTab === "logs" && (
            <div>
              <div className="status-bar" style={{ marginBottom: "20px" }}>
                {status}
              </div>

              {logs.length === 0 ? (
                <div
                  style={{
                    textAlign: "center",
                    padding: "60px 20px",
                    background: "#f9fafb",
                    borderRadius: "12px",
                    border: "2px dashed #d1d5db",
                  }}
                >
                  <div style={{ fontSize: "3rem", marginBottom: "16px" }}>
                    📋
                  </div>
                  <p
                    style={{
                      color: "#6b7280",
                      fontSize: "1.1rem",
                      margin: "0",
                    }}
                  >
                    {status.includes("Error") ||
                    status.includes("not configured")
                      ? status
                      : "No logs available yet. Run the agent to see execution logs."}
                  </p>
                </div>
              ) : (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "16px",
                  }}
                >
                  {logs.map((log) => (
                    <div
                      key={log.id}
                      style={{
                        background: "#fff",
                        border: "1px solid #e5e7eb",
                        borderRadius: "12px",
                        padding: "20px",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                        transition: "all 0.2s",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.boxShadow =
                          "0 4px 6px rgba(0,0,0,0.1)";
                        e.currentTarget.style.borderColor = "#10b981";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.boxShadow =
                          "0 1px 3px rgba(0,0,0,0.05)";
                        e.currentTarget.style.borderColor = "#e5e7eb";
                      }}
                    >
                      {/* Log Header */}
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "flex-start",
                          marginBottom: "16px",
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "12px",
                              marginBottom: "8px",
                            }}
                          >
                            <span
                              style={{
                                background: "#10b981",
                                color: "#fff",
                                padding: "4px 12px",
                                borderRadius: "6px",
                                fontSize: "0.75rem",
                                fontWeight: "600",
                              }}
                            >
                              ID: {log.id}
                            </span>
                            <span
                              style={{
                                color: "#6b7280",
                                fontSize: "0.875rem",
                              }}
                            >
                              {new Date(log.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <h3
                            style={{
                              margin: "0 0 8px 0",
                              fontSize: "1.1rem",
                              color: "#111827",
                              fontWeight: "600",
                            }}
                          >
                            {log.tool_name}
                          </h3>
                          <div
                            style={{
                              display: "flex",
                              gap: "12px",
                              alignItems: "center",
                            }}
                          >
                            <span
                              style={{
                                display: "inline-flex",
                                alignItems: "center",
                                gap: "6px",
                                padding: "4px 12px",
                                borderRadius: "6px",
                                fontSize: "0.813rem",
                                fontWeight: "500",
                                background: log.deleted_data
                                  ? "#fee2e2"
                                  : "#f3f4f6",
                                color: log.deleted_data ? "#dc2626" : "#6b7280",
                              }}
                            >
                              {log.deleted_data
                                ? "Has Deleted Data"
                                : "No Data Deleted"}
                            </span>
                          </div>
                        </div>

                        {/* View Button */}
                        {log.deleted_data && (
                          <button
                            className="secondary-button"
                            onClick={() => handleViewDeleted(log.id)}
                            style={{
                              fontSize: "0.875rem",
                              padding: "8px 16px",
                              display: "flex",
                              alignItems: "center",
                              gap: "6px",
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
                              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                              <circle cx="12" cy="12" r="3" />
                            </svg>
                            {selectedLog === log.id ? "Hide Data" : "View Data"}
                          </button>
                        )}
                      </div>

                      {/* Cleaner Agent Response */}
                      <div
                        style={{
                          background: "#f0fdf4",
                          border: "1px solid #86efac",
                          borderRadius: "8px",
                          padding: "16px",
                          marginTop: "16px",
                          marginBottom: selectedLog === log.id ? "16px" : "0",
                        }}
                      >
                        <h4
                          style={{
                            margin: "0 0 8px 0",
                            fontSize: "0.875rem",
                            fontWeight: "600",
                            color: "#166534",
                          }}
                        >
                          Cleaner Agent Response
                        </h4>
                        {log.cleaner_response ? (
                          <p
                            style={{
                              margin: 0,
                              fontSize: "0.875rem",
                              color: "#15803d",
                              lineHeight: "1.6",
                              whiteSpace: "pre-wrap",
                            }}
                          >
                            {log.cleaner_response}
                          </p>
                        ) : (
                          <p
                            style={{
                              margin: 0,
                              fontSize: "0.875rem",
                              color: "#6b7280",
                              fontStyle: "italic",
                            }}
                          >
                            No agent response available for this execution
                          </p>
                        )}
                      </div>

                      {/* Deleted Data Preview */}
                      {selectedLog === log.id && (
                        <div
                          style={{
                            background: "#fef2f2",
                            border: "1px solid #fecaca",
                            borderRadius: "8px",
                            padding: "16px",
                            marginTop: "12px",
                          }}
                        >
                          <h4
                            style={{
                              margin: "0 0 12px 0",
                              fontSize: "0.875rem",
                              fontWeight: "600",
                              color: "#991b1b",
                            }}
                          >
                            Deleted Data Preview
                          </h4>
                          {loadingDeleted ? (
                            <p
                              style={{
                                color: "#dc2626",
                                fontSize: "0.875rem",
                                margin: 0,
                              }}
                            >
                              Loading...
                            </p>
                          ) : deletedData && deletedData.length > 0 ? (
                            <div
                              style={{ overflow: "auto", maxHeight: "300px" }}
                            >
                              <table
                                style={{
                                  fontSize: "0.75rem",
                                  width: "100%",
                                  borderCollapse: "collapse",
                                }}
                              >
                                <thead>
                                  <tr style={{ background: "#fff" }}>
                                    {Object.keys(deletedData[0]).map((key) => (
                                      <th
                                        key={key}
                                        style={{
                                          padding: "8px 12px",
                                          textAlign: "left",
                                          borderBottom: "2px solid #fecaca",
                                          fontWeight: "600",
                                          color: "#991b1b",
                                        }}
                                      >
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {deletedData.map((row, idx) => (
                                    <tr
                                      key={idx}
                                      style={{
                                        background:
                                          idx % 2 === 0 ? "#fff" : "#fef2f2",
                                      }}
                                    >
                                      {Object.values(row).map((val, i) => (
                                        <td
                                          key={i}
                                          style={{
                                            padding: "8px 12px",
                                            borderBottom: "1px solid #fee2e2",
                                            color: "#7f1d1d",
                                          }}
                                        >
                                          {String(val)}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <p
                              style={{
                                color: "#dc2626",
                                fontSize: "0.875rem",
                                margin: 0,
                              }}
                            >
                              No deleted data found for this execution.
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Versions Tab - Professional Card Layout */}
          {activeTab === "versions" && (
            <div>
              <div className="status-bar" style={{ marginBottom: "20px" }}>
                {versionStatus}
              </div>

              {versions.length === 0 ? (
                <div
                  style={{
                    textAlign: "center",
                    padding: "60px 20px",
                    background: "#f9fafb",
                    borderRadius: "12px",
                    border: "2px dashed #d1d5db",
                  }}
                >
                  <svg
                    width="64"
                    height="64"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#9ca3af"
                    strokeWidth="1.5"
                    style={{ margin: "0 auto 16px" }}
                  >
                    <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                    <polyline points="17 21 17 13 7 13 7 21" />
                    <polyline points="7 3 7 8 15 8" />
                  </svg>
                  <p
                    style={{
                      color: "#6b7280",
                      fontSize: "1.1rem",
                      margin: "0 0 8px 0",
                    }}
                  >
                    {versionStatus.includes("Error") ||
                    versionStatus.includes("not configured")
                      ? versionStatus
                      : "No versions saved yet"}
                  </p>
                  <p
                    style={{
                      color: "#9ca3af",
                      fontSize: "0.9rem",
                      margin: "0",
                    }}
                  >
                    Save a version from the LLM Agent page to create a
                    checkpoint
                  </p>
                </div>
              ) : (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "16px",
                  }}
                >
                  {versions.map((version, index) => (
                    <div
                      key={index}
                      style={{
                        background: "#fff",
                        border: "1px solid #e5e7eb",
                        borderRadius: "12px",
                        padding: "20px",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
                        transition: "all 0.2s",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.boxShadow =
                          "0 4px 6px rgba(0,0,0,0.1)";
                        e.currentTarget.style.borderColor = "#10b981";
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.boxShadow =
                          "0 1px 3px rgba(0,0,0,0.05)";
                        e.currentTarget.style.borderColor = "#e5e7eb";
                      }}
                    >
                      <div style={{ flex: 1 }}>
                        <h3
                          style={{
                            margin: "0 0 8px 0",
                            fontSize: "1.1rem",
                            color: "#111827",
                            fontWeight: "600",
                          }}
                        >
                          {version.tool_details}
                        </h3>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                          }}
                        >
                          <span
                            style={{ fontSize: "0.875rem", color: "#6b7280" }}
                          >
                            {new Date(version.timestamp).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      <div
                        style={{
                          display: "flex",
                          gap: "12px",
                          alignItems: "center",
                        }}
                      >
                        <button
                          className="secondary-button"
                          onClick={() => handleRevert(version)}
                          style={{
                            fontSize: "0.875rem",
                            padding: "10px 20px",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            borderColor: "#10b981",
                            color: "#10b981",
                            fontWeight: "600",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#10b981";
                            e.currentTarget.style.color = "#fff";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "transparent";
                            e.currentTarget.style.color = "#10b981";
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
                            <polyline points="1 4 1 10 7 10" />
                            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                          </svg>
                          Revert
                        </button>

                        <button
                          className="secondary-button"
                          onClick={() => handleDeleteVersion(version)}
                          style={{
                            fontSize: "0.875rem",
                            padding: "10px 20px",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            borderColor: "#ef4444",
                            color: "#ef4444",
                            fontWeight: "600",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.background = "#ef4444";
                            e.currentTarget.style.color = "#fff";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.background = "transparent";
                            e.currentTarget.style.color = "#ef4444";
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
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                            <line x1="10" y1="11" x2="10" y2="17" />
                            <line x1="14" y1="11" x2="14" y2="17" />
                          </svg>
                          Delete
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LogsPage;
