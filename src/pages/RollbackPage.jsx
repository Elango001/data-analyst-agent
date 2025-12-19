import React, { useEffect, useState } from "react";

const API_BASE = "";

const RollbackPage = () => {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState("");

  useEffect(() => {
    const load = async () => {
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
    load();
  }, []);

  const handleRollback = (tool) => {
    // Placeholder: actual rollback endpoint not yet defined
    alert(`Rollback requested for tool: ${tool.tool_name || tool.tool}`);
  };

  return (
    <div className="page rollback-page">
      <h2>Rollback Tools</h2>
      <p>
        Inspect executed tools and trigger rollbacks. Each entry is displayed as
        <code>{"{tool: name, params: {...}}"}</code> with a revert button.
      </p>
      <div className="status-bar">{status}</div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Timestamp</th>
              <th>Tool</th>
              <th>Params</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => {
              let parsed = null;
              try {
                // tool_name is often a stringified dict in the backend example
                parsed =
                  typeof log.tool_name === "string"
                    ? JSON.parse(log.tool_name.replace(/'/g, '"'))
                    : log.tool_name;
              } catch {
                parsed = { tool: log.tool_name, params: {} };
              }

              const toolName = parsed?.tool || parsed?.name || log.tool_name;
              const params = parsed?.params || parsed || {};

              return (
                <tr key={log.id}>
                  <td>{log.id}</td>
                  <td>{log.timestamp}</td>
                  <td>{toolName}</td>
                  <td>
                    <pre>{JSON.stringify(params, null, 2)}</pre>
                  </td>
                  <td>
                    <button
                      className="secondary-button"
                      onClick={() =>
                        handleRollback({ ...log, tool_name: toolName, params })
                      }
                    >
                      Revert
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RollbackPage;
