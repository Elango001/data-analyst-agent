import React from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import HomePage from "../pages/HomePage";
import LlmPage from "../pages/LlmPage";
import NotebookPage from "../pages/NotebookPage";
import LogsPage from "../pages/LogsPage";

const AppShell = () => {
  return (
    <div className="app-shell">
      <header className="top-bar top-bar--full">
        <div className="brand">Data Analyst Agent Studio</div>
        <nav className="top-nav">
          <NavLink to="/" end className="top-nav-item">
            Home
          </NavLink>
          <NavLink to="/llm" className="top-nav-item">
            LLM Agent
          </NavLink>
          <NavLink to="/notebook" className="top-nav-item">
            Notebook
          </NavLink>
          <NavLink to="/logs" className="top-nav-item">
            Logs & Rollback
          </NavLink>
        </nav>
      </header>
      <main className="content-area content-area--full">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/llm" element={<LlmPage />} />
          <Route path="/notebook" element={<NotebookPage />} />
          <Route path="/logs" element={<LogsPage />} />
        </Routes>
      </main>
    </div>
  );
};

export default AppShell;
