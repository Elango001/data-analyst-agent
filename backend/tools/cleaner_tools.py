from langchain_core.tools import tool
import pandas as pd
from backend.Configuration.config import Config
@tool
def fillna(columns: list, strategy: str = "mean") -> dict:
    """
    description: Fills missing values using given strategy (mean, median, mode).
    args:
        - columns: List of column names to fill
        - strategy: mean | median | mode
    """
    import numpy as np
    try:
        if strategy not in ["mean", "median", "mode"]:
            raise ValueError("strategy must be one of: mean, median, mode")

        new_df = Config.data_config.get_df()
        
        for col in columns:
            if col not in new_df.columns:
                raise ValueError(f"Column '{col}' not found")

            if strategy == "mean":
                value = new_df[col].mean()
            elif strategy == "median":
                value = new_df[col].median()
            else:
                value = new_df[col].mode()[0]

            new_df[col] = new_df[col].fillna(value)

        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "fillna", "columns": columns, "strategy": strategy}), None
            )
            return {"success": True, "action": "fillna", "columns": columns, "strategy": strategy, "tool_id": tool_id}
        
        return {"success": True, "action": "fillna", "columns": columns, "strategy": strategy}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "fillna"}
@tool
def dropna(columns: list = None) -> dict:
    """
    description: Drops rows with missing values. If columns specified, drops rows with NaN in those columns only.
    args:
        - columns: List of column names to check for NaN (optional, if None checks all columns)
    """
    try:
        new_df = Config.data_config.get_df()
        
        if columns:
            for col in columns:
                if col not in new_df.columns:
                    raise ValueError(f"Column '{col}' not found")
            deleted_rows = new_df[new_df[columns].isnull().any(axis=1)].copy()
            new_df = new_df.dropna(subset=columns)
        else:
            deleted_rows = new_df[new_df.isnull().any(axis=1)].copy()
            new_df = new_df.dropna()
        
        Config.data_config.set_df(new_df)
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager and len(deleted_rows) > 0:
            tool_id = data_manager.log_tool_execution(
                str({"tool":"dropna","columns":columns}), deleted_rows
            )
            return {"success": True, "action": "dropna", "columns": columns, "rows_deleted": len(deleted_rows), "tool_id": tool_id}
        
        return {"success": True, "action": "dropna", "columns": columns, "rows_deleted": len(deleted_rows)}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "dropna"}
@tool
def scale(columns: list, strategy: str = "standard") -> dict:
    """
    description: Scales numeric columns using selected strategy (standard or minmax).
    args:
        - columns: List of numeric columns
        - strategy: standard | minmax
    """
    from sklearn.preprocessing import StandardScaler, MinMaxScaler

    try:
        if strategy not in ["standard", "minmax"]:
            raise ValueError("strategy must be standard or minmax")

        new_df = Config.data_config.get_df()
        
        for col in columns:
            if col not in new_df.columns:
                raise ValueError(f"Column '{col}' not found")

        if strategy == "standard":
            scaler = StandardScaler()
        else:
            scaler = MinMaxScaler()

        new_df[columns] = scaler.fit_transform(new_df[columns])
        Config.data_config.set_df(new_df)

        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "scale", "columns": columns, "strategy": strategy}), None
            )
            return {"success": True, "action": "scale", "strategy": strategy, "tool_id": tool_id}
        
        return {"success": True, "action": "scale", "strategy": strategy}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "scale"}
@tool
def encode(column: str, strategy: str = "onehot") -> dict:
    """
    description: Encodes a categorical column using the selected strategy.
    args:
        - column: Column name to encode
        - strategy: onehot | label
    """
    from sklearn.preprocessing import LabelEncoder

    try:
        new_df = Config.data_config.get_df()
        
        if column not in new_df.columns:
            raise ValueError(f"Column '{column}' not found")

        if strategy not in ["onehot", "label"]:
            raise ValueError("strategy must be one of: onehot, label")

        if strategy == "onehot":
            new_df = pd.get_dummies(new_df, columns=[column])

        elif strategy == "label":
            encoder = LabelEncoder()
            new_df[column] = encoder.fit_transform(new_df[column].astype(str))

        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "encode", "column": column, "strategy": strategy}), None
            )
            return {"success": True, "action": "encode", "strategy": strategy, "tool_id": tool_id}
        
        return {"success": True, "action": "encode", "strategy": strategy}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "encode"}
@tool
def remove_outliers(column: str, strategy: str = "iqr") -> dict:
    """
    description: Removes outliers using selected strategy.
    args:
        - column: Numeric column to clean
        - strategy: iqr (more strategies like zscore can be added later)
    """
    try:
        new_df = Config.data_config.get_df()
        
        if column not in new_df.columns:
            raise ValueError(f"Column '{column}' not found")

        if strategy not in ["iqr"]:
            raise ValueError("strategy must be: iqr")

        if strategy == "iqr":
            Q1 = new_df[column].quantile(0.25)
            Q3 = new_df[column].quantile(0.75)
            IQR = Q3 - Q1
            deleted_rows = new_df[(new_df[column] < Q1 - 1.5 * IQR) | (new_df[column] > Q3 + 1.5 * IQR)].copy()
            new_df = new_df[(new_df[column] >= Q1 - 1.5 * IQR) & (new_df[column] <= Q3 + 1.5 * IQR)]

        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager and len(deleted_rows) > 0:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "remove_outliers", "column": column, "strategy": strategy}), deleted_rows
            )
            return {"success": True, "action": "remove_outliers", "strategy": strategy, "rows_deleted": len(deleted_rows), "tool_id": tool_id}
        
        return {"success": True, "action": "remove_outliers", "strategy": strategy, "rows_deleted": len(deleted_rows)}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "remove_outliers"}
@tool
def drop_columns(columns: list) -> dict:
    """
    description: Drops unnecessary or irrelevant columns.
    args:
        - columns: list of column names
    """
    try:
        new_df = Config.data_config.get_df()
        
        for col in columns:
            if col not in new_df.columns:
                raise ValueError(f"Column '{col}' not found")

        deleted_data = new_df[columns].copy()
        deleted_data['_original_index'] = new_df.index
        new_df = new_df.drop(columns=columns)
        
        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "drop_columns", "columns": columns}), deleted_data
            )
            return {"success": True, "action": "drop_columns", "columns": columns, "tool_id": tool_id}
        
        return {"success": True, "action": "drop_columns", "columns": columns}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "drop_columns"}
@tool
def impute_by_group(column: str, group_by: str, strategy: str = "mean") -> dict:
    """
    description: Fills missing values based on group statistics.
    args:
        - column: the target column to impute
        - group_by: the grouping column
        - strategy: mean | median | mode
    """
    try:
        new_df = Config.data_config.get_df()
        
        if column not in new_df.columns or group_by not in new_df.columns:
            raise ValueError("Invalid column(s) provided")

        if strategy == "mean":
            new_df[column] = new_df[column].fillna(new_df.groupby(group_by)[column].transform("mean"))
        elif strategy == "median":
            new_df[column] = new_df[column].fillna(new_df.groupby(group_by)[column].transform("median"))
        else:
            new_df[column] = new_df[column].fillna(new_df.groupby(group_by)[column].transform(lambda x: x.mode()[0]))

        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "impute_by_group", "column": column, "group_by": group_by, "strategy": strategy}), None
            )
            return {"success": True, "action": "impute_by_group", "tool_id": tool_id}
        
        return {"success": True, "action": "impute_by_group"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "impute_by_group"}
@tool
def to_numeric(columns: list) -> dict:
    """
    description: Converts given columns to numeric values. Non-numeric values become NaN.
    args:
        - columns: list of column names
    """
    try:
        new_df = Config.data_config.get_df()
        
        for col in columns:
            if col not in new_df.columns:
                raise ValueError(f"Column '{col}' not found")
            new_df[col] = pd.to_numeric(new_df[col], errors="coerce")
        
        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "to_numeric", "columns": columns}), None
            )
            return {"success": True, "action": "to_numeric", "tool_id": tool_id}
        
        return {"success": True, "action": "to_numeric"}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "to_numeric"}
@tool
def to_datetime(columns: list, format: str = None) -> dict:
    """
    description: Converts string columns to datetime dtype.
    args:
        - columns: list of column names
        - format: optional datetime format string (e.g. "%Y-%m-%d")
    """
    try:
        new_df = Config.data_config.get_df()
        
        for col in columns:
            if col not in new_df.columns:
                raise ValueError(f"Column '{col}' not found")
            new_df[col] = pd.to_datetime(new_df[col], format=format, errors="coerce")
        
        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "to_datetime", "columns": columns, "format": format}), None
            )
            return {"success": True, "action": "to_datetime", "tool_id": tool_id}
        
        return {"success": True, "action": "to_datetime"}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "to_datetime"}
@tool
def clean_text(columns: list, lowercase: bool = True, remove_special: bool = True, strip: bool = True) -> dict:
    """
    description: Cleans text columns (lowercase, strip whitespace, remove symbols).
    args:
        - columns: list of column names
        - lowercase: convert to lowercase
        - remove_special: remove special characters
        - strip: trim extra spaces
    """
    import re
    try:
        new_df = Config.data_config.get_df()
        
        for col in columns:
            if col not in new_df.columns:
                raise ValueError(f"Column '{col}' not found")
            s = new_df[col].astype(str)
            if lowercase: s = s.str.lower()
            if strip: s = s.str.strip()
            if remove_special: s = s.apply(lambda x: re.sub(r"[^a-zA-Z0-9\s]", "", x))
            new_df[col] = s
        
        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "clean_text", "columns": columns, "lowercase": lowercase, "remove_special": remove_special, "strip": strip}), None
            )
            return {"success": True, "action": "clean_text", "tool_id": tool_id}
        
        return {"success": True, "action": "clean_text"}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "clean_text"}
@tool
def handle_duplicates(strategy: str = "drop") -> dict:
    """
    description: Handles duplicate records
    args:
        - strategy: drop | first | last
    """
    try:
        new_df = Config.data_config.get_df()
        
        if strategy not in ["drop", "first", "last"]:
            raise ValueError("strategy must be: drop | first | last")
        
        if strategy == "drop":
            deleted_rows = new_df[new_df.duplicated()].copy()
            new_df = new_df.drop_duplicates()
        elif strategy == "first":
            deleted_rows = new_df[new_df.duplicated(keep="first")].copy()
            new_df = new_df[~new_df.duplicated(keep="first")]
        elif strategy == "last":
            deleted_rows = new_df[new_df.duplicated(keep="last")].copy()
            new_df = new_df[~new_df.duplicated(keep="last")]
        
        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager and len(deleted_rows) > 0:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "handle_duplicates", "strategy": strategy}), deleted_rows
            )
            return {"success": True, "action": "handle_duplicates", "strategy": strategy, "rows_deleted": len(deleted_rows), "tool_id": tool_id}
        
        return {"success": True, "action": "handle_duplicates", "strategy": strategy, "rows_deleted": len(deleted_rows)}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "handle_duplicates"}
@tool
def combine_columns(columns: list, new_column: str, separator: str = "_") -> dict:
    """
    description: Combines multiple columns into a single text column.
    args:
        - columns: list of column names to combine
        - new_column: output column
        - separator: join delimiter
    """
    try:
        new_df = Config.data_config.get_df()
        
        for col in columns:
            if col not in new_df.columns:
                raise ValueError(f"Column '{col}' not found")
        
        new_df[new_column] = new_df[columns].astype(str).agg(separator.join, axis=1)
        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "combine_columns", "columns": columns, "new_column": new_column, "separator": separator}), None
            )
            return {"success": True, "action": "combine_columns", "tool_id": tool_id}
        
        return {"success": True, "action": "combine_columns"}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "combine_columns"}
@tool
def rename_columns(mapping: dict) -> dict:
    """
    description: Renames columns using a dict mapping old→new
    args:
        - mapping: {"old": "new", ...}
    """
    try:
        new_df = Config.data_config.get_df()
        new_df = new_df.rename(columns=mapping)
        Config.data_config.set_df(new_df)
        
        data_manager = Config.db_config.get_deleted_data_handler()
        if data_manager:
            tool_id = data_manager.log_tool_execution(
                str({"tool": "rename_columns", "mapping": mapping}), None
            )
            return {"success": True, "action": "rename_columns", "tool_id": tool_id}
        
        return {"success": True, "action": "rename_columns"}
    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "rename_columns"}

c_tools = [
    fillna,
    encode,
    scale,
    remove_outliers,
    to_numeric,
    to_datetime,
    clean_text,
    handle_duplicates,
    drop_columns,
    combine_columns,
    rename_columns,
    impute_by_group
]