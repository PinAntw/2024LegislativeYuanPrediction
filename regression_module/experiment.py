import pandas as pd
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Arial Unicode Ms']

# === 載入資料並處理缺失值 ===
df = pd.read_csv("./data/ElectionData.csv", encoding="utf-8-sig")
df.fillna(df.median(numeric_only=True), inplace=True)

# === 定義變數群 ===
label = "得票率"
group1 = ["學歷等級", "性別", "年齡", "原選區連任", "在位與否"]
group2 = ["政黨立場","泛藍","中立","泛綠","人口密度", "政黨地位(上屆政黨得票率)", "競爭激烈(Entropy)"] 
group3 = ["PageRank", "Density", "Mutuality", "Betweenness", "Closeness", "有無臉書"]

# === 建立標準化迴歸模型 ===
def standardized_ols(X, y):
    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y.values.reshape(-1, 1)).flatten()
    X_scaled = sm.add_constant(X_scaled)
    model = sm.OLS(y_scaled, X_scaled).fit()
    return model

# === 擷取迴歸結果並加上顯著性星號 ===
def extract_results(model, features):
    coefs = model.params[1:]  # 跳過常數項
    pvals = model.pvalues[1:]
    stars = []
    for p in pvals:
        if p < 0.001:
            stars.append("***")
        elif p < 0.01:
            stars.append("**")
        elif p < 0.05:
            stars.append("*")
        else:
            stars.append("")
    formatted = [f"{coef:.3f}{star}" for coef, star in zip(coefs, stars)]
    return pd.Series(formatted, index=features)

# === 建立三個模型 ===
X1 = df[group1]
X2 = df[group1 + group2]
X3 = df[group1 + group2 + group3]
y = df[label]

model1 = standardized_ols(X1, y)
model2 = standardized_ols(X2, y)
model3 = standardized_ols(X3, y)

res1 = extract_results(model1, X1.columns)
res2 = extract_results(model2, X2.columns)
res3 = extract_results(model3, X3.columns)

# === 整合成單一表格 ===
all_features = list(dict.fromkeys(list(X1.columns) + list(X2.columns) + list(X3.columns)))
result_df = pd.DataFrame(index=all_features)
result_df["Model 1"] = res1
result_df["Model 2"] = res2
result_df["Model 3"] = res3

# === 抽取模型摘要指標 ===
f1 = model1.fvalue
f2 = model2.fvalue
f3 = model3.fvalue

adj_r2_1 = model1.rsquared_adj
adj_r2_2 = model2.rsquared_adj
adj_r2_3 = model3.rsquared_adj

delta_r2_2 = adj_r2_2 - adj_r2_1
delta_r2_3 = adj_r2_3 - adj_r2_2

# === 建立新行表示統計指標 ===
stats_df = pd.DataFrame({
    "Model 1": [f"{f1:.1f}***", f"{adj_r2_1:.3f}", ""],
    "Model 2": [f"{f2:.1f}***", f"{adj_r2_2:.3f}", f"{delta_r2_2:.3f}"],
    "Model 3": [f"{f3:.1f}***", f"{adj_r2_3:.3f}", f"{delta_r2_3:.3f}"]
}, index=["F", "Adjusted R²", "ΔR²"])

# === 合併原始係數表格與統計摘要 ===
full_result_df = pd.concat([result_df, stats_df])

# === 重畫圖與輸出 ===
fig, ax = plt.subplots(figsize=(12, len(full_result_df) * 0.5 + 1))
ax.axis("off")
table = ax.table(cellText=full_result_df.fillna("").values,
                 rowLabels=full_result_df.index,
                 colLabels=full_result_df.columns,
                 cellLoc='center',
                 loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.2, 1.5)
plt.tight_layout()
plt.savefig("./data/standardized_regression_table.png", dpi=300)

# === 輸出 CSV ===
full_result_df.to_csv("./data/standardized_regression_table.csv", encoding="utf-8-sig")

print("✅ 已產生含摘要的 standardized_regression_table.png 與 .csv")
