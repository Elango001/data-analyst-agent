# Frontend-Backend Integration Guide

## Backend API Endpoints

### 1. **Configure Database** 
**POST** `/configure-db`

Configure PostgreSQL and CSV for deleted data tracking.

```json
{
  "host": "localhost",
  "database": "preprocessing_logs",
  "user": "postgres",
  "password": "your_password",
  "port": 5432,
  "csv_path": "deleted_data.csv"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Database configured successfully"
}
```

### 2. **Get Tool Logs**
**GET** `/tool-logs`

Get all tool execution logs from PostgreSQL.

**Response:**
```json
{
  "status": "success",
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-12-18T17:14:48.229126",
      "tool_name": "{'tool': 'remove_outliers', 'column': 'FWI', 'strategy': 'iqr'}",
      "deleted_data": true
    }
  ]
}
```

### 3. **Get Deleted Data**
**GET** `/deleted-data/{tool_id}`

Retrieve deleted rows for a specific tool execution.

**Response:**
```json
{
  "status": "success",
  "data": [
    {"col1": "value1", "col2": "value2"},
    {"col1": "value3", "col2": "value4"}
  ],
  "count": 2
}
```

## Frontend Integration Steps

### 1. Add DB Configuration UI

Create a form to configure database connection:

```javascript
async function configureDatabase(dbConfig) {
  const response = await fetch('/configure-db', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dbConfig)
  });
  return await response.json();
}
```

### 2. Display Tool Execution History

Fetch and display all tool logs:

```javascript
async function fetchToolLogs() {
  const response = await fetch('/tool-logs');
  const data = await response.json();
  
  // Display logs in UI
  data.logs.forEach(log => {
    console.log(`Tool: ${log.tool_name}`);
    console.log(`Has deleted data: ${log.deleted_data}`);
  });
}
```

### 3. View Deleted Data

Allow users to view deleted data for specific tool executions:

```javascript
async function viewDeletedData(toolId) {
  const response = await fetch(`/deleted-data/${toolId}`);
  const data = await response.json();
  
  if (data.data) {
    // Display deleted data in table
    renderTable(data.data);
  } else {
    console.log('No deleted data for this tool');
  }
}
```

## UI Components to Add

### 1. Database Configuration Panel
- Host input
- Database name input
- Username input
- Password input (secure)
- Port input
- CSV path input
- Configure button

### 2. Tool History Panel
- List of all tool executions
- Timestamp
- Tool name and parameters
- Deleted data indicator (✓/✗)
- Click to view deleted data button

### 3. Deleted Data Viewer
- Modal/Panel to display deleted rows
- Table format with all columns
- Row count
- Export option (optional)
- Restore option (future feature)

## Example Usage Flow

1. **User configures agent** (existing)
2. **User configures database** (new)
   ```javascript
   await configureDatabase({
     host: "localhost",
     database: "preprocessing_logs",
     user: "postgres",
     password: "__Elango2006",
     port: 5432,
     csv_path: "deleted_data.csv"
   });
   ```

3. **User uploads data** (existing)
4. **User runs cleaning** (existing)
5. **View tool history** (new)
   - Shows all executed tools
   - Indicates which tools deleted data
6. **View deleted data** (new)
   - Click on any tool with deleted_data=true
   - See exactly what rows were removed

## Data Flow

```
User Action → Backend Tool Execution
                ↓
         PostgresLogger logs tool call
                ↓
    DeletedDataCSV stores deleted rows (if any)
                ↓
         Frontend fetches logs
                ↓
    User views deleted data via API
```

## Testing

Test the integration:

```bash
# Start backend
python main.py

# Configure DB
curl -X POST http://localhost:8000/configure-db \
  -H "Content-Type: application/json" \
  -d '{
    "password": "__Elango2006"
  }'

# Get logs
curl http://localhost:8000/tool-logs

# Get deleted data
curl http://localhost:8000/deleted-data/1
```
