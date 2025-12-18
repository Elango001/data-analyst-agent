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
