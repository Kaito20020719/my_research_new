import pandas as pd

print("kg.csv を読み込んでいます...")
# 1. kg.csv を読み込む
df = pd.read_csv("app/my_research_new/data/kg.csv", low_memory=False)

# 2. x側 または y側 が "disease" の行のみを抽出する
disease_nodes_x = df[df["x_type"] == "disease"][
    ["x_id", "x_name", "x_source"]
].drop_duplicates()
disease_nodes_x.columns = ["disease_id", "disease_name_en", "source"]

disease_nodes_y = df[df["y_type"] == "disease"][
    ["y_id", "y_name", "y_source"]
].drop_duplicates()
disease_nodes_y.columns = ["disease_id", "disease_name_en", "source"]

# 3. 重複を排除して「PrimeKGが持つ英語の病名＆IDリスト」を作る
primekg_diseases = pd.concat(
    [disease_nodes_x, disease_nodes_y]
).drop_duplicates()

print(f"分解前のユニーク疾患数: {len(primekg_diseases)}")

# -------------------------------------------------------------
# ★ Approach A: グループ化された disease_id を1行ずつ分解する処理
# -------------------------------------------------------------
print("グループ化された disease_id (例: 11160_13119...) を分解しています...")

# 1. disease_id をアンダースコア '_' でリストに分割
primekg_diseases["disease_id_single"] = (
    primekg_diseases["disease_id"].astype(str).str.split("_")
)

# 2. explode 関数でリスト要素を縦に展開（行に分解）
primekg_diseases_exploded = primekg_diseases.explode("disease_id_single")

# 3. カラムの整理と元の複合ID保持（トレーサビリティのため）
primekg_diseases_exploded["original_grouped_id"] = primekg_diseases_exploded[
    "disease_id"
]
primekg_diseases_exploded["disease_id"] = primekg_diseases_exploded[
    "disease_id_single"
]

# 不要になった一時カラムを削除し、ID重複を除去
cols_order = [
    "disease_id",
    "disease_name_en",
    "source",
    "original_grouped_id",
]
primekg_diseases_exploded = primekg_diseases_exploded[
    cols_order
].drop_duplicates()

# -------------------------------------------------------------
# 保存と確認
# -------------------------------------------------------------
output_path = (
    "app/my_research_new/data/japanese_mapping/disease_sources_group_sep.csv"
)
primekg_diseases_exploded.to_csv(output_path, index=False, encoding="utf-8")

print("\n--- 処理が完了しました ---")
print(f"分解後の総疾患数（単一ID単位）: {len(primekg_diseases_exploded)}")
print(f"含まれる source 種別: {primekg_diseases_exploded['source'].unique()}")
print(f"保存先: {output_path}")

# 分解例のプレビュー表示
print("\n[抽出データサンプル]")
print(primekg_diseases_exploded.head(5))