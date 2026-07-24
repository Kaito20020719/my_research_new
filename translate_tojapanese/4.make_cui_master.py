#MULSからCUIと日本語病名の対応表を作るコードです。
import pandas as pd

mrconso_path = "/app/synEHR/my_research/data/2026AA/META/MRCONSO.RRF"
cui_master_output_path = "/app/synEHR/my_research/data/cui_master.csv"

print(
    "MRCONSO.RRF から日本語用語 (LAT='JPN'かつ SRL != '4', '9') を抽出しています..."
)

# MRCONSO.RRF のインデックス定義:
# 0: CUI
# 1: LAT
# 11: SAB
# 14: STR
# 15: SRL

# 列番号（0, 1, 11, 14, 15）で直接読み込み
col_indices = [0, 1, 11, 14, 15]
col_names = ["CUI", "LAT", "SAB", "STR", "SRL"]

jpn_rows = []

# Cエンジンを使用して高速化（on_bad_lines='skip'で異常行を安全に回避）
chunks = pd.read_csv(
    mrconso_path,
    sep="|",
    header=None,
    usecols=col_indices,
    names=col_names,
    dtype=str,
    chunksize=500000,
    on_bad_lines="skip",
)

for chunk in chunks:
    # SRLの前後空白を除去
    chunk["SRL_clean"] = chunk["SRL"].astype(str).str.strip()

    # 条件: LAT == 'JPN' かつ SRL が '4' でも '9' でも無い
    jpn_chunk = chunk[
        (chunk["LAT"] == "JPN") & (~chunk["SRL_clean"].isin(["4", "9"]))
    ]

    if not jpn_chunk.empty:
        jpn_rows.append(jpn_chunk)

if jpn_rows:
    df_cui_ja = pd.concat(jpn_rows, ignore_index=True)

    # 重複除去 (CUI と STR の組み合わせ)
    df_cui_ja = df_cui_ja[["CUI", "STR"]].drop_duplicates()
    df_cui_ja.columns = ["cui_code", "disease_name_ja"]

    # 保存
    df_cui_ja.to_csv(cui_master_output_path, index=False, encoding="utf-8-sig")
    print(f"✅ CUIマスターを作成しました: {cui_master_output_path}")
    print(f"抽出されたユニークCUI数: {df_cui_ja['cui_code'].nunique()} 件")
    print(f"総レコード数（別名含む）: {len(df_cui_ja)} 件")
else:
    print(
        "❌ エラー: 条件を満たす日本語用語 (LAT='JPN', SRL != 4, 9) が見つかりませんでした。"
    )