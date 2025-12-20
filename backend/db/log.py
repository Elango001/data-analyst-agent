import csv
import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class ToolExecutionLog(Base):
    __tablename__ = 'tool_execution_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    tool_name = Column(String, nullable=False)
    deleted_data = Column(Boolean, default=False, nullable=False)

class CleanerResponse(Base):
    __tablename__ = 'cleaner_response'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(Integer, nullable=False)
    response_data = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)

class DataVersion(Base):
    __tablename__ = 'data_version'
    
    timestamp = Column(DateTime, primary_key=True, nullable=False)
    tool_details = Column(Text, nullable=False)
    csv_filename = Column(String, nullable=False)

class PostgresLogger:
    def __init__(self, host: str = "localhost", database: str = "preprocessing_logs", 
                 user: str = "postgres", password: str = "postgres", port: int = 5432):
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        if not database_exists(database_url):
            create_database(database_url)
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def log_tool_execution(self, tool_name: str, has_deleted_data: bool) -> int:
        session: Session = self.SessionLocal()
        try:
            log_entry = ToolExecutionLog(
                timestamp=datetime.utcnow(),
                tool_name=tool_name,
                deleted_data=has_deleted_data
            )
            session.add(log_entry)
            session.commit()
            return log_entry.id
        finally:
            session.close()
    
    def check_has_deleted_data(self, tool_id: int) -> bool:
        session: Session = self.SessionLocal()
        try:
            log = session.query(ToolExecutionLog).filter_by(id=tool_id).first()
            return log.deleted_data if log else False
        finally:
            session.close()
    
    def save_cleaner_response(self, tool_id: int, response_data: str):
        session: Session = self.SessionLocal()
        try:
            response = CleanerResponse(
                tool_id=tool_id,
                response_data=response_data,
                timestamp=datetime.utcnow()
            )
            session.add(response)
            session.commit()
        finally:
            session.close()
    
    def get_all_tool_logs(self) -> List[Dict]:
        session: Session = self.SessionLocal()
        try:
            logs = session.query(ToolExecutionLog).all()
            return [
                {
                    'id': log.id,
                    'timestamp': log.timestamp,
                    'tool_name': log.tool_name,
                    'deleted_data': log.deleted_data
                }
                for log in logs
            ]
        finally:
            session.close()
    
    def get_cleaner_response(self, tool_id: int) -> Optional[str]:
        session: Session = self.SessionLocal()
        try:
            response = session.query(CleanerResponse).filter_by(tool_id=tool_id).first()
            return response.response_data if response else None
        finally:
            session.close()
    
    def save_data_version(self, timestamp: datetime, tool_details: str, csv_filename: str):
        """Save a data version entry to the database"""
        session: Session = self.SessionLocal()
        try:
            version = DataVersion(
                timestamp=timestamp,
                tool_details=tool_details,
                csv_filename=csv_filename
            )
            session.add(version)
            session.commit()
        finally:
            session.close()
    
    def get_data_version(self, timestamp: datetime) -> Optional[Dict]:
        """Get a specific data version by timestamp"""
        session: Session = self.SessionLocal()
        try:
            version = session.query(DataVersion).filter_by(timestamp=timestamp).first()
            if version:
                return {
                    'timestamp': version.timestamp,
                    'tool_details': version.tool_details,
                    'csv_filename': version.csv_filename
                }
            return None
        finally:
            session.close()
    
    def get_all_data_versions(self) -> List[Dict]:
        """Get all data versions ordered by timestamp"""
        session: Session = self.SessionLocal()
        try:
            versions = session.query(DataVersion).order_by(DataVersion.timestamp.desc()).all()
            return [
                {
                    'timestamp': version.timestamp,
                    'tool_details': version.tool_details,
                    'csv_filename': version.csv_filename
                }
                for version in versions
            ]
        finally:
            session.close()
    
    def delete_data_version(self, timestamp: datetime, version_dir: str = "data_versions") -> bool:
        """Delete a data version from both database and CSV file"""
        session: Session = self.SessionLocal()
        try:
            # Get the version record first to get the csv filename
            version = session.query(DataVersion).filter_by(timestamp=timestamp).first()
            if not version:
                return False
            
            csv_filename = version.csv_filename
            
            # Delete from database
            session.delete(version)
            session.commit()
            
            # Delete the CSV file if it exists
            csv_path = os.path.join(version_dir, csv_filename)
            if os.path.exists(csv_path):
                os.remove(csv_path)
                print(f"Deleted CSV file: {csv_path}")
            
            return True
        except Exception as e:
            session.rollback()
            print(f"Error deleting version: {e}")
            return False
        finally:
            session.close()

class DeletedDataCSV:
    def __init__(self, csv_path: str = "deleted_data.csv"):
        self.csv_path = csv_path
        self._initialize_csv()
    
    def _initialize_csv(self):
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['tool_id', 'deleted_row'])
    
    def store_deleted_data(self, tool_id: int, deleted_rows: pd.DataFrame):
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            for _, row in deleted_rows.iterrows():
                row_data = row.to_json()
                writer.writerow([tool_id, row_data])
    
    def get_deleted_data(self, tool_id: int) -> Optional[pd.DataFrame]:
        from io import StringIO
        deleted_rows = []
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row['tool_id']) == tool_id:
                    deleted_rows.append(pd.read_json(StringIO(row['deleted_row']), typ='series'))
        
        if deleted_rows:
            return pd.DataFrame(deleted_rows)
        return None

class VersionCSV:
    def __init__(self, version_dir: str = "data_versions"):
        self.version_dir = version_dir
        self._initialize_directory()
    
    def _initialize_directory(self):
        if not os.path.exists(self.version_dir):
            os.makedirs(self.version_dir)
    
    def save_version(self, timestamp: datetime, data: pd.DataFrame) -> str:
        """Save a version of the data and return the filename"""
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S_%f")
        filename = f"version_{timestamp_str}.csv"
        filepath = os.path.join(self.version_dir, filename)
        data.to_csv(filepath, index=False)
        return filename
    
    def get_version(self, filename: str) -> Optional[pd.DataFrame]:
        """Retrieve a version by filename"""
        filepath = os.path.join(self.version_dir, filename)
        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        return None
    
    def list_versions(self) -> List[str]:
        """List all version files"""
        if os.path.exists(self.version_dir):
            return [f for f in os.listdir(self.version_dir) if f.startswith("version_") and f.endswith(".csv")]
        return []


class DeletedDataHandler:
    def __init__(self, host: str = "localhost", database: str = "preprocessing_logs", 
                 user: str = "postgres", password: str = "postgres", port: int = 5432,
                 csv_path: str = "deleted_data.csv"):
        self.postgres = PostgresLogger(host, database, user, password, port)
        self.csv = DeletedDataCSV(csv_path)
    
    def log_tool_execution(self, tool_name: str, deleted_rows: Optional[pd.DataFrame] = None) -> int:
        has_deleted_data = deleted_rows is not None and len(deleted_rows) > 0
        tool_id = self.postgres.log_tool_execution(tool_name, has_deleted_data)
        
        if has_deleted_data:
            self.csv.store_deleted_data(tool_id, deleted_rows)
        
        return tool_id
    
    def get_deleted_data(self, tool_id: int) -> Optional[pd.DataFrame]:
        return self.csv.get_deleted_data(tool_id)
    
    def check_has_deleted_data(self, tool_id: int) -> bool:
        return self.postgres.check_has_deleted_data(tool_id)
    
    def save_cleaner_response(self, tool_id: int, response_data: str):
        self.postgres.save_cleaner_response(tool_id, response_data)
    
    def get_all_tool_logs(self) -> List[Dict]:
        return self.postgres.get_all_tool_logs()
    
    def get_cleaner_response(self, tool_id: int) -> Optional[str]:
        return self.postgres.get_cleaner_response(tool_id)

class VersionHandler:
    def __init__(self, host: str = "localhost", database: str = "preprocessing_logs", 
                 user: str = "postgres", password: str = "postgres", port: int = 5432,
                 version_dir: str = "data_versions"):
        self.postgres = PostgresLogger(host, database, user, password, port)
        self.csv = VersionCSV(version_dir)
    
    def save_version(self, data: pd.DataFrame, tool_details: str) -> datetime:
        """Save a version of the data with tool details"""
        timestamp = datetime.utcnow()
        
        # Save the CSV file
        csv_filename = self.csv.save_version(timestamp, data)
        
        # Log to PostgreSQL
        self.postgres.save_data_version(timestamp, tool_details, csv_filename)
        
        return timestamp
    
    def get_version(self, timestamp: datetime) -> Optional[pd.DataFrame]:
        """Retrieve a specific version by timestamp"""
        version_info = self.postgres.get_data_version(timestamp)
        if version_info:
            return self.csv.get_version(version_info['csv_filename'])
        return None
    
    def get_all_versions(self) -> List[Dict]:
        """Get all version metadata"""
        return self.postgres.get_all_data_versions()
    
    def get_version_by_csv_filename(self, csv_filename: str) -> Optional[pd.DataFrame]:
        """Retrieve a version directly by CSV filename"""
        return self.csv.get_version(csv_filename)
    
    def delete_data_version(self, timestamp: datetime) -> bool:
        """Delete a data version from both database and CSV file"""
        return self.postgres.delete_data_version(timestamp, self.csv.version_dir)

