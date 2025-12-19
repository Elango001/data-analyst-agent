import React from "react";

const HomePage = () => {
  return (
    <div className="page home-page">
      <section className="home-hero">
        <h1 className="home-hero-title">Intelligent Data Analysis Platform</h1>
        <p className="home-hero-subtitle">
          A multi-agent system for automated data cleaning, statistical
          analysis, and visualization. Built with advanced LLM capabilities and
          workflow orchestration for enterprise-grade data operations.
        </p>
        <div className="home-cta-row">
          <a href="/llm" className="primary-button">
            Launch Agent
          </a>
          <a href="/config" className="secondary-button">
            Configuration
          </a>
        </div>
        <p className="home-highlight">
          Agentic workflows • Real-time monitoring • Reproducible operations
        </p>
      </section>

      <section className="home-panels">
        <div className="card">
          <h3>Configuration</h3>
          <p>
            Configure LLM API keys and database credentials. Support for Gemini
            and PostgreSQL integration with secure credential management.
          </p>
        </div>
        <div className="card">
          <h3>Agent Interface</h3>
          <p>
            Execute multi-step workflows with specialized agents for data
            cleaning, analysis, and visualization. Stream tool calls and agent
            responses in real-time.
          </p>
        </div>
        <div className="card">
          <h3>Workspace</h3>
          <p>
            Interactive environment for exploratory data analysis and custom
            workflows. Supports direct data manipulation and agent-assisted
            operations.
          </p>
        </div>
        <div className="card">
          <h3>Rollback System</h3>
          <p>
            Version control for data operations. Browse execution history with
            structured parameters and restore previous states on demand.
          </p>
        </div>
        <div className="card">
          <h3>Deleted Data</h3>
          <p>
            Audit trail for all data removal operations. Track deleted records
            by tool execution with complete transparency and recovery
            capabilities.
          </p>
        </div>
        <div className="card">
          <h3>System Logs</h3>
          <p>
            Comprehensive logging of agent activities and tool executions.
            Monitor system performance and debug workflow issues.
          </p>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
