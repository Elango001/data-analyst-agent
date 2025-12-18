import csv
import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
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

class DeletedDataHandler:
    def __init__(self, host: str = "localhost", database: str = "preprocessing_logs", 
                 user: str = "postgres", password: str = "postgres", port: int = 5432,
                 csv_path: str = "deleted_data.csv"):
        self.csv_path = csv_path
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self._initialize_csv()
    
    def _initialize_csv(self):
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['tool_id', 'deleted_row'])
    
    def log_tool_execution(self, tool_name: str, deleted_rows: Optional[pd.DataFrame] = None) -> int:
        session: Session = self.SessionLocal()
        try:
            has_deleted_data = deleted_rows is not None and len(deleted_rows) > 0
            
            log_entry = ToolExecutionLog(
                timestamp=datetime.utcnow(),
                tool_name=tool_name,
                deleted_data=has_deleted_data
            )
            session.add(log_entry)
            session.commit()
            tool_id = log_entry.id
            
            if has_deleted_data:
                self._store_deleted_data(tool_id, deleted_rows)
            
            return tool_id
        finally:
            session.close()
    
    def _store_deleted_data(self, tool_id: int, deleted_rows: pd.DataFrame):
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            for _, row in deleted_rows.iterrows():
                row_data = row.to_json()
                writer.writerow([tool_id, row_data])
    
    def get_deleted_data(self, tool_id: int) -> Optional[pd.DataFrame]:
        deleted_rows = []
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if int(row['tool_id']) == tool_id:
                    deleted_rows.append(pd.read_json(row['deleted_row'], typ='series'))
        
        if deleted_rows:
            return pd.DataFrame(deleted_rows)
        return None
    
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
