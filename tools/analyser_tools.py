from langchain_core.tools import tool
import numpy as np
import pandas as pd
from Configuration.config import Config
@tool
def summary_stats(columns: list) -> dict:
    """
    description: Returns summary statistics (count, mean, std, min, 25%, 50%, 75%, max)
    args:
        - columns: List of numeric column names to summarize
    """
    try:
        df = Config.data_config.get_df()
        
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        result = {}
        for col in columns:
            result[col] = df[col].describe().to_dict()

        return {"success": True, "action": "summary_stats", "result": result}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "summary_stats"}
@tool
def value_counts(columns: list, normalize: bool = False) -> dict:
    """
    description: Returns frequency distribution for categorical columns
    args:
        - columns: List of categorical column names
        - normalize: If True, returns percentage distribution
    """
    try:
        df = Config.data_config.get_df()
        
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        result = {}
        for col in columns:
            result[col] = df[col].value_counts(normalize=normalize).to_dict()

        return {"success": True, "action": "value_counts", "normalize": normalize, "result": result}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "value_counts"}
@tool
def distribution(columns: list, bins: int = 10) -> dict:
    """
    description: Returns histogram distribution for numeric columns (bin counts)
    args:
        - columns: List of numeric column names
        - bins: Number of histogram bins
    """
    import numpy as np
    try:
        df = Config.data_config.get_df()
        
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        result = {}
        for col in columns:
            counts, bin_edges = np.histogram(df[col].dropna(), bins=bins)
            result[col] = {"counts": counts.tolist(), "bin_edges": bin_edges.tolist()}

        return {"success": True, "action": "distribution", "bins": bins, "result": result}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "distribution"}

@tool
def groupby_aggregate(group_col: str, agg_col: str, agg_fn: str = "mean") -> dict:
    """
    description: Performs groupby aggregation (mean, median, sum, max, min, count)
    args:
        - group_col: Column to group by (categorical)
        - agg_col: Column to aggregate (numeric)
        - agg_fn: mean | median | sum | max | min | count
    """
    try:
        df = Config.data_config.get_df()
        
        if group_col not in df.columns or agg_col not in df.columns:
            raise ValueError("Column not found")

        if agg_fn not in ["mean", "median", "sum", "max", "min", "count"]:
            raise ValueError("agg_fn must be one of: mean, median, sum, max, min, count")

        grouped = getattr(df.groupby(group_col)[agg_col], agg_fn)()
        result = grouped.to_dict()

        return {"success": True, "action": "groupby_aggregate", "group_col": group_col, "agg_col": agg_col, "agg_fn": agg_fn, "result": result}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "groupby_aggregate"}
@tool
def crosstab(col1: str, col2: str, normalize: bool = False) -> dict:
    """
    description: Creates a crosstab (contingency table) between two categorical columns
    args:
        - col1: First categorical column
        - col2: Second categorical column
        - normalize: If True, normalizes results to percentages
    """
    import pandas as pd
    try:
        df = Config.data_config.get_df()
        
        if col1 not in df.columns or col2 not in df.columns:
            raise ValueError("Column not found")

        ct = pd.crosstab(df[col1], df[col2], normalize="all" if normalize else False)
        return {"success": True, "action": "crosstab", "normalize": normalize, "result": ct.to_dict()}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "crosstab"}
@tool
def correlation(columns: list) -> dict:
    """
    description: Computes pairwise correlations between numeric columns
    args:
        - columns: List of numeric column names
    """
    try:
        df = Config.data_config.get_df()
        
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        corr_matrix = df[columns].corr().to_dict()
        return {"success": True, "action": "correlation", "result": corr_matrix}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "correlation"}
@tool
def covariance(columns: list) -> dict:
    """
    description: Computes covariance between numeric columns
    args:
        - columns: List of numeric column names
    """
    try:
        df = Config.data_config.get_df()
        
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        cov_matrix = df[columns].cov().to_dict()
        return {"success": True, "action": "covariance", "result": cov_matrix}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "covariance"}
@tool
def regression_analysis(target: str, features: list) -> dict:
    """
    description: Fits a linear regression model and returns coefficients + intercept + R^2 score
    args:
        - target: Target column (numeric)
        - features: List of numeric feature columns
    """
    from sklearn.linear_model import LinearRegression
    try:
        df = Config.data_config.get_df()
        
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found")

        missing_cols = [c for c in features if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Feature columns not found: {missing_cols}")

        X = df[features].dropna()
        y = df[target].loc[X.index]

        model = LinearRegression()
        model.fit(X, y)

        coefficients = dict(zip(features, model.coef_))
        intercept = model.intercept_
        r2 = model.score(X, y)

        return {
            "success": True,
            "action": "regression_analysis",
            "target": target,
            "features": features,
            "coefficients": coefficients,
            "intercept": intercept,
            "r2_score": r2,
        }

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "regression_analysis"}
@tool
def statistical_test(col1: str, col2: str, test_type: str = "t_test") -> dict:
    """
    description: Performs statistical significance test between two columns
    args:
        - col1: Column name
        - col2: Column name
        - test_type: t_test | anova | chi_square
    """
    from scipy.stats import ttest_ind, f_oneway, chi2_contingency
    import pandas as pd
    try:
        df = Config.data_config.get_df()
        
        if col1 not in df.columns or col2 not in df.columns:
            raise ValueError("Columns not found")

        if test_type == "t_test":
            stat, p = ttest_ind(df[col1].dropna(), df[col2].dropna())
        elif test_type == "anova":
            stat, p = f_oneway(df[col1].dropna(), df[col2].dropna())
        elif test_type == "chi_square":
            contingency = pd.crosstab(df[col1], df[col2])
            stat, p, _, _ = chi2_contingency(contingency)
        else:
            raise ValueError("test_type must be t_test, anova, or chi_square")

        return {"success": True, "action": "statistical_test", "test_type": test_type, "statistic": stat, "p_value": p}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "statistical_test"}
@tool
def feature_importance(target: str, features: list) -> dict:
    """
    description: Computes feature importance using a tree-based model
    args:
        - target: Target column (numeric)
        - features: List of numeric feature columns
    """
    from sklearn.ensemble import RandomForestRegressor
    try:
        df = Config.data_config.get_df()
        
        if target not in df.columns:
            raise ValueError(f"Target column '{target}' not found")

        missing_cols = [c for c in features if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Feature columns not found: {missing_cols}")

        X = df[features].dropna()
        y = df[target].loc[X.index]

        model = RandomForestRegressor(random_state=42)
        model.fit(X, y)

        importance = dict(zip(features, model.feature_importances_))

        return {"success": True, "action": "feature_importance", "target": target, "features": features, "importance": importance}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "feature_importance"}
@tool
def time_series_forecast(column: str, periods: int = 10) -> dict:
    """
    description: Forecasts future values of a time-series column using ARIMA
    args:
        - column: Numeric time-series column
        - periods: Number of future periods to forecast
    """
    from statsmodels.tsa.arima.model import ARIMA
    try:
        df = Config.data_config.get_df()
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")

        ts = df[column].dropna()
        model = ARIMA(ts, order=(1, 1, 1))
        fit = model.fit()
        forecast = fit.forecast(steps=periods)

        return {"success": True, "action": "time_series_forecast", "column": column, "periods": periods, "forecast": forecast.tolist()}

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "time_series_forecast"}
@tool
def train_regression_model(target: str, features: list) -> dict:
    """
    description: Trains a regression model to predict a numeric target variable
    args:
        - target: Target column (numeric)
        - features: List of feature columns (numeric)
    """
    from sklearn.linear_model import LinearRegression
    try:
        df = Config.data_config.get_df()
        
        if target not in df.columns:
            raise ValueError("Target column not found")
        for col in features:
            if col not in df.columns:
                raise ValueError(f"Feature column '{col}' not found")

        X = df[features].dropna()
        y = df[target].loc[X.index]

        model = LinearRegression()
        model.fit(X, y)

        return {
            "success": True,
            "action": "train_regression_model",
            "target": target,
            "features": features,
            "coefficients": dict(zip(features, model.coef_)),
            "intercept": model.intercept_,
        }

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "train_regression_model"}
@tool
def train_classification_model(target: str, features: list) -> dict:
    """
    description: Trains a classification model to predict labels using RandomForest
    args:
        - target: Target column (categorical)
        - features: List of feature columns (numeric/categorical encoded)
    """
    from sklearn.ensemble import RandomForestClassifier
    try:
        df = Config.data_config.get_df()
        
        if target not in df.columns:
            raise ValueError("Target column not found")
        for col in features:
            if col not in df.columns:
                raise ValueError(f"Feature column '{col}' not found")

        X = df[features].dropna()
        y = df[target].loc[X.index]

        model = RandomForestClassifier(random_state=42)
        model.fit(X, y)

        return {
            "success": True,
            "action": "train_classification_model",
            "target": target,
            "features": features,
            "classes": model.classes_.tolist(),
            "feature_importances": dict(zip(features, model.feature_importances_)),
        }

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "train_classification_model"}
@tool
def cluster_data(columns: list, n_clusters: int = 3) -> dict:
    """
    description: Performs clustering using KMeans to detect natural groups in data
    args:
        - columns: List of numeric columns
        - n_clusters: Number of clusters to form
    """
    from sklearn.cluster import KMeans
    try:
        df = Config.data_config.get_df()
        
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        X = df[columns].dropna()
        model = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = model.fit_predict(X)

        return {
            "success": True,
            "action": "cluster_data",
            "columns": columns,
            "n_clusters": n_clusters,
            "cluster_labels": cluster_labels.tolist(),
            "centroids": model.cluster_centers_.tolist(),
        }

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "cluster_data"}
@tool
def pca_dimensionality_reduction(columns: list, n_components: int = 2) -> dict:
    """
    description: Applies PCA to detect major drivers in the data and reduce dimensions
    args:
        - columns: List of numeric columns
        - n_components: Number of principal components
    """
    from sklearn.decomposition import PCA
    try:
        df = Config.data_config.get_df()
        
        missing_cols = [c for c in columns if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Columns not found: {missing_cols}")

        X = df[columns].dropna()
        pca = PCA(n_components=n_components)
        transformed = pca.fit_transform(X)

        return {
            "success": True,
            "action": "pca_dimensionality_reduction",
            "columns": columns,
            "n_components": n_components,
            "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
            "components": pca.components_.tolist(),
            "transformed_data": transformed.tolist(),
        }

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "pca_dimensionality_reduction"}
@tool
def anomaly_detection(column: str, threshold: float = 3.0) -> dict:
    """
    description: Detects anomalies using Z-score method
    args:
        - column: Numeric column name
        - threshold: Z-score limit (default 3.0)
    """
    import numpy as np
    try:
        df = Config.data_config.get_df()
        
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found")

        values = df[column].dropna()
        mean = values.mean()
        std = values.std()

        z_scores = (values - mean) / std
        anomalies = values[abs(z_scores) > threshold].index.tolist()

        return {
            "success": True,
            "action": "anomaly_detection",
            "column": column,
            "threshold": threshold,
            "anomaly_indices": anomalies,
        }

    except Exception as e:
        return {"success": False, "error_type": type(e).__name__, "error_message": str(e), "action": "anomaly_detection"}

a_tools=[summary_stats,
value_counts,
distribution,
correlation,
covariance,]