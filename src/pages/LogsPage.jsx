import React, { useEffect, useState } from "react";

const API_BASE = "";

const LogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState("");
  const [selectedLog, setSelectedLog] = useState(null);
  const [deletedData, setDeletedData] = useState(null);
  const [loadingDeleted, setLoadingDeleted] = useState(false);

  useEffect(() => {
    const load = async () => {
      setStatus("Loading logs...");
      try {
        const res = await fetch(`${API_BASE}/tool-logs`);

        const data = await res.json();

        // Check if there's an error or warning in the response
        if (data.status === "error" || data.status === "warning") {
          setStatus(data.message || "Failed to load logs");
          setLogs([]);
          return;
        }

        setLogs(data.logs || []);
        setStatus(
          data.message ||
          (data.logs && data.logs.length > 0
            ? `Loaded ${data.logs.length} log(s)`
            : "No logs found")
        );
      } catch (err) {
        console.error("Logs error:", err);
        setStatus(`Error: ${err.message}`);
        setLogs([]);
      }
    };
    load();
  }, []);

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

  const handleRollback = async (log) => {
    if (!log.deleted_data) {
      alert("No deleted data available for this tool execution.");
      return;
    }

    if (!confirm(`Are you sure you want to rollback tool execution #${log.id} (${log.tool_name})? This will restore the deleted data.`)) {
      return;
    }

    // TODO: Implement actual rollback endpoint
    alert(`Rollback functionality for tool execution #${log.id} is not yet implemented.\n\nThis would restore the deleted data from this operation.`);
  };

  return (
    <div className="page logs-page">
      <div className="page-header-compact">
        <h2>Tool Execution Logs & Rollback</h2>
        <p style={{ margin: '8px 0 0 0', color: '#666', fontSize: '0.9rem' }}>
          View all tool executions and rollback changes when needed
        </p>
        <div className="status-bar">{status}</div>
      </div>
      <div className="table-wrapper">
        <table className="logs-table">
          <colgroup>
            <col style={{ width: "60px" }} />
            <col style={{ width: "180px" }} />
            <col style={{ width: "auto" }} />
            <col style={{ width: "100px" }} />
            <col style={{ width: "200px" }} />
          </colgroup>
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Tool</th>
              <th>Deleted Data?</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {logs.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
                  {status.includes('Error') || status.includes('not configured')
                    ? status
                    : 'No logs available yet. Run the agent to see execution logs.'}
                </td>
              </tr>
            ) : (
              logs.map((log) => (
                <React.Fragment key={log.id}>
                  <tr>
                    <td>{log.id}</td>
                    <td>{new Date(log.timestamp).toLocaleString()}</td>
                    <td>{log.tool_name}</td>
                    <td>
                      <span style={{
                        color: log.deleted_data ? '#dc2626' : '#666',
                        fontWeight: log.deleted_data ? '600' : 'normal'
                      }}>
                        {log.deleted_data ? "Yes" : "No"}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        {log.deleted_data && (
                          <>
                            <button
                              className="secondary-button"
                              onClick={() => handleViewDeleted(log.id)}
                              style={{ fontSize: '0.75rem', padding: '6px 12px' }}
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2" style={{ marginRight: '4px' }}>
                                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                                <circle cx="12" cy="12" r="3" />
                              </svg>
                              {selectedLog === log.id ? 'Hide' : 'View'}
                            </button>
                            <button
                              className="secondary-button"
                              onClick={() => handleRollback(log)}
                              style={{
                                fontSize: '0.75rem',
                                padding: '6px 12px',
                                borderColor: '#dc2626',
                                color: '#dc2626'
                              }}
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2" style={{ marginRight: '4px' }}>
                                <polyline points="1 4 1 10 7 10" />
                                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                              </svg>
                              Rollback
                            </button>
                          </>
                        )}
                        {!log.deleted_data && (
                          <span style={{ fontSize: '0.75rem', color: '#999', padding: '6px 0' }}>
                            No action available
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                  {selectedLog === log.id && (
                    <tr>
                      <td colSpan="5" style={{ padding: '0', background: '#fafafa' }}>
                        <div style={{ padding: '16px', borderTop: '1px solid #eaeaea' }}>
                          <h4 style={{ margin: '0 0 12px 0', fontSize: '0.875rem', color: '#333' }}>
                            Deleted Data Preview
                          </h4>
                          {loadingDeleted ? (
                            <p style={{ color: '#666', fontSize: '0.875rem' }}>Loading...</p>
                          ) : deletedData && deletedData.length > 0 ? (
                            <div style={{ overflow: 'auto', maxHeight: '300px' }}>
                              <table style={{ fontSize: '0.75rem', width: '100%' }}>
                                <thead>
                                  <tr style={{ background: '#fff' }}>
                                    {Object.keys(deletedData[0]).map((key) => (
                                      <th key={key} style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #eaeaea' }}>
                                        {key}
                                      </th>
                                    ))}
                                  </tr>
                                </thead>
                                <tbody>
                                  {deletedData.map((row, idx) => (
                                    <tr key={idx}>
                                      {Object.values(row).map((val, i) => (
                                        <td key={i} style={{ padding: '8px', borderBottom: '1px solid #f0f0f0' }}>
                                          {String(val)}
                                        </td>
                                      ))}
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <p style={{ color: '#999', fontSize: '0.875rem' }}>
                              No deleted data found for this execution.
                            </p>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default LogsPage;
