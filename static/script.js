// API Base URL
const API_BASE = window.location.origin;

// Model options for each provider
const models = {
  gemini: ["gemini-2.0-flash", "gemini-2.5-flash"],
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

    const cleanResponse = await fetch(`${API_BASE}/clean`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const cleanResult = await cleanResponse.json();

    if (cleanResponse.ok) {
      showStatus("✓ Data cleaning completed successfully!", "success");
      console.log("Cleaning result:", cleanResult);
    } else {
      showStatus(cleanResult.detail || "Cleaning failed", "error");
    }
  } catch (error) {
    showStatus("Error: " + error.message, "error");
  }
});
