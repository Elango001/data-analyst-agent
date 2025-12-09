import sqlite3
from datetime import datetime
from typing import List, Dict, Optional


class LoggingService:
    """Simple SQLite-based logging service for preprocessing tool usage."""
    
    def __init__(self, db_path: str = "preprocessing_logs.db"):
        """
        Initialize the logging service.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database connection and create tables if they don't exist."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            self._create_tables()
            print(f"✓ Database initialized: {self.db_path}")
        except sqlite3.Error as e:
            print(f"✗ Database initialization error: {e}")
            raise
    
    def _create_tables(self) -> None:
        """Create the tool_usage_log and deleted_records tables if they don't exist."""
        # Tool usage log table
        create_log_table_query = """
        CREATE TABLE IF NOT EXISTS tool_usage_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tool_name TEXT NOT NULL
        )
        """
        
        # Deleted records table for undo functionality
        create_deleted_records_query = """
        CREATE TABLE IF NOT EXISTS deleted_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            log_id INTEGER NOT NULL,
            row_index INTEGER NOT NULL,
            record_data TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (log_id) REFERENCES tool_usage_log(id)
        )
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(create_log_table_query)
            cursor.execute(create_deleted_records_query)
            self.connection.commit()
            print("✓ Tables 'tool_usage_log' and 'deleted_records' ready")
        except sqlite3.Error as e:
            print(f"✗ Table creation error: {e}")
            raise
    
    def log_tool_usage(self, tool_name: str) -> int:
        """
        Log a preprocessing tool usage.
        
        Args:
            tool_name: Name of the preprocessing tool used
            
        Returns:
            The ID of the inserted log entry
        """
        timestamp = datetime.utcnow().isoformat()
        insert_query = "INSERT INTO tool_usage_log (timestamp, tool_name) VALUES (?, ?)"
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(insert_query, (timestamp, tool_name))
            self.connection.commit()
            log_id = cursor.lastrowid
            if log_id is None:
                raise RuntimeError("Failed to retrieve log ID")
            print(f"✓ Logged: {tool_name} at {timestamp} (ID: {log_id})")
            return log_id
        except sqlite3.Error as e:
            print(f"✗ Logging error: {e}")
            raise
    
    def get_all_logs(self) -> List[Dict]:
        """
        Retrieve all logs from the database.
        
        Returns:
            List of dictionaries containing log entries
        """
        query = "SELECT id, timestamp, tool_name FROM tool_usage_log ORDER BY id DESC"
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]
            return logs
        except sqlite3.Error as e:
            print(f"✗ Error fetching all logs: {e}")
            return []
    
    def get_logs_by_tool(self, tool_name: str) -> List[Dict]:
        """
        Retrieve logs for a specific tool.
        
        Args:
            tool_name: Name of the tool to filter by
            
        Returns:
            List of dictionaries containing log entries for the specified tool
        """
        query = """
        SELECT id, timestamp, tool_name 
        FROM tool_usage_log 
        WHERE tool_name = ? 
        ORDER BY id DESC
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query, (tool_name,))
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]
            return logs
        except sqlite3.Error as e:
            print(f"✗ Error fetching logs for tool '{tool_name}': {e}")
            return []
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve the most recent logs.
        
        Args:
            limit: Number of recent logs to retrieve
            
        Returns:
            List of dictionaries containing recent log entries
        """
        query = f"""
        SELECT id, timestamp, tool_name 
        FROM tool_usage_log 
        ORDER BY id DESC 
        LIMIT ?
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]
            return logs
        except sqlite3.Error as e:
            print(f"✗ Error fetching recent logs: {e}")
            return []
    
    def get_logs_since_id(self, log_id: int) -> List[Dict]:
        """
        Retrieve all logs since a specific log ID (inclusive).
        Useful for rollback operations to get all tools used after a certain point.
        
        Args:
            log_id: The log ID to start from
            
        Returns:
            List of dictionaries containing log entries since the specified ID
        """
        query = """
        SELECT id, timestamp, tool_name 
        FROM tool_usage_log 
        WHERE id >= ? 
        ORDER BY id ASC
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query, (log_id,))
            rows = cursor.fetchall()
            logs = [dict(row) for row in rows]
            return logs
        except sqlite3.Error as e:
            print(f"✗ Error fetching logs since ID {log_id}: {e}")
            return []
    
    def get_log_by_id(self, log_id: int) -> Optional[Dict]:
        """
        Retrieve a specific log entry by ID.
        
        Args:
            log_id: The ID of the log entry
            
        Returns:
            Dictionary containing the log entry, or None if not found
        """
        query = "SELECT id, timestamp, tool_name FROM tool_usage_log WHERE id = ?"
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query, (log_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"✗ Error fetching log ID {log_id}: {e}")
            return None
    
    def get_tool_usage_sequence(self) -> List[str]:
        """
        Get the sequence of tools used in order.
        Useful for understanding the preprocessing pipeline and for rollback.
        
        Returns:
            List of tool names in the order they were used
        """
        query = "SELECT tool_name FROM tool_usage_log ORDER BY id ASC"
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [row['tool_name'] for row in rows]
        except sqlite3.Error as e:
            print(f"✗ Error fetching tool sequence: {e}")
            return []
    
    # ========================================================================
    # DELETED RECORDS MANAGEMENT (for undo functionality)
    # ========================================================================
    
    def log_deleted_record(self, batch_id: int, log_id: int, row_index: int, record_data: Dict) -> int:
        """
        Log a deleted record for undo functionality.
        Records deleted together should share the same batch_id.
        
        Args:
            batch_id: Identifier grouping records deleted together
            log_id: Reference to the tool_usage_log entry
            row_index: Original position of the row in the dataframe
            record_data: Dictionary containing the full record data
            
        Returns:
            The ID of the inserted deleted record entry
        """
        import json
        timestamp = datetime.utcnow().isoformat()
        record_json = json.dumps(record_data)
        insert_query = """
        INSERT INTO deleted_records (batch_id, log_id, row_index, record_data, timestamp) 
        VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(insert_query, (batch_id, log_id, row_index, record_json, timestamp))
            self.connection.commit()
            record_id = cursor.lastrowid
            if record_id is None:
                raise RuntimeError("Failed to retrieve deleted record ID")
            print(f"✓ Deleted record logged: Batch {batch_id}, Row {row_index} (ID: {record_id})")
            return record_id
        except sqlite3.Error as e:
            print(f"✗ Error logging deleted record: {e}")
            raise
    
    def get_deleted_records_by_batch(self, batch_id: int) -> List[Dict]:
        """
        Retrieve all deleted records belonging to the same batch.
        Records in the same batch were deleted together and should be restored together.
        
        Args:
            batch_id: The batch identifier
            
        Returns:
            List of dictionaries with deleted record data (parsed from JSON)
        """
        import json
        query = """
        SELECT id, batch_id, log_id, row_index, record_data, timestamp 
        FROM deleted_records 
        WHERE batch_id = ? 
        ORDER BY row_index ASC
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query, (batch_id,))
            rows = cursor.fetchall()
            records = []
            for row in rows:
                record = dict(row)
                record['record_data'] = json.loads(record['record_data'])
                records.append(record)
            return records
        except sqlite3.Error as e:
            print(f"✗ Error fetching deleted records for batch {batch_id}: {e}")
            return []
    
    def get_deleted_records_by_log(self, log_id: int) -> List[Dict]:
        """
        Retrieve all deleted records associated with a specific log entry.
        
        Args:
            log_id: The log ID from tool_usage_log
            
        Returns:
            List of dictionaries with deleted record data (parsed from JSON)
        """
        import json
        query = """
        SELECT id, batch_id, log_id, row_index, record_data, timestamp 
        FROM deleted_records 
        WHERE log_id = ? 
        ORDER BY batch_id ASC, row_index ASC
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query, (log_id,))
            rows = cursor.fetchall()
            records = []
            for row in rows:
                record = dict(row)
                record['record_data'] = json.loads(record['record_data'])
                records.append(record)
            return records
        except sqlite3.Error as e:
            print(f"✗ Error fetching deleted records for log {log_id}: {e}")
            return []
    
    def get_all_batches(self) -> List[int]:
        """
        Get all unique batch IDs.
        Useful for listing all deletion operations that can be undone.
        
        Returns:
            List of unique batch IDs in descending order
        """
        query = "SELECT DISTINCT batch_id FROM deleted_records ORDER BY batch_id DESC"
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [row['batch_id'] for row in rows]
        except sqlite3.Error as e:
            print(f"✗ Error fetching batch IDs: {e}")
            return []
    
    def get_batch_info(self, batch_id: int) -> Optional[Dict]:
        """
        Get information about a specific batch including count and related log.
        
        Args:
            batch_id: The batch identifier
            
        Returns:
            Dictionary with batch information (batch_id, log_id, record_count, timestamp)
        """
        query = """
        SELECT 
            batch_id,
            log_id,
            COUNT(*) as record_count,
            MIN(timestamp) as timestamp
        FROM deleted_records 
        WHERE batch_id = ?
        GROUP BY batch_id, log_id
        """
        
        try:
            if self.connection is None:
                raise RuntimeError("Database connection not initialized")
            cursor = self.connection.cursor()
            cursor.execute(query, (batch_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.Error as e:
            print(f"✗ Error fetching batch info for {batch_id}: {e}")
            return None
    
    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            print("✓ Database connection closed")


# ============================================================================
# DEMO: Example usage of the LoggingService
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Data Preprocessing Agent - Logging Service Demo")
    print("=" * 60)
    print()
    
    # Initialize the logging service
    logger = LoggingService()
    
    print("\n" + "-" * 60)
    print("1. Logging preprocessing tool usage...")
    print("-" * 60)
    log1 = logger.log_tool_usage("remove_nulls")
    log2 = logger.log_tool_usage("encode_categorical")
    
    print("\n" + "-" * 60)
    print("2. Logging deleted records (simulating 2 rows deleted together)...")
    print("-" * 60)
    # Batch 1: Two rows deleted together by remove_nulls tool
    batch_1 = 1
    row1 = {"id": 5, "name": "John", "age": None, "salary": None}
    row2 = {"id": 8, "name": "Jane", "age": None, "salary": 50000}
    
    logger.log_deleted_record(batch_id=batch_1, log_id=log1, row_index=5, record_data=row1)
    logger.log_deleted_record(batch_id=batch_1, log_id=log1, row_index=8, record_data=row2)
    
    print("\n" + "-" * 60)
    print("3. Retrieving deleted records by batch (for undo)...")
    print("-" * 60)
    deleted_batch = logger.get_deleted_records_by_batch(batch_1)
    for record in deleted_batch:
        print(f"Batch: {record['batch_id']}, Row: {record['row_index']}, Data: {record['record_data']}")
    
    print("\n" + "-" * 60)
    print("4. Getting batch information...")
    print("-" * 60)
    batch_info = logger.get_batch_info(batch_1)
    if batch_info:
        print(f"Batch {batch_info['batch_id']}: {batch_info['record_count']} records deleted at {batch_info['timestamp']}")
        print(f"Associated with log ID: {batch_info['log_id']}")
    
    print("\n" + "-" * 60)
    print("5. Getting all tool usage logs...")
    print("-" * 60)
    all_logs = logger.get_all_logs()
    for log in all_logs:
        print(f"ID: {log['id']}, Tool: {log['tool_name']}, Time: {log['timestamp']}")
    
    print("\n" + "-" * 60)
    print("6. Getting deleted records by log ID...")
    print("-" * 60)
    deleted_by_log = logger.get_deleted_records_by_log(log1)
    print(f"Total deleted records for log {log1}: {len(deleted_by_log)}")
    for record in deleted_by_log:
        print(f"  Row {record['row_index']}: {record['record_data']}")
    
    print("\n" + "-" * 60)
    print("7. Listing all available batches...")
    print("-" * 60)
    all_batches = logger.get_all_batches()
    print(f"Available batches for undo: {all_batches}")
    
    # Close the connection
    print("\n" + "-" * 60)
    logger.close()
    print("=" * 60)
    print("Demo completed!")
    print("=" * 60)


