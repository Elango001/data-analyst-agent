import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

const DeletedDataPage = () => {
  const [logs, setLogs] = useState([]);
  const [selectedToolId, setSelectedToolId] = useState(null);
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const loadLogs = async () => {
      setStatus("Loading tool logs...");
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
            ? `Loaded ${data.logs.length} tool execution(s)`
            : "No tool executions found"
        );
      } catch (err) {
        console.error("Logs error:", err);
        setStatus(`Error: ${err.message}`);
        setLogs([]);
      }
    };
    loadLogs();
  }, []);

  const loadDeletedData = async (toolId) => {
    setSelectedToolId(toolId);
    setStatus("Loading deleted data...");
    setRows([]);

    try {
      const res = await fetch(`${API_BASE}/deleted-data/${toolId}`);

      // Check if response is ok before parsing JSON
      if (!res.ok) {
        const errorText = await res.text();
        let errorMsg = "Failed to load deleted data";
        try {
          const errorData = JSON.parse(errorText);
          errorMsg = errorData.detail || errorMsg;
        } catch {
          errorMsg = errorText || errorMsg;
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      setRows(data.data || []);
      setStatus(
        data.data && data.data.length > 0
          ? `Loaded ${data.count || 0} deleted row(s)`
          : "No deleted data for this tool execution"
      );
    } catch (err) {
      console.error("Deleted data error:", err);
      setStatus(`Error: ${err.message}`);
      setRows([]);
    }
  };

  return (
    <div className="page deleted-data-page">
      <div className="page-header-compact">
        <h2>Deleted Data</h2>
        <div className="status-bar">{status}</div>
      </div>
      <div className="two-column">
        <div className="card">
          <h3>Tool Executions</h3>
          <ul className="list">
            {logs.map((log) => (
              <li key={log.id}>
                <button
                  className={
                    "link-button" + (selectedToolId === log.id ? " active" : "")
                  }
                  onClick={() => loadDeletedData(log.id)}
                >
                  #{log.id} - {log.tool_name}
                </button>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h3>Deleted Rows</h3>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  {rows[0] &&
                    Object.keys(rows[0]).map((col) => <th key={col}>{col}</th>)}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => (
                  <tr key={idx}>
                    {Object.keys(row).map((col) => (
                      <td key={col}>{String(row[col])}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeletedDataPage;
