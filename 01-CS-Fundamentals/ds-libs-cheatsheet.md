# Data-Science Libraries -- Interview Cheatsheet

## NumPy

### Why it exists
Vectorized array operations in C -> 10-100x faster than Python loops. Foundation for every Python ML lib.

### Essentials
```python
import numpy as np

a = np.array([1, 2, 3])          # 1D
M = np.array([[1,2],[3,4]])      # 2D
np.zeros((3,4))                  # 3x4 zeros
np.ones((3,4))
np.arange(0, 10, 0.5)            # like range but float
np.linspace(0, 1, 100)
np.random.randn(3, 4)            # standard normal
```

### Shapes & broadcasting
```python
A.shape, A.ndim, A.dtype
A.reshape(2, -1)                 # -1 = infer
A.T                              # transpose
A[:, np.newaxis]                 # add axis (== A[:, None])
```

**Broadcasting rules** (interview gold):
1. Align shapes from the **right**
2. Each dim: equal OR one is 1 OR missing
3. Stretch the size-1 dim virtually

```python
a = np.ones((3, 4))      # (3,4)
b = np.ones(4)           # (4,)  -> treated as (1,4) -> broadcast to (3,4)
a + b                    # works
a + np.ones(3)           #  (3,4) vs (3,) -- shapes from right: 4 vs 3 mismatch
```

### Vectorization (interview classic)
```python
# slow Python loop
out = [x**2 + 1 for x in arr]

# vectorized
out = arr**2 + 1
```

### Useful functions
- `np.sum, np.mean, np.std, np.max, np.min` -- with `axis=` arg
- `np.argmax, np.argsort` -- index of max / sort order
- `np.where(cond, a, b)` -- element-wise if/else
- `np.concatenate, np.stack, np.vstack, np.hstack, np.split`
- `np.dot, A @ B` -- matmul
- `np.einsum("ij,jk->ik", A, B)` -- flexible tensor contraction

## Pandas

### Why it exists
Tabular data with labeled rows + columns + mixed types. Bridges SQL and NumPy.

### Core objects
```python
import pandas as pd

s = pd.Series([1, 2, 3], index=["a","b","c"])
df = pd.DataFrame({
    "name": ["a","b","c"],
    "age":  [10, 20, 30],
})
```

### IO
```python
df = pd.read_csv("f.csv")
df = pd.read_parquet("f.parquet")    # faster, smaller
df = pd.read_sql("SELECT * FROM t", conn)
df.to_csv("f.csv", index=False)
```

### Selection
```python
df.head() / df.tail() / df.sample(5)
df["col"]                       # Series
df[["a","b"]]                   # DataFrame
df.loc[10, "col"]               # label-based
df.iloc[10, 2]                  # integer position
df.loc[df["age"] > 18]          # boolean mask
df.query("age > 18 and city=='Chandigarh'")
```

### Cleaning
```python
df.isna().sum()                 # count NaNs per column
df.dropna()                     # drop rows with any NaN
df.fillna(0)
df.fillna({"col": df["col"].median()})
df.duplicated().sum()
df.drop_duplicates()
df["col"].astype("int64")
```

### Group / aggregate
```python
df.groupby("category")["price"].mean()
df.groupby(["category","brand"]).agg({"price":"mean", "stock":"sum"})

# pivot
df.pivot_table(index="category", columns="month", values="sales", aggfunc="sum")
```

### Merge / join
```python
pd.merge(df1, df2, on="user_id", how="left")    # SQL-like LEFT JOIN
pd.concat([df1, df2], axis=0)                   # stack rows
```

### Date / time
```python
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.month
df.set_index("date").resample("D").sum()
```

### Apply (use sparingly)
```python
# slow if vectorization exists
df["x"] = df["a"].apply(lambda v: v * 2)
# fast
df["x"] = df["a"] * 2

# Apply legit use: complex per-row logic
df["score"] = df.apply(lambda row: complex_fn(row), axis=1)
```

## Matplotlib + Seaborn

### Quick plots
```python
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10,5))
plt.plot(x, y, label="line")
plt.scatter(x, y)
plt.bar(categories, values)
plt.hist(values, bins=30)
plt.xlabel("x"); plt.ylabel("y"); plt.legend(); plt.title("title")
plt.savefig("out.png", dpi=150, bbox_inches="tight")

# Seaborn for stat plots
sns.histplot(df["age"], kde=True)
sns.boxplot(x="category", y="price", data=df)
sns.heatmap(df.corr(), annot=True, cmap="coolwarm")
sns.pairplot(df, hue="label")
```

## scikit-learn

### The fit/transform/predict pattern
```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

scaler = StandardScaler().fit(X_train)
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)         # <- use train's stats!

clf = RandomForestClassifier(n_estimators=200, n_jobs=-1)
clf.fit(X_train_s, y_train)
preds = clf.predict(X_test_s)
print(classification_report(y_test, preds))
```

### Pipelines (avoid data leakage)
```python
from sklearn.pipeline import Pipeline

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier()),
])
pipe.fit(X_train, y_train)            # scaler.fit only on train fold
pipe.predict(X_test)
```

### Cross-validation
```python
from sklearn.model_selection import cross_val_score, KFold, StratifiedKFold

scores = cross_val_score(pipe, X, y, cv=StratifiedKFold(5), scoring="f1_macro")
print(scores.mean(), scores.std())
```

### Hyperparameter search
```python
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

grid = {"clf__n_estimators": [100, 200, 500], "clf__max_depth": [None, 10, 20]}
search = GridSearchCV(pipe, grid, cv=5, scoring="f1_macro", n_jobs=-1)
search.fit(X_train, y_train)
search.best_params_, search.best_score_
```

### Common algorithms
- `LinearRegression`, `LogisticRegression`, `Ridge`, `Lasso`
- `DecisionTreeClassifier/Regressor`
- `RandomForest...`
- `GradientBoosting...` (use XGBoost/LightGBM for production)
- `KMeans`, `DBSCAN`, `GaussianMixture`
- `PCA`, `TSNE`, `UMAP` (umap-learn)
- `KNeighbors...`
- `SVC` / `SVR`

### Metrics
- Classification: `accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix`
- Regression: `mean_squared_error, mean_absolute_error, r2_score`
- Multi-class: `average="macro"` vs `"weighted"` vs `"micro"`

## XGBoost / LightGBM (tabular SOTA)
```python
import xgboost as xgb

model = xgb.XGBClassifier(
    n_estimators=500, max_depth=6, learning_rate=0.05,
    subsample=0.8, colsample_bytree=0.8,
    early_stopping_rounds=20,
    eval_metric="auc",
)
model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
```
- Faster + better than scikit-learn's GBM on tabular
- Feature importance via `model.feature_importances_` or SHAP

## Common interview Qs
1. *Why NumPy over Python lists?* Contiguous typed memory + vectorized C loops -> 10-100x faster.
2. *Broadcasting?* Align shapes from right; each dim must match, be 1, or be missing.
3. *`.loc` vs `.iloc`?* `.loc` is label-based; `.iloc` is integer-position-based.
4. *Why use scikit-learn Pipeline?* Prevents data leakage -- preprocessing fits only on train; same params applied at inference.
5. *Train/val/test split?* Train fits model, val tunes hyperparams (and early stop), test = final eval **never touched** during dev.
6. *`apply()` slow?* Yes -- it's a Python loop under the hood. Use vectorized ops or `numpy` where possible.
7. *Stratified split?* Preserves class proportions in each split -- important for imbalanced classification.
8. *Why XGBoost over sklearn GBM?* Faster (C++ backend, multi-thread), better defaults, native early stopping, GPU support.
9. *Cross-validation purpose?* Estimate generalization error robustly + use all data for both training and validating.
10. *When NOT to use cross-validation?* Very large dataset (single split is enough) or time-series (need TimeSeriesSplit).

## Project anchor
> "For the Statcon RUL work, the full pipeline was: pandas for time-series feature engineering (rolling means, decay rates), scikit-learn Pipeline (StandardScaler -> XGBoost) to prevent leakage, GroupKFold by battery cell so the model never saw the same cell in train and val, early stopping on val AUC, then SHAP for feature attribution to explain to engineers which signals drove the prediction."
