#ICD10コードをキーにして、PrimeKGの病名に日本語病名を紐付ける
import pandas as pd


def add_japanese_disease_names_v3(primekg_path, icd_master_path, output_path):
    # 1. データの読み込み
    print("データを読み込んでいます...")
    df_primekg = pd.read_csv(primekg_path, dtype=str)
    df_master = pd.read_csv(icd_master_path, dtype=str)

    # 2. マスター側の icd10_formatted をキーにした辞書（マッピング）を作成
    # 欠損値を除外し、同じICD10コードを持つ日本語病名をセット（重複排除）にまとめる
    df_master_clean = df_master.dropna(subset=["icd10_formatted"])
    icd_to_ja_map = (
        df_master_clean.groupby("icd10_formatted")["disease_name_ja"]
        .apply(lambda x: list(set(x)))
        .to_dict()
    )

    all_master_icds = list(icd_to_ja_map.keys())

    # 3. PrimeKGのICD10文字列から日本語病名を検索・抽出するロジック
    def get_japanese_names(icd_str):
        if pd.isna(icd_str) or not str(icd_str).strip():
            return None

        # カンマ区切りのコードを個別配列にする (例: "Q78.0,Q78.8" -> ["Q78.0", "Q78.8"])
        codes = [
            c.strip()
            for c in str(icd_str).replace(" ", "").split(",")
            if c.strip()
        ]
        matched_ja_names = set()

        for code in codes:
            # ① 完全一致検索 (例: E10.0 == E10.0)
            if code in icd_to_ja_map:
                matched_ja_names.update(icd_to_ja_map[code])
            else:
                # ② 前方一致検索 (例: PrimeKGが "E10" の場合、"E10.0", "E10.1" ... をすべて拾う)
                prefix_matches = [
                    m for m in all_master_icds if m.startswith(code)
                ]
                for m in prefix_matches:
                    matched_ja_names.update(icd_to_ja_map[m])

        if matched_ja_names:
            names_list = sorted(list(matched_ja_names))
            # 代表的な病名が多くなりすぎる場合は、先頭3件＋件数表示にまとめる
            if len(names_list) > 3:
                return " / ".join(names_list[:3]) + f" (他{len(names_list)-3}件)"
            return " / ".join(names_list)

        return None

    # 4. マッチング処理
    print("日本語病名の紐付け処理を行っています...")
    df_primekg["disease_name_ja"] = df_primekg["ICD10_code"].apply(
        get_japanese_names
    )

    # 列順の整理
    cols = [
        "disease_id",
        "disease_name_en",
        "disease_name_ja",
        "source",
        "ICD10_code",
        "CUI_code",
    ]
    df_primekg = df_primekg[cols]

    # 5. 保存
    df_primekg.to_csv(output_path, index=False, encoding="utf-8-sig")

    # ログ出力
    total_icd_count = df_primekg["ICD10_code"].notnull().sum()
    hit_count = df_primekg["disease_name_ja"].notnull().sum()
    print("--- 処理が完了しました ---")
    print(f"PrimeKG側でICD10が設定されている件数: {total_icd_count}")
    print(
        f"日本語名がマッチした件数: {hit_count} (成功率: {hit_count/total_icd_count*100:.1f}%)"
    )
    print(f"出力先: {output_path}")

def check_japanese_name_nomapping(output_path):
    df_primekg = pd.read_csv(output_path, dtype=str)
    no_ja_names = df_primekg[df_primekg["disease_name_ja"].isnull()]
    have_ja_names = df_primekg[df_primekg["disease_name_ja"].notnull()]
    print(f"日本語病名が紐付いていない疾患数: {len(no_ja_names)}")
    print(f"日本語病名が紐付いている疾患数: {len(have_ja_names)}")
    print(
        f"日本語病名が紐付いていない疾患の例: {no_ja_names['disease_name_en'].head(10).tolist()}"
    )
    print(
        f"日本語病名が紐付いている疾患の例: {have_ja_names['disease_name_en'].head(10).tolist()}"
    )

if __name__ == "__main__":
    primekg_path = "/app/synEHR/my_research/data/primekg_disease_with_codes.csv"
    
    icd_master_path = (
        "/app/synEHR/my_research/data/icd_master_utf8.csv"
    )
    output_path = (
        "/app/synEHR/my_research/data/primekg_disease_with_japanese.csv"
    )

    add_japanese_disease_names_v3(primekg_path, icd_master_path, output_path)
    check_japanese_name_nomapping(output_path)

    