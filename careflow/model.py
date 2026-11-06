import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.dummy import DummyRegressor

def train_wait_model(flow):
    """Train a small exploratory model; report holdout MAE against a mean baseline."""
    df = flow.copy()
    df["Arrival Hour"] = pd.to_datetime(
        df["Arrival or Queue Entry Time"].astype(str), format="%H:%M", errors="coerce"
    ).dt.hour
    df["Visit Weekday"] = df["Visit Date"].dt.dayofweek
    features = ["Department", "Service Type", "Queue Length on Arrival",
                "Service Time Min", "Arrival Hour", "Visit Weekday"]
    target = "Waiting Time Min"
    df = df[features + [target]].dropna(subset=[target])
    if len(df) < 30 or df[target].nunique() < 2:
        return None, "Not enough usable observations to train a meaningful exploratory model."

    X, y = df[features], df[target]
    categorical = ["Department", "Service Type"]
    numeric = [c for c in features if c not in categorical]
    prep = ColumnTransformer([
        ("cat", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                          ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
        ("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), numeric)
    ])
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42
    )
    model = Pipeline([
        ("prep", prep),
        ("regressor", RandomForestRegressor(n_estimators=200, random_state=42,
                                            min_samples_leaf=2))
    ])
    baseline = DummyRegressor(strategy="mean")
    model.fit(X_train, y_train)
    baseline.fit(X_train, y_train)
    pred = model.predict(X_test)
    base_pred = baseline.predict(X_test)
    result = {
        "model_mae": float(mean_absolute_error(y_test, pred)),
        "baseline_mae": float(mean_absolute_error(y_test, base_pred)),
        "test_rows": int(len(y_test)),
        "train_rows": int(len(y_train)),
        "model": model
    }
    return result, None
