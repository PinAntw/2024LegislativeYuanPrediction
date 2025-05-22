import pandas as pd
from datetime import datetime

# === 讀取資料 ===
df = pd.read_csv("./data/ElectionData.csv", encoding="utf-8-sig")

# === 性別數值化 ===
df["性別"] = df["性別"].map({"女": 0, "男": 1})

# === 年齡計算 ===
def calculate_age(birth_str):
    try:
        birth_date = pd.to_datetime(birth_str, errors='coerce')
        if pd.isna(birth_date):
            return None
        base_date = pd.to_datetime("2024-01-13")
        age = base_date.year - birth_date.year
        if (base_date.month, base_date.day) < (birth_date.month, birth_date.day):
            age -= 1
        return age
    except:
        return None

df["年齡"] = df["出生年次"].apply(calculate_age)

# === 政黨立場分類 ===（維基百科）
blue_parties = ["新黨", "中國青年黨", "親民黨", "中國國民黨", "無黨團結聯盟", "中國民眾黨", "台灣工黨", "勞動黨"]
green_parties = ["台灣團結聯盟", "喜樂島聯盟", "台澎國際法法理建國黨", "台灣基進", "民主進步黨", "時代力量", "社會民主黨", "台灣綠黨", "小民參政歐巴桑聯盟"]

def map_position(party):
    if pd.isna(party) or party.strip() == "" or party.strip() == "無":
        return 0  # 中立
    elif party in blue_parties:
        return -1
    elif party in green_parties:
        return 1
    else:
        return 0  # 其他未列入者視為中立

df["政黨立場"] = df["推薦政黨"].apply(map_position)

# One-Hot Encoding for position
df["泛藍"] = (df["政黨立場"] == -1).astype(int)
df["中立"] = (df["政黨立場"] == 0).astype(int)
df["泛綠"] = (df["政黨立場"] == 1).astype(int)

# === 學歷編碼 ===
edu_order = {
    "高中職以下": 1,
    "學士": 2,
    "碩士": 3,
    "博士": 4
}
df["學歷等級"] = df["教育程度"].map(edu_order).fillna(0).astype(int)

# === 儲存結果 ===
df.to_csv("./data/ElectionData_encoded.csv", index=False, encoding="utf-8-sig")
print("✅ 所有欄位編碼完成，含政黨立場分類，已儲存至 ElectionData_encoded.csv")
