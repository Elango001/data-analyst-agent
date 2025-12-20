import React, { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

const VisualizationsPage = () => {
  const [visualizations, setVisualizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchVisualizations();
  }, []);

  const fetchVisualizations = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/tool-logs`);
      const data = await res.json();

      if (data.status === "success") {
        // Filter for visualization tools and extract visualizations
        const vizLogs = data.logs
          .filter(
            (log) =>
              log.action && log.action.startsWith("plot_") && log.tool_result
          )
          .map((log) => {
            try {
              const result =
                typeof log.tool_result === "string"
                  ? JSON.parse(log.tool_result)
                  : log.tool_result;

              return {
                id: log.id,
                timestamp: log.timestamp,
                action: log.action,
                explanation: log.cleaner_response || "No explanation provided",
                visualization: result.visualization || null,
                title:
                  result.title ||
                  log.action.replace("plot_", "").replace("_", " "),
                success: result.success || false,
                params: log.tool_args ? JSON.parse(log.tool_args) : {},
              };
            } catch (e) {
              console.error("Error parsing log:", e);
              return null;
            }
          })
          .filter((viz) => viz !== null && viz.visualization);

        setVisualizations(vizLogs);
      } else {
        setError(data.message || "Failed to load visualizations");
      }
    } catch (err) {
      console.error("Error fetching visualizations:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page visualizations-page">
        <div className="page-header">
          <h2>📊 Visualizations</h2>
          <p className="page-subtitle">Loading visualizations...</p>
        </div>
        <div
          className="loading-spinner"
          style={{ textAlign: "center", padding: "40px" }}
        >
          <svg
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="#10b981"
            strokeWidth="2"
            className="spinning-icon"
          >
            <path d="M21 12a9 9 0 1 1-6.219-8.56" />
          </svg>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page visualizations-page">
        <div className="page-header">
          <h2>📊 Visualizations</h2>
          <p className="page-subtitle">Error loading visualizations</p>
        </div>
        <div
          className="error-message"
          style={{
            padding: "20px",
            background: "#fee",
            border: "1px solid #fcc",
            borderRadius: "8px",
            margin: "20px",
          }}
        >
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="page visualizations-page">
      <div className="page-header">
        <h2>📊 Visualizations</h2>
        <p className="page-subtitle">
          View all generated visualizations with their explanations
        </p>
        <button
          className="secondary-button"
          onClick={fetchVisualizations}
          style={{ marginTop: "10px" }}
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
            <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
          </svg>
          Refresh
        </button>
      </div>

      <div className="visualizations-container" style={{ padding: "20px" }}>
        {visualizations.length === 0 ? (
          <div
            className="empty-state"
            style={{
              textAlign: "center",
              padding: "60px 20px",
              color: "#666",
            }}
          >
            <svg
              width="80"
              height="80"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#ccc"
              strokeWidth="1"
              style={{ margin: "0 auto 20px" }}
            >
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <h3 style={{ color: "#666", marginBottom: "10px" }}>
              No Visualizations Yet
            </h3>
            <p>
              Run the Visualizer Agent from the LLM Page to generate
              visualizations
            </p>
          </div>
        ) : (
          <div
            className="visualizations-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(500px, 1fr))",
              gap: "24px",
            }}
          >
            {visualizations.map((viz) => (
              <div
                key={viz.id}
                className="visualization-card"
                style={{
                  background: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  padding: "20px",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
                  transition: "all 0.2s",
                }}
              >
                <div className="viz-header" style={{ marginBottom: "16px" }}>
                  <h3
                    style={{
                      fontSize: "1.1rem",
                      fontWeight: "600",
                      color: "#111",
                      marginBottom: "8px",
                      textTransform: "capitalize",
                    }}
                  >
                    {viz.title}
                  </h3>
                  <div
                    style={{
                      fontSize: "0.875rem",
                      color: "#666",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                    }}
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <circle cx="12" cy="12" r="10" />
                      <polyline points="12 6 12 12 16 14" />
                    </svg>
                    {new Date(viz.timestamp).toLocaleString()}
                  </div>
                </div>

                {/* Tool Call Details */}
                <div
                  className="tool-call-info"
                  style={{
                    background: "#f9fafb",
                    padding: "12px",
                    borderRadius: "8px",
                    marginBottom: "16px",
                    fontSize: "0.875rem",
                  }}
                >
                  <div
                    style={{
                      fontWeight: "600",
                      color: "#10b981",
                      marginBottom: "6px",
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
                      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                    </svg>
                    {viz.action}
                  </div>
                  <div style={{ color: "#666" }}>
                    <strong>Parameters:</strong>
                    <pre
                      style={{
                        background: "white",
                        padding: "8px",
                        borderRadius: "4px",
                        marginTop: "4px",
                        fontSize: "0.8rem",
                        overflow: "auto",
                        border: "1px solid #e5e7eb",
                      }}
                    >
                      {JSON.stringify(viz.params, null, 2)}
                    </pre>
                  </div>
                </div>

                {/* Agent Explanation */}
                {viz.explanation && (
                  <div
                    className="explanation"
                    style={{
                      background: "#f0fdf4",
                      border: "1px solid #86efac",
                      padding: "12px",
                      borderRadius: "8px",
                      marginBottom: "16px",
                      fontSize: "0.875rem",
                    }}
                  >
                    <div
                      style={{
                        fontWeight: "600",
                        color: "#166534",
                        marginBottom: "6px",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z" />
                      </svg>
                      Agent Explanation
                    </div>
                    <div style={{ color: "#166534", lineHeight: "1.6" }}>
                      {viz.explanation}
                    </div>
                  </div>
                )}

                {/* Visualization Image */}
                <div
                  className="visualization-image"
                  style={{
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                    overflow: "hidden",
                    background: "white",
                  }}
                >
                  <img
                    src={`data:image/png;base64,${viz.visualization}`}
                    alt={viz.title}
                    style={{
                      width: "100%",
                      height: "auto",
                      display: "block",
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualizationsPage;
