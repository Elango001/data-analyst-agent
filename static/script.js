// API Base URL
const API_BASE = window.location.origin;

// Model options for each provider
const models = {
  google: [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemma-3-27b",
    "gemini-2.5-flash-lite",
  ],
  openai: ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
  claude: [
    "claude-3-5-sonnet-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
  ],
};

// Store configuration
let modelConfig = {
  provider: "",
  modelName: "",
  apiKey: "",
};

// Modal Elements
const configModal = document.getElementById("configModal");
const configBtn = document.getElementById("configBtn");
const closeModal = document.getElementById("closeModal");
const cancelBtn = document.getElementById("cancelBtn");
const saveConfigBtn = document.getElementById("saveConfigBtn");
const providerSelect = document.getElementById("providerSelect");
const modelSelect = document.getElementById("modelSelect");

// Handle provider change
providerSelect.addEventListener("change", () => {
  const selectedProvider = providerSelect.value;

  // Clear model select
  modelSelect.innerHTML = '<option value="">-- Select Model --</option>';

  if (selectedProvider && models[selectedProvider]) {
    models[selectedProvider].forEach((model) => {
      const option = document.createElement("option");
      option.value = model;
      option.textContent = model;
      modelSelect.appendChild(option);
    });
  }

  // Reset model select if provider changed
  modelSelect.value = "";
});

// Open modal
configBtn.addEventListener("click", () => {
  configModal.classList.add("active");
  // Pre-fill if already configured
  providerSelect.value = modelConfig.provider;
  if (modelConfig.provider && models[modelConfig.provider]) {
    modelSelect.innerHTML = '<option value="">-- Select Model --</option>';
    models[modelConfig.provider].forEach((model) => {
      const option = document.createElement("option");
      option.value = model;
      option.textContent = model;
      modelSelect.appendChild(option);
    });
    modelSelect.value = modelConfig.modelName;
  }
  document.getElementById("modalApiKey").value = modelConfig.apiKey;
});

// Close modal functions
function closeConfigModal() {
  configModal.classList.remove("active");
}

closeModal.addEventListener("click", closeConfigModal);
cancelBtn.addEventListener("click", closeConfigModal);

// Close modal when clicking outside
window.addEventListener("click", (e) => {
  if (e.target === configModal) {
    closeConfigModal();
  }
});

// Save configuration
saveConfigBtn.addEventListener("click", async () => {
  const provider = providerSelect.value.trim();
  const modelName = modelSelect.value.trim();
  const apiKey = document.getElementById("modalApiKey").value.trim();

  if (!provider) {
    alert("Please select a provider");
    return;
  }

  if (!modelName) {
    alert("Please select a model");
    return;
  }

  if (!apiKey) {
    alert("Please enter API key");
    return;
  }

  // Validate API key by making a request
  saveConfigBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/configure`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        provider: provider,
        model_name: modelName,
        api_key: apiKey,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      alert(result.detail || "Configuration failed");
      return;
    }

    // Configuration successful, save to local config
    modelConfig.provider = provider;
    modelConfig.modelName = modelName;
    modelConfig.apiKey = apiKey;

    alert("✓ Configuration saved successfully!");
    closeConfigModal();
  } catch (error) {
    alert("Error: " + error.message);
  } finally {
    saveConfigBtn.disabled = false;
  }
});

// Submit button handler for file upload
document.getElementById("submitBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("csvFile");

  // Validate configuration
  if (!modelConfig.modelName) {
    showStatus(
      'Please configure model first by clicking "Configure Model" button',
      "error"
    );
    return;
  }

  if (!modelConfig.apiKey) {
    showStatus(
      'Please configure model first by clicking "Configure Model" button',
      "error"
    );
    return;
  }

  if (!fileInput.files.length) {
    showStatus("Please select a CSV file", "error");
    return;
  }

  // Step 1: Configure API
  showStatus("Configuring...", "loading");

  try {
    const configResponse = await fetch(`${API_BASE}/configure`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        provider: modelConfig.provider,
        model_name: modelConfig.modelName,
        api_key: modelConfig.apiKey,
      }),
    });

    const configResult = await configResponse.json();

    if (!configResponse.ok) {
      showStatus(configResult.detail || "Configuration failed", "error");
      return;
    }

    // Step 2: Upload file
    showStatus("Uploading dataset...", "loading");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const uploadResponse = await fetch(`${API_BASE}/upload`, {
      method: "POST",
      body: formData,
    });

    const uploadResult = await uploadResponse.json();

    if (uploadResponse.ok) {
      showStatus(
        `✓ Success! Uploaded ${uploadResult.rows} rows, ${uploadResult.columns} columns`,
        "success"
      );
    } else {
      showStatus(uploadResult.detail || "Upload failed", "error");
    }
  } catch (error) {
    showStatus("Error: " + error.message, "error");
  }
});

// Helper function to show status messages
function showStatus(message, type) {
  const statusEl = document.getElementById("status");
  statusEl.textContent = message;
  statusEl.className = `status ${type}`;
}

// Start Cleaning button handler
document.getElementById("cleanBtn").addEventListener("click", async () => {
  // Check if configured
  if (!modelConfig.modelName || !modelConfig.apiKey) {
    showStatus(
      'Please configure model first by clicking "Configure Model" button',
      "error"
    );
    return;
  }

  try {
    showStatus("Starting data cleaning process...", "loading");

    // Hide welcome message and show data preview
    const welcomeMessage = document.getElementById("welcomeMessage");
    const dataPreview = document.getElementById("dataPreview");
    const chatMessages = document.getElementById("chatMessages");

    // Create EventSource for SSE
    const eventSource = new EventSource(`${API_BASE}/clean`);

    let lastState = null;

    // Listen for messages
    eventSource.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);

        // Only show cleaner node messages
        if (data.node === "cleaner_node") {
          // Add agent message if available
          if (data.last_message) {
            addChatMessage("agent", data.last_message);
          }

          // Show tool calls if available
          if (data.tool_call && data.tool_call.length > 0) {
            addToolCallMessage(data.tool_call);
          }

          // Update data preview (20 rows) in main area
          if (data.summary && data.summary.data_preview) {
            displayDataTable(data.summary.data_preview);
            welcomeMessage.style.display = "none";
            dataPreview.style.display = "block";
            lastState = data.summary; // Save for final display
          }
        }
      } catch (error) {
        console.error("Error parsing event:", error);
      }
    });

    // Handle errors (connection close)
    eventSource.addEventListener("error", (error) => {
      eventSource.close();

      if (lastState) {
        // Finalize - mark as completed
        showStatus("✓ Data cleaning completed!", "success");
        addChatMessage(
          "system",
          "✅ Data cleaning process completed successfully!"
        );
      } else {
        showStatus("Error during cleaning process", "error");
        addChatMessage("system", "❌ Error occurred during cleaning process.");
        welcomeMessage.style.display = "block";
        dataPreview.style.display = "none";
      }
    });
  } catch (error) {
    showStatus("Error: " + error.message, "error");
    addChatMessage("system", `❌ Error: ${error.message}`);
  }
});

// Function to add chat messages
function addChatMessage(type, content) {
  const chatMessages = document.getElementById("chatMessages");

  const messageDiv = document.createElement("div");
  messageDiv.className = `chat-message ${type}`;

  let label = "";
  if (type === "agent") {
    label = '<div class="message-label">🤖 Agent</div>';
  } else if (type === "system") {
    label = '<div class="message-label">ℹ️ System</div>';
  }

  messageDiv.innerHTML = `
    ${label}
    <div class="message-content">${escapeHtml(content)}</div>
  `;

  chatMessages.appendChild(messageDiv);

  // Auto-scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Function to add tool call messages
function addToolCallMessage(toolCalls) {
  const chatMessages = document.getElementById("chatMessages");

  const messageDiv = document.createElement("div");
  messageDiv.className = "chat-message tool";

  let toolsHtml =
    '<div class="message-label">🔧 Tool Calls</div><div class="message-content">';

  toolCalls.forEach((call, index) => {
    toolsHtml += `
      <div class="tool-call-item">
        <strong>Tool ${index + 1}: ${call.tool}</strong>
        <code>${JSON.stringify(call.params, null, 2)}</code>
      </div>
    `;
  });

  toolsHtml += "</div>";
  messageDiv.innerHTML = toolsHtml;

  chatMessages.appendChild(messageDiv);

  // Auto-scroll to bottom
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Helper function to escape HTML
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Function to display data table (20 rows)
function displayDataTable(dataPreview) {
  const tableHead = document.getElementById("tableHead");
  const tableBody = document.getElementById("tableBody");

  // Clear previous data
  tableHead.innerHTML = "";
  tableBody.innerHTML = "";

  if (!dataPreview || dataPreview.length === 0) {
    tableBody.innerHTML = '<tr><td colspan="100%">No data available</td></tr>';
    return;
  }

  // Get column names from first row
  const columns = Object.keys(dataPreview[0]);

  // Build table header
  const headerRow = document.createElement("tr");
  columns.forEach((col) => {
    const th = document.createElement("th");
    th.textContent = col;
    headerRow.appendChild(th);
  });
  tableHead.appendChild(headerRow);

  // Build table rows (max 20 rows)
  const rowsToShow = dataPreview.slice(0, 20);
  rowsToShow.forEach((row) => {
    const tr = document.createElement("tr");
    columns.forEach((col) => {
      const td = document.createElement("td");
      const value = row[col];
      // Handle null/undefined
      td.textContent = value !== null && value !== undefined ? value : "";
      tr.appendChild(td);
    });
    tableBody.appendChild(tr);
  });
}

// Clear chat button
document.getElementById("clearChat").addEventListener("click", () => {
  const chatMessages = document.getElementById("chatMessages");
  const welcomeMessage = document.getElementById("welcomeMessage");
  const dataPreview = document.getElementById("dataPreview");

  chatMessages.innerHTML = `
    <div class="chat-message system">
      <div class="message-content">
        👋 Chat cleared. Upload a dataset and click "Start Cleaning" to begin.
      </div>
    </div>
  `;

  // Reset to welcome state
  welcomeMessage.style.display = "flex";
  dataPreview.style.display = "none";
});
