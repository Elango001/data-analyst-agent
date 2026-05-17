import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

try:
    from sqlalchemy_utils import database_exists, create_database
except Exception:  # pragma: no cover - optional dependency
    database_exists = None
    create_database = None

load_dotenv()

Base = declarative_base()

class ToolExecutionLog(Base):
    __tablename__ = 'tool_execution_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    agent_name = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    tool_payload = Column(Text, nullable=True)

class AgentInteractionLog(Base):
    __tablename__ = 'agent_interaction_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    agent_name = Column(String, nullable=False)
    response_data = Column(Text, nullable=True)
    tool_payload = Column(Text, nullable=True)
    code_payload = Column(Text, nullable=True)

class CodeExecutionLog(Base):
    __tablename__ = 'code_execution_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    agent_name = Column(String, nullable=False)
    code_id = Column(String, nullable=True)
    code_payload = Column(Text, nullable=False)
    result_payload = Column(Text, nullable=True)
    error_payload = Column(Text, nullable=True)

class PostgresLogger:
    def __init__(self, host: str = "localhost", database: str = "preprocessing_logs", 
                 user: str = "postgres", password: str = "postgres", port: int = 5432):
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        # print(database_url)
        if database_exists is not None and create_database is not None and not database_exists(database_url):
            create_database(database_url)
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        # print(database_url)

    def _serialize_payload(self, payload: Optional[Any]) -> Optional[str]:
        if payload is None:
            return None
        if isinstance(payload, str):
            return payload
        try:
            return json.dumps(payload, default=str)
        except TypeError:
            return str(payload)

    def log_tool_execution(self, agent_name: str, tool_name: str, tool_payload: Optional[Any] = None) -> int:
        session: Session = self.SessionLocal()
        try:
            log_entry = ToolExecutionLog(
                timestamp=datetime.utcnow(),
                agent_name=agent_name,
                tool_name=tool_name,
                tool_payload=self._serialize_payload(tool_payload)
            )
            session.add(log_entry)
            session.commit()
            return log_entry.id
        finally:
            session.close()

    def log_agent_interaction(
        self,
        agent_name: str,
        response_data: Optional[Any],
        tool_payload: Optional[Any] = None,
        code_payload: Optional[Any] = None,
    ) -> int:
        session: Session = self.SessionLocal()
        try:
            response = AgentInteractionLog(
                timestamp=datetime.utcnow(),
                agent_name=agent_name,
                response_data=self._serialize_payload(response_data),
                tool_payload=self._serialize_payload(tool_payload),
                code_payload=self._serialize_payload(code_payload),
            )
            session.add(response)
            session.commit()
            return response.id
        finally:
            session.close()

    def log_code_execution(
        self,
        agent_name: str,
        code_id: Optional[str],
        code_payload: Any,
        result_payload: Optional[Any] = None,
        error_payload: Optional[Any] = None,
    ) -> int:
        session: Session = self.SessionLocal()
        try:
            log_entry = CodeExecutionLog(
                timestamp=datetime.utcnow(),
                agent_name=agent_name,
                code_id=code_id,
                code_payload=self._serialize_payload(code_payload) or "",
                result_payload=self._serialize_payload(result_payload),
                error_payload=self._serialize_payload(error_payload),
            )
            session.add(log_entry)
            session.commit()
            return log_entry.id
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
                    'agent_name': log.agent_name,
                    'tool_name': log.tool_name,
                    'tool_payload': log.tool_payload
                }
                for log in logs
            ]
        finally:
            session.close()
    def get_agent_logs(self, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
        session: Session = self.SessionLocal()
        try:
            query = session.query(AgentInteractionLog)
            if agent_name:
                query = query.filter_by(agent_name=agent_name)
            logs = query.all()
            return [
                {
                    'id': log.id,
                    'timestamp': log.timestamp,
                    'agent_name': log.agent_name,
                    'response_data': log.response_data,
                    'tool_payload': log.tool_payload,
                    'code_payload': log.code_payload,
                }
                for log in logs
            ]
        finally:
            session.close()

    def get_all_code_logs(self) -> List[Dict[str, Any]]:
        session: Session = self.SessionLocal()
        try:
            logs = session.query(CodeExecutionLog).all()
            return [
                {
                    'id': log.id,
                    'timestamp': log.timestamp,
                    'agent_name': log.agent_name,
                    'code_id': log.code_id,
                    'code_payload': log.code_payload,
                    'result_payload': log.result_payload,
                    'error_payload': log.error_payload,
                }
                for log in logs
            ]
        finally:
            session.close()
