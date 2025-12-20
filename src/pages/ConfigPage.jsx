import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

// Model configurations for different providers
const MODEL_OPTIONS = {
  google: [
    { value: "gemini-2.0-flash-exp", label: "Gemini 2.0 Flash (Experimental)" },
    { value: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
    { value: "gemini-1.5-flash-8b", label: "Gemini 1.5 Flash-8B" },
    { value: "gemini-1.5-pro", label: "Gemini 1.5 Pro" },
    { value: "gemini-1.0-pro", label: "Gemini 1.0 Pro" },
  ],
  openai: [
    { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
    { value: "gpt-4", label: "GPT-4" },
    { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
  ],
  anthropic: [
    { value: "claude-3-opus", label: "Claude 3 Opus" },
    { value: "claude-3-sonnet", label: "Claude 3 Sonnet" },
    { value: "claude-3-haiku", label: "Claude 3 Haiku" },
  ],
};

const PROVIDER_OPTIONS = [
  { value: "google", label: "Google Gemini" },
  { value: "openai", label: "OpenAI" },
  { value: "anthropic", label: "Anthropic" },
];

const DB_OPTIONS = [
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mongodb", label: "MongoDB" },
  { value: "mysql", label: "MySQL" },
];

const ConfigPage = () => {
  // Load from localStorage
  const [provider, setProvider] = useState(() => {
    return localStorage.getItem("llm_provider") || "google";
  });
  const [modelName, setModelName] = useState(() => {
    return localStorage.getItem("llm_model") || "gemini-2.0-flash-exp";
  });
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem("llm_api_key") || "";
  });
  const [dbType, setDbType] = useState("postgresql");
  const [csvFile, setCsvFile] = useState(null);
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
  const [status, setStatus] = useState("");

  // Save to localStorage whenever config changes
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

  useEffect(() => {
    localStorage.setItem("db_config", JSON.stringify(db));
  }, [db]);

  // Clear all storage when the window/tab is closed or refreshed
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      // Clear all localStorage data
      localStorage.removeItem("llm_provider");
      localStorage.removeItem("llm_model");
      localStorage.removeItem("llm_api_key");
      localStorage.removeItem("db_config");

      // Clear all sessionStorage data
      sessionStorage.clear();
    };

    // Add event listener for beforeunload (triggered when closing/refreshing)
    window.addEventListener("beforeunload", handleBeforeUnload);

    // Cleanup: Remove event listener when component unmounts
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, []);

  const handleProviderChange = (newProvider) => {
    if (newProvider !== "google") {
      setStatus(
        "⚠️ Only Google Gemini is currently supported. Other providers are not yet developed."
      );
      return;
    }
    setProvider(newProvider);
    // Set default model for the selected provider
    if (MODEL_OPTIONS[newProvider] && MODEL_OPTIONS[newProvider].length > 0) {
      setModelName(MODEL_OPTIONS[newProvider][0].value);
    }
  };

  const handleDbTypeChange = (newDbType) => {
    if (newDbType !== "postgresql") {
      setStatus(
        "⚠️ Only PostgreSQL is currently supported. MongoDB and MySQL are not yet developed."
      );
      setDbType("postgresql");
      return;
    }
    setDbType(newDbType);
    // Update default port based on database type
    const defaultPorts = {
      postgresql: 5432,
      mongodb: 27017,
      mysql: 3306,
    };
    setDb({ ...db, port: defaultPorts[newDbType] || 5432 });
  };

  const handleConfigureLLM = async (e) => {
    e.preventDefault();

    // Check if provider is supported
    if (provider !== "google") {
      setStatus("⚠️ Only Google Gemini is currently supported.");
      return;
    }

    setStatus("Configuring LLM...");
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
      setStatus(`✓ ${data.message}`);
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
  };

  const handleConfigureDb = async (e) => {
    e.preventDefault();

    // Check if database type is supported
    if (dbType !== "postgresql") {
      setStatus("⚠️ Only PostgreSQL is currently supported.");
      return;
    }

    setStatus("Configuring database...");
    try {
      const res = await fetch(`${API_BASE}/configure-db`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...db, type: dbType }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to configure DB");
      setStatus(`✓ ${data.message}`);
    } catch (err) {
      setStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div className="page config-page">
      <div className="config-header">
        <h2>System Configuration</h2>
        <p className="config-subtitle">
          Configure your LLM provider and database connection settings
        </p>
      </div>

      <div className="config-grid">
        <section className="config-card">
          <div className="config-card-header">
            <h3>LLM Configuration</h3>
            <span className="config-badge">Required</span>
          </div>
          <form onSubmit={handleConfigureLLM} className="config-form">
            <div className="form-group">
              <label htmlFor="provider">Provider</label>
              <select
                id="provider"
                className="form-select"
                value={provider}
                onChange={(e) => handleProviderChange(e.target.value)}
              >
                {PROVIDER_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="model">Model</label>
              <select
                id="model"
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
              <label htmlFor="apiKey">API Key</label>
              <input
                id="apiKey"
                type="password"
                className="form-input"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your API key"
              />
            </div>

            <button type="submit" className="primary-button full-width">
              Save LLM Configuration
            </button>
          </form>
        </section>

        <section className="config-card">
          <div className="config-card-header">
            <h3>Database Configuration</h3>
            <span className="config-badge">Required</span>
          </div>
          <form onSubmit={handleConfigureDb} className="config-form">
            <div className="form-group">
              <label htmlFor="dbType">Database Type</label>
              <select
                id="dbType"
                className="form-select"
                value={dbType}
                onChange={(e) => handleDbTypeChange(e.target.value)}
              >
                {DB_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="host">Host</label>
                <input
                  id="host"
                  className="form-input"
                  value={db.host}
                  onChange={(e) => setDb({ ...db, host: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="port">Port</label>
                <input
                  id="port"
                  type="number"
                  className="form-input"
                  value={db.port}
                  onChange={(e) =>
                    setDb({ ...db, port: parseInt(e.target.value, 10) || 5432 })
                  }
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="database">Database Name</label>
              <input
                id="database"
                className="form-input"
                value={db.database}
                onChange={(e) => setDb({ ...db, database: e.target.value })}
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="user">Username</label>
                <input
                  id="user"
                  className="form-input"
                  value={db.user}
                  onChange={(e) => setDb({ ...db, user: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input
                  id="password"
                  type="password"
                  className="form-input"
                  value={db.password}
                  onChange={(e) => setDb({ ...db, password: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="csvFile">
                CSV File (for deleted data storage)
              </label>
              <div className="file-upload-wrapper">
                <input
                  id="csvFile"
                  type="file"
                  accept=".csv"
                  className="file-input"
                  onChange={(e) => {
                    const file = e.target.files[0];
                    if (file) {
                      setCsvFile(file);
                      setDb({ ...db, csv_path: file.name });
                    }
                  }}
                />
                <label htmlFor="csvFile" className="file-upload-label">
                  {csvFile ? csvFile.name : "Choose CSV file or use default"}
                </label>
              </div>
              <small className="form-hint">
                Optional: Upload a CSV file or leave blank to use default path
              </small>
            </div>

            <button type="submit" className="primary-button full-width">
              Save Database Configuration
            </button>
          </form>
        </section>
      </div>

      {status && (
        <div
          className={`status-message ${
            status.startsWith("✓")
              ? "success"
              : status.startsWith("Error")
              ? "error"
              : ""
          }`}
        >
          {status}
        </div>
      )}
    </div>
  );
};

export default ConfigPage;
