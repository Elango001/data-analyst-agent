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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" style={{ marginRight: '6px', display: 'inline-block', verticalAlign: 'middle' }}>
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <polyline points="2 17 12 22 22 17" />
              <polyline points="2 12 12 17 22 12" />
            </svg>
            Launch Agent
          </a>
        </div>
        <p className="home-highlight">
          Agentic workflows • Real-time monitoring • Reproducible operations
        </p>
      </section>

      <section className="home-panels">
        <div className="card">
          <h3>Agent Interface</h3>
          <p>
            Execute multi-step workflows with specialized agents for data
            cleaning, analysis, and visualization. Stream tool calls and agent
            responses in real-time. Configure LLM and database settings directly from the interface.
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
