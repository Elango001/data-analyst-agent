/* ================= NAVBAR ================= */
document.querySelector(".navbar").innerHTML = `
  <div class="nav-left">🧠 Data Analyst Agent</div>
  <div class="nav-right">
    <button onclick="go('config')">Configuration</button>
    <button onclick="go('workspace')">Workspace</button>
    <button onclick="go('logs')">Logs</button>
    <button onclick="go('rollback')">Rollback</button>
    <button onclick="go('deleted')">Deleted Data</button>
  </div>
`;

/* ================= CHAT ================= */
document.querySelector(".chat-panel").innerHTML = `
  <div class="chat-header">
    🤖 Agent Chat
    <button class="clear-chat" onclick="clearChat()">Clear</button>
  </div>

  <div class="chat-body" id="chatBody">
    <div class="chat agent">Hello! I'm your data cleaning agent. 
    Upload a dataset and click "Start Cleaning" to begin.</div>
  </div>

  // <div class="chat-input">
  //   <input id="chatInput" placeholder="Type your message..." />
  //   <button onclick="sendChat()">Send</button>
  // </div>
`;

window.sendChat = () => {
  const input = document.getElementById("chatInput");
  if (!input.value.trim()) return;

  const chatBody = document.getElementById("chatBody");

  chatBody.innerHTML += `<div class="chat user">${input.value}</div>`;
  chatBody.innerHTML += `<div class="chat agent">Processing...</div>`;

  input.value = "";
  chatBody.scrollTop = chatBody.scrollHeight;
};

window.clearChat = () => {
  document.getElementById("chatBody").innerHTML =
    `<div class="chat agent">Chat cleared. How can I help again?</div>`;
};

/* ================= PAGES ================= */
const pages = {
  config: `
    <h2>Configuration</h2>

    <div class="card">
      <h3>Model Configuration</h3>

      <label>Provider</label>
      <select onchange="selectProvider(this.value)">
        <option value="">Select Provider</option>
        <option value="google">Google</option>
        <option value="chatgpt">ChatGPT</option>
      </select>

      <div id="model-box"></div>
      <div id="api-box"></div>
    </div>

    <div class="card">
      <h3>Database Configuration</h3>

      <label>Database</label>
      <select onchange="selectDB(this.value)">
        <option value="">Select Database</option>
        <option value="postgres">PostgreSQL</option>
        <option value="mongo">MongoDB</option>
      </select>

      <div id="db-credentials"></div>
    </div>

    <button class="btn primary">Save Configuration</button>
  `,

  workspace: `
    <h2>LLM Workspace</h2>
    <div class="card">
      <p>Agent execution, tool calls, and outputs will appear here.</p>
    </div>
  `,

  logs: `
    <h2>Logs</h2>
    <div class="card"><pre>System initialized successfully...</pre></div>
  `,

  rollback: `
    <h2>Rollback</h2>
    <div class="card">
      <p>{ tool: "normalize", params: {} } <button>Revert</button></p>
    </div>
  `,

  deleted: `
    <h2>Deleted Data</h2>
    <div class="card">
      <p>Deleted rows and datasets will be shown here.</p>
    </div>
  `
};

window.go = (page) => {
  document.getElementById("content").innerHTML = pages[page];
};

/* ================= CONFIG LOGIC ================= */
window.selectProvider = (provider) => {
  const modelBox = document.getElementById("model-box");
  const apiBox = document.getElementById("api-box");

  modelBox.innerHTML = "";
  apiBox.innerHTML = "";

  if (!provider) return;

  modelBox.innerHTML = `
    <label>Model</label>
    <select onchange="showApiKey()">
      <option value="">Select Model</option>
      ${provider === "google"
        ? `<option>Gemini Pro</option><option>Gemini Lite</option>`
        : `<option>GPT-4</option><option>GPT-3.5</option>`}
    </select>
  `;
};

window.showApiKey = () => {
  document.getElementById("api-box").innerHTML = `
    <label>API Key</label>
    <input type="password" placeholder="Enter API Key" />
  `;
};

window.selectDB = (db) => {
  const box = document.getElementById("db-credentials");
  if (!db) return (box.innerHTML = "");

  box.innerHTML = `
    <label>Host</label>
    <input placeholder="localhost">

    <label>Port</label>
    <input placeholder="${db === "postgres" ? "5432" : "27017"}">

    <label>Username</label>
    <input>

    <label>Password</label>
    <input type="password">
  `;
};

/* ================= DEFAULT PAGE ================= */
go("config");
