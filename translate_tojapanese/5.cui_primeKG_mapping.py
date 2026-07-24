import re
import pandas as pd


def add_japanese_with_icd_and_cui(
    primekg_path, icd_master_path, cui_master_path, output_path
):
    print("データを読み込んでいます...")
    df_primekg = pd.read_csv(primekg_path, dtype=str)
    df_icd_master = pd.read_csv(icd_master_path, dtype=str)

    # 1. ICD-10 マスターの辞書化
    df_icd_clean = df_icd_master.dropna(subset=["icd10_formatted"])
    icd_to_ja_map = (
        df_icd_clean.groupby("icd10_formatted")["disease_name_ja"]
        .apply(lambda x: list(set(x)))
        .to_dict()
    )
    all_master_icds = list(icd_to_ja_map.keys())

    # 2. CUI マスターの辞書化
    print("CUIマスターをロードしています...")
    df_cui_master = pd.read_csv(cui_master_path, dtype=str)
    cui_to_ja_map = (
        df_cui_master.groupby("cui_code")["disease_name_ja"]
        .apply(lambda x: list(set(x)))
        .to_dict()
    )

    # ICD10 検索
    def search_icd10(icd_str):
        if pd.isna(icd_str) or not str(icd_str).strip():
            return set()
        codes = [
            c.strip()
            for c in str(icd_str).replace(" ", "").split(",")
            if c.strip()
        ]
        matched = set()
        for code in codes:
            if code in icd_to_ja_map:
                matched.update(icd_to_ja_map[code])
            else:
                prefix_matches = [
                    m for m in all_master_icds if m.startswith(code)
                ]
                for m in prefix_matches:
                    matched.update(icd_to_ja_map[m])
        return matched

    # CUI 検索
    def search_cui(cui_str):
        if pd.isna(cui_str) or not str(cui_str).strip():
            return set()
        # "C1860231" または カンマ区切り "C1414017,C1824925" を分割
        cuis = [
            c.strip().upper()
            for c in str(cui_str).replace('"', "").split(",")
            if c.strip()
        ]
        matched = set()
        for cui in cuis:
            if cui in cui_to_ja_map:
                matched.update(cui_to_ja_map[cui])
        return matched

    # 3. 紐付け処理
    print("日本語病名の紐付けを行っています (ICD-10 -> CUIの順で検索)...")
    ja_names_result = []

    icd_hit_count = 0
    cui_hit_count = 0

    for _, row in df_primekg.iterrows():
        matched_names = set()

        # Step A: ICD-10 で検索
        icd_matches = search_icd10(row.get("ICD10_code"))
        if icd_matches:
            matched_names.update(icd_matches)
            icd_hit_count += 1
        else:
            # Step B: ICD-10 で該当がない場合は CUI で検索
            cui_matches = search_cui(row.get("CUI_code"))
            if cui_matches:
                matched_names.update(cui_matches)
                cui_hit_count += 1

        # 結果の整形
        if matched_names:
            names_list = sorted(list(matched_names))
            if len(names_list) > 3:
                ja_names_result.append(
                    " / ".join(names_list[:3]) + f" (他{len(names_list)-3}件)"
                )
            else:
                ja_names_result.append(" / ".join(names_list))
        else:
            ja_names_result.append(None)

    df_primekg["disease_name_ja"] = ja_names_result

    # 列順の整理と保存
    cols = [
        "disease_id",
        "disease_name_en",
        "disease_name_ja",
        "source",
        "ICD10_code",
        "CUI_code",
    ]
    df_primekg = df_primekg[cols]
    df_primekg.to_csv(output_path, index=False, encoding="utf-8-sig")

    # ログ出力
    total_diseases = len(df_primekg)
    total_hits = df_primekg["disease_name_ja"].notnull().sum()

    print("\n--- 処理が完了しました ---")
    print(f"全疾患数: {total_diseases}")
    print(f" ├ ICD-10 経由でマッチ: {icd_hit_count} 件")
    print(f" ├ CUI 経由で追加マッチ: {cui_hit_count} 件")
    print(
        f" └ 合計日本語化完了: {total_hits} 件 (カバー率: {total_hits/total_diseases*100:.1f}%)"
    )
    print(f"出力先: {output_path}")


if __name__ == "__main__":
    primekg_path = "/app/synEHR/my_research/data/primekg_disease_with_codes.csv"
    icd_master_path = "/app/synEHR/my_research/data/icd_master_utf8.csv"
    cui_master_path = "/app/synEHR/my_research/data/cui_master.csv"
    output_path = (
        "/app/synEHR/my_research/data/primekg_disease_with_japanese.csv"
    )

    add_japanese_with_icd_and_cui(
        primekg_path, icd_master_path, cui_master_path, output_path
    )