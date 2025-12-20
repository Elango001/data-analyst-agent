from backend.Configuration.config import Config
from typing import Optional, List, Dict
import pandas as pd
from datetime import datetime

class Versioner:
    """Class to version/save data snapshots"""
    
    def __init__(self, config: Config):
        """
        Initialize Versioner with Config
        
        Args:
            config: Config instance containing db_config with version_handler
        """
        self.config = config
        self.version_handler = config.db_config.get_version_handler()
        
        if self.version_handler is None:
            raise ValueError("Version handler not initialized in Config. Please call config.db_config.set_db_config() first.")
    
    def save_version(self, tool_details: str) -> datetime:
        """
        Save current data as a version
        
        Args:
            tool_details: Description of the tool/operation that created this version
            
        Returns:
            timestamp: The timestamp (primary key) of the saved version
        """
        current_data = self.config.data_config.get_df()
        
        if current_data is None or current_data.empty:
            raise ValueError("No data available in Config to save as version")
        
        timestamp = self.version_handler.save_version(current_data, tool_details)
        return timestamp
    
    def get_all_versions(self) -> List[Dict]:
        """
        Get all available versions metadata
        
        Returns:
            List of dictionaries containing version information
        """
        return self.version_handler.get_all_versions()


class Revert:
    """Class to revert/restore data from saved versions"""
    
    def __init__(self, config: Config):
        """
        Initialize Revert with Config
        
        Args:
            config: Config instance containing db_config with version_handler
        """
        self.config = config
        self.version_handler = config.db_config.get_version_handler()
        
        if self.version_handler is None:
            raise ValueError("Version handler not initialized in Config. Please call config.db_config.set_db_config() first.")
    
    def revert_to_version(self, timestamp: datetime) -> bool:
        """
        Revert to a specific version by copying it to current data
        Does not delete the version from storage
        
        Args:
            timestamp: The timestamp (primary key) of the version to revert to
            
        Returns:
            bool: True if successful, False otherwise
        """
        version_data = self.version_handler.get_version(timestamp)
        
        if version_data is None:
            raise ValueError(f"Version with timestamp {timestamp} not found")
        
        # Update the current data in Config
        self.config.data_config.set_df(version_data)
        return True
    
    def get_version_data(self, timestamp: datetime) -> Optional[pd.DataFrame]:
        """
        Get data from a specific version without reverting
        
        Args:
            timestamp: The timestamp (primary key) of the version
            
        Returns:
            DataFrame or None if version not found
        """
        return self.version_handler.get_version(timestamp)
    
    def get_all_versions(self) -> List[Dict]:
        """
        Get all available versions metadata
        
        Returns:
            List of dictionaries containing version information
        """
        return self.version_handler.get_all_versions()
