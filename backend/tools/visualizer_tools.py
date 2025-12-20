from langchain_core.tools import tool
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from backend.Configuration.config import Config
import io
import base64

def fig_to_base64():
    """Convert current matplotlib figure to base64 string"""
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return img_base64

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

        plt.figure(figsize=(10, 6))
        df[column].dropna().hist(bins=bins)
        plt.title(f"Histogram of {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")
        
        img_base64 = fig_to_base64()

        return {
            "success": True, 
            "action": "plot_histogram", 
            "result": "Histogram plotted",
            "visualization": img_base64,
            "type": "image",
            "title": f"Histogram of {column}"
        }

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

        plt.figure(figsize=(10, 6))
        df[column].dropna().plot(kind="box")
        plt.title(f"Box Plot of {column}")
        
        img_base64 = fig_to_base64()

        return {
            "success": True, 
            "action": "plot_box", 
            "result": "Box plot plotted",
            "visualization": img_base64,
            "type": "image",
            "title": f"Box Plot of {column}"
        }

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

        plt.figure(figsize=(10, 6))
        plt.scatter(df[x], df[y], alpha=0.5)
        plt.xlabel(x)
        plt.ylabel(y)
        plt.title(f"Scatter Plot of {x} vs {y}")
        
        img_base64 = fig_to_base64()

        return {
            "success": True, 
            "action": "plot_scatter", 
            "result": "Scatter plot done",
            "visualization": img_base64,
            "type": "image",
            "title": f"Scatter Plot: {x} vs {y}"
        }

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

        plt.figure(figsize=(10, 6))
        plt.plot(df[column])
        plt.title(f"Line Plot of {column}")
        plt.xlabel("Index")
        plt.ylabel(column)
        plt.grid(True, alpha=0.3)
        
        img_base64 = fig_to_base64()

        return {
            "success": True, 
            "action": "plot_line", 
            "result": "Line chart plotted",
            "visualization": img_base64,
            "type": "image",
            "title": f"Line Plot of {column}"
        }

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

        plt.figure(figsize=(10, 6))
        df[category].value_counts().plot(kind="bar")
        plt.title(f"Bar Chart of {category}")
        plt.xlabel(category)
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha='right')
        
        img_base64 = fig_to_base64()

        return {
            "success": True, 
            "action": "plot_bar", 
            "result": "Bar chart plotted",
            "visualization": img_base64,
            "type": "image",
            "title": f"Bar Chart of {category}"
        }

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
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt='.2f', square=True)
        plt.title("Correlation Heatmap")
        
        img_base64 = fig_to_base64()

        return {
            "success": True, 
            "action": "plot_heatmap", 
            "result": "Heatmap plotted",
            "visualization": img_base64,
            "type": "image",
            "title": "Correlation Heatmap"
        }

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

        plt.figure(figsize=(10, 6))
        plt.scatter(df[x], df[y], c=cluster_labels, cmap="tab10", alpha=0.6)
        plt.xlabel(x)
        plt.ylabel(y)
        plt.title("Cluster Visualization")
        plt.colorbar(label='Cluster')
        
        img_base64 = fig_to_base64()

        return {
            "success": True, 
            "action": "plot_clusters", 
            "result": "Cluster plot done",
            "visualization": img_base64,
            "type": "image",
            "title": f"Cluster Plot: {x} vs {y}"
        }

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