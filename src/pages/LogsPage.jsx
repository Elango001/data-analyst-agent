import React, { useEffect, useState } from "react";

const API_BASE = "";

const LogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const load = async () => {
      setStatus("Loading logs...");
      try {
        const res = await fetch(`${API_BASE}/tool-logs`);

        // Check if response is ok before parsing JSON
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
            ? `Loaded ${data.logs.length} log(s)`
            : "No logs found"
        );
      } catch (err) {
        console.error("Logs error:", err);
        setStatus(`Error: ${err.message}`);
        setLogs([]);
      }
    };
    load();
  }, []);

  return (
    <div className="page logs-page">
      <div className="page-header-compact">
        <h2>Agent & Tool Logs</h2>
        <div className="status-bar">{status}</div>
      </div>
      <div className="table-wrapper">
        <table className="logs-table">
          <colgroup>
            <col style={{ width: "60px" }} />
            <col style={{ width: "180px" }} />
            <col style={{ width: "auto" }} />
            <col style={{ width: "100px" }} />
          </colgroup>
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Tool</th>
              <th>Deleted Data?</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td>{log.id}</td>
                <td>{log.timestamp}</td>
                <td>{log.tool_name}</td>
                <td>{log.deleted_data ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default LogsPage;
