import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

plt.rcParams['font.sans-serif'] = ['Arial Unicode Ms']    
df = pd.read_csv("crawler_module/follow.csv", encoding='utf-8-sig')

# 整理候選人清單（name → nameid）
person_df = df[['name', 'nameid']].drop_duplicates()
nameid_map = dict(zip(person_df['name'], person_df['nameid']))
id_to_name = {v: k for k, v in nameid_map.items()}

# 檢查互追關係：name → [其他被追蹤 name]
adjacency_dict = {}

for name, nameid in nameid_map.items():
    followed_ids = df[df['name'] == name]['followid'].tolist()
    followed_names = []
    for fid in followed_ids:
        if fid in id_to_name and fid != nameid:
            followed_names.append(id_to_name[fid])
    adjacency_dict[name] = followed_names

# 輸出 adjacency_list.csv
adj_df = pd.DataFrame([
    {"name": name, "followname": "、".join(follows) if follows else ""}
    for name, follows in adjacency_dict.items()
])
adj_df.to_csv("adjacency_list.csv", index=False, encoding="utf-8-sig")
print("[CSV] 已輸出 adjacency_list.csv")

# 建立 NetworkX 圖形物件（有向圖）
G = nx.DiGraph()

# 加入節點與邊
for source, targets in adjacency_dict.items():
    for target in targets:
        G.add_edge(source, target)

# 設定圖形大小與排版
plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G, k=0.5, seed=42)  # 自動排版
nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=1200)
nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=15, edge_color='gray')
nx.draw_networkx_labels(G, pos, font_size=10, font_family="sans-serif")

plt.axis('off')
plt.title("候選人 Facebook 互追關係圖", fontsize=14)
plt.tight_layout()
plt.savefig("network_graph.png", dpi=300)
plt.close()
print("[圖像] 已輸出 network_graph.png ✅")
