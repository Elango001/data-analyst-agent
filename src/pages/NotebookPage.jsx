import React from 'react';

const NotebookPage = () => {
  return (
    <div className="page notebook-page">
      <h2>Notebook Workspace</h2>
      <p>
        This page is a visual placeholder for a future notebook-style workflow, similar
        to Databricks or Jupyter. You could add cells, charts, and SQL editors here.
      </p>
      <div className="notebook-mock">
        <div className="notebook-cell markdown"># Cleaning Experiment</div>
        <div className="notebook-cell code"># Code cell
print("Run cleaning pipeline...")</div>
        <div className="notebook-cell output">[Output] Cleaning summary...</div>
      </div>
    </div>
  );
};

export default NotebookPage;
