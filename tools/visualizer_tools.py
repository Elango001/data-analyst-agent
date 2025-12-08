from langchain_core.tools import tool
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from Configuration.config import Config
@tool
def plot_histogram(column: str, bins: int = 10) -> dict:
    """
    description: Plots histogram for a numeric column.
    args:
        - column: numeric column name
        - bins: number of bins
    """
    try:
        df = Config.data_config.get_df()
        
        if column not in df.columns:
            raise ValueError("Column not found")

        plt.figure()
        df[column].dropna().hist(bins=bins)
        plt.title(f"Histogram of {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")
        plt.show()

        return {"success": True, "action": "plot_histogram", "result": "Histogram plotted"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "plot_histogram"}
@tool
def plot_box(column: str) -> dict:
    """
    description: Plots box plot to show distribution and outliers.
    args:
        - column: numeric column name
    """
    try:
        df = Config.data_config.get_df()
        
        if column not in df.columns:
            raise ValueError("Column not found")

        plt.figure()
        df[column].dropna().plot(kind="box")
        plt.title(f"Box Plot of {column}")
        plt.show()

        return {"success": True, "action": "plot_box", "result": "Box plot plotted"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "plot_box"}
@tool
def plot_scatter(x: str, y: str) -> dict:
    """
    description: Plots scatter chart for two numeric columns.
    args:
        - x: X-axis column
        - y: Y-axis column
    """
    try:
        df = Config.data_config.get_df()
        
        if x not in df.columns or y not in df.columns:
            raise ValueError("Column not found")

        plt.figure()
        plt.scatter(df[x], df[y])
        plt.xlabel(x)
        plt.ylabel(y)
        plt.title(f"Scatter Plot of {x} vs {y}")
        plt.show()

        return {"success": True, "action": "plot_scatter", "result": "Scatter plot done"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "plot_scatter"}
@tool
def plot_line(column: str) -> dict:
    """
    description: Plots a line chart for numeric column over index (usually time).
    args:
        - column: numeric column
    """
    try:
        df = Config.data_config.get_df()
        
        if column not in df.columns:
            raise ValueError("Column not found")

        plt.figure()
        plt.plot(df[column])
        plt.title(f"Line Plot of {column}")
        plt.xlabel("Index")
        plt.ylabel(column)
        plt.show()

        return {"success": True, "action": "plot_line", "result": "Line chart plotted"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "plot_line"}
@tool
def plot_bar(category: str) -> dict:
    """
    description: Plots bar chart for category count distribution.
    args:
        - category: categorical column name
    """
    try:
        df = Config.data_config.get_df()
        
        if category not in df.columns:
            raise ValueError("Column not found")

        plt.figure()
        df[category].value_counts().plot(kind="bar")
        plt.title(f"Bar Chart of {category}")
        plt.xlabel(category)
        plt.ylabel("Count")
        plt.show()

        return {"success": True, "action": "plot_bar", "result": "Bar chart plotted"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "plot_bar"}
@tool
def plot_heatmap(columns: list) -> dict:
    """
    description: Plots correlation heatmap for numeric columns.
    args:
        - columns: list of numeric columns
    """
    try:
        df = Config.data_config.get_df()
        
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found: {missing}")

        corr = df[columns].corr()
        plt.figure()
        sns.heatmap(corr, annot=True, cmap="coolwarm")
        plt.title("Correlation Heatmap")
        plt.show()

        return {"success": True, "action": "plot_heatmap", "result": "Heatmap plotted"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "plot_heatmap"}
@tool
def plot_clusters(x: str, y: str, cluster_labels: list) -> dict:
    """
    description: Plots 2D cluster visualization using x & y numeric columns.
    args:
        - x: numeric feature
        - y: numeric feature
        - cluster_labels: cluster labels from clustering algorithm
    """
    try:
        df = Config.data_config.get_df()
        
        if x not in df.columns or y not in df.columns:
            raise ValueError("Column not found")
        if len(cluster_labels) != len(df):
            raise ValueError("Length of cluster_labels must match dataset size")

        plt.figure()
        plt.scatter(df[x], df[y], c=cluster_labels, cmap="tab10")
        plt.xlabel(x)
        plt.ylabel(y)
        plt.title("Cluster Visualization")
        plt.show()

        return {"success": True, "action": "plot_clusters", "result": "Cluster plot done"}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "plot_clusters"}
v_tools=[
    plot_histogram,
    plot_box,
    plot_scatter,
    plot_line,
    plot_bar,
    plot_heatmap,
    plot_clusters,]