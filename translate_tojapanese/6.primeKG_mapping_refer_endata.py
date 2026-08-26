import re
from collections import deque
import pandas as pd


def add_japanese_with_icd_cui_and_en_v2(
    primekg_path,
    icd_master_path,
    cui_master_path,
    cui_en_master_path,
    mondo_obo_path,
    output_path,
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

    # 3. 英語名マスター (cui_master_inc_en.csv) の辞書化
    print("英語名対応マスターをロード・辞書化しています...")
    df_cui_en = pd.read_csv(cui_en_master_path, dtype=str)

    def normalize_text(text):
        if pd.isna(text):
            return ""
        return str(text).lower().strip()

    en_to_ja_map = {}
    for _, row in df_cui_en.dropna(subset=["disease_name_ja"]).iterrows():
        ja_names = [
            n.strip()
            for n in str(row["disease_name_ja"]).split("/")
            if n.strip()
        ]

        en_candidates = []
        if "disease_name_en_pref" in row and pd.notna(
            row["disease_name_en_pref"]
        ):
            en_candidates.append(row["disease_name_en_pref"])
        if "disease_name_en_all" in row and pd.notna(
            row["disease_name_en_all"]
        ):
            en_candidates.extend(str(row["disease_name_en_all"]).split("/"))

        for en in en_candidates:
            norm_en = normalize_text(en)
            if norm_en:
                if norm_en not in en_to_ja_map:
                    en_to_ja_map[norm_en] = set()
                en_to_ja_map[norm_en].update(ja_names)

    # --------------------------------------------------
    # 4. mondo.obo から 親概念(is_a) および 廃止転送マップ(replaced_by / consider) を構築
    # --------------------------------------------------
    print("mondo.obo を解析中 (親概念構造 & 廃止ノード転送マップ)...")
    parent_map = {}  # 子MONDO_ID -> [親MONDO_IDのリスト]
    replaced_by_map = {}  # 廃止MONDO_ID -> 現行MONDO_ID

    is_a_pattern = re.compile(r"^\s*is_a:\s*(MONDO:\d+)", re.IGNORECASE)
    replaced_pattern = re.compile(
        r"^\s*replaced_by:\s*(MONDO:\d+)", re.IGNORECASE
    )
    consider_pattern = re.compile(r"^\s*consider:\s*(MONDO:\d+)", re.IGNORECASE)

    def extract_mondo_num(mondo_str):
        if pd.isna(mondo_str) or not str(mondo_str).strip():
            return ""
        clean_str = (
            str(mondo_str)
            .upper()
            .replace("MONDO:", "")
            .replace("MONDO_", "")
            .strip()
        )
        return clean_str.zfill(7) if clean_str.isdigit() else ""

    current_id = None
    current_term = False

    with open(mondo_obo_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.rstrip("\r\n")

            if line.strip() == "[Term]":
                current_term = True
                current_id = None
                continue

            if line.startswith("[") and line.endswith("]"):
                current_term = False

            if not current_term:
                continue

            if line.startswith("id:"):
                current_id = extract_mondo_num(line.split("id:")[1].strip())
                if current_id and current_id not in parent_map:
                    parent_map[current_id] = []

            elif line.startswith("is_a:"):
                match = is_a_pattern.match(line)
                if match and current_id:
                    parent_id = extract_mondo_num(match.group(1))
                    if parent_id:
                        parent_map[current_id].append(parent_id)

            elif line.startswith("replaced_by:"):
                match = replaced_pattern.match(line)
                if match and current_id:
                    rep_id = extract_mondo_num(match.group(1))
                    if rep_id:
                        replaced_by_map[current_id] = rep_id

            elif line.startswith("consider:"):
                # replaced_by が定義されていない場合の代替候補として登録
                if current_id and current_id not in replaced_by_map:
                    match = consider_pattern.match(line)
                    if match:
                        cons_id = extract_mondo_num(match.group(1))
                        if cons_id:
                            replaced_by_map[current_id] = cons_id

    print(
        f"  └ obo解析完了: ノード数={len(parent_map)}, 廃止ノード転送ルール数={len(replaced_by_map)}"
    )

    # 検索高速化用: MONDO ID -> 行データの逆引き辞書
    mondo_to_row_map = {}
    for _, row in df_primekg.iterrows():
        m_id = extract_mondo_num(row.get("disease_id"))
        if m_id:
            mondo_to_row_map[m_id] = row

    # --------------------------------------------------
    # ヘルパー関数群
    # --------------------------------------------------
    def get_active_mondo_id(mondo_id_str):
        """廃止ノードID（obsolete）を現行のMONDO IDに自動変換する（多重置換対応）"""
        m_id = extract_mondo_num(mondo_id_str)
        if not m_id:
            return ""

        visited_ids = set()
        curr = m_id
        # ループ（多重リダイレクト）防止のため最大10回まで追跡
        for _ in range(10):
            if curr in replaced_by_map and curr not in visited_ids:
                visited_ids.add(curr)
                curr = replaced_by_map[curr]
            else:
                break
        return curr

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

    def search_cui(cui_str):
        if pd.isna(cui_str) or not str(cui_str).strip():
            return set()
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

    def search_english(en_str):
        if pd.isna(en_str) or not str(en_str).strip():
            return set()
        norm_en = normalize_text(en_str)
        if norm_en in en_to_ja_map:
            return en_to_ja_map[norm_en]
        return set()

    def search_parent_ontology(mondo_id_str):
        """現行ノード（または廃止転送後のノード）から親概念(is_a)を幅優先探索(BFS)で遡って検索"""
        active_id = get_active_mondo_id(mondo_id_str)
        if not active_id or active_id not in parent_map:
            return set()

        queue = deque(parent_map[active_id])
        visited = {active_id}

        while queue:
            curr_parent_id = queue.popleft()
            if curr_parent_id in visited:
                continue
            visited.add(curr_parent_id)

            if curr_parent_id in mondo_to_row_map:
                parent_row = mondo_to_row_map[curr_parent_id]

                p_icd = search_icd10(parent_row.get("ICD10_code"))
                if p_icd:
                    return p_icd

                p_cui = search_cui(parent_row.get("CUI_code"))
                if p_cui:
                    return p_cui

                p_en = search_english(parent_row.get("disease_name_en"))
                if p_en:
                    return p_en

            if curr_parent_id in parent_map:
                for p_p in parent_map[curr_parent_id]:
                    if p_p not in visited:
                        queue.append(p_p)

        return set()

    # --------------------------------------------------
    # 紐付け処理（メイン）
    # --------------------------------------------------
    print("日本語病名の紐付けを行っています...")
    ja_names_result = []

    icd_hit_count = 0
    cui_hit_count = 0
    en_hit_count = 0
    obsolete_hit_count = 0  # 廃止ノード転送による直接ヒット数
    parent_hit_count = 0  # 親概念検索によるヒット数

    for _, row in df_primekg.iterrows():
        matched_names = set()

        # Step A: ICD-10 で検索
        icd_matches = search_icd10(row.get("ICD10_code"))
        if icd_matches:
            matched_names.update(icd_matches)
            icd_hit_count += 1
        else:
            # Step B: CUI で検索
            cui_matches = search_cui(row.get("CUI_code"))
            if cui_matches:
                matched_names.update(cui_matches)
                cui_hit_count += 1
            else:
                # Step C: 英語病名 (disease_name_en) で照合
                en_matches = search_english(row.get("disease_name_en"))
                if en_matches:
                    matched_names.update(en_matches)
                    en_hit_count += 1
                else:
                    # ★ Step D-1: 廃止ノード（obsolete）転送先の現行ノード情報で再照合
                    orig_mondo = row.get("disease_id")
                    active_mondo = get_active_mondo_id(orig_mondo)

                    if active_mondo and active_mondo != extract_mondo_num(
                        orig_mondo
                    ):
                        if active_mondo in mondo_to_row_map:
                            active_row = mondo_to_row_map[active_mondo]
                            act_icd = search_icd10(active_row.get("ICD10_code"))
                            act_cui = search_cui(active_row.get("CUI_code"))
                            act_en = search_english(
                                active_row.get("disease_name_en")
                            )

                            if act_icd:
                                matched_names.update(act_icd)
                            elif act_cui:
                                matched_names.update(act_cui)
                            elif act_en:
                                matched_names.update(act_en)

                            if matched_names:
                                obsolete_hit_count += 1

                    # ★ Step D-2: それでもヒットしない場合、親概念(is_a)を遡って検索
                    if not matched_names:
                        parent_matches = search_parent_ontology(orig_mondo)
                        if parent_matches:
                            matched_names.update(parent_matches)
                            parent_hit_count += 1

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
    existing_cols = [c for c in cols if c in df_primekg.columns]
    df_primekg = df_primekg[existing_cols]

    df_primekg.to_csv(output_path, index=False, encoding="utf-8-sig")

    # ログ出力
    total_diseases = len(df_primekg)
    total_hits = df_primekg["disease_name_ja"].notnull().sum()

    print("\n--- 処理が完了しました ---")
    print(f"全疾患数: {total_diseases}")
    print(f" ├ ICD-10 経由でマッチ: {icd_hit_count} 件")
    print(f" ├ CUI 経由で追加マッチ: {cui_hit_count} 件")
    print(f" ├ 英語名 経由で追加マッチ: {en_hit_count} 件")
    print(
        f" ├ 廃止ノード(obsolete)転送経由で追加マッチ: {obsolete_hit_count} 件"
    )
    print(f" ├ 親概念(is_a) 経由で追加マッチ: {parent_hit_count} 件")
    print(
        f" └ 合計日本語化完了: {total_hits} 件 (カバー率: {total_hits/total_diseases*100:.1f}%)"
    )
    print(f"出力先: {output_path}")


if __name__ == "__main__":
    primekg_path = "app/my_research_new/data/japanese_mapping/primekg_disease_with_codes.csv"
    icd_master_path = "/app/my_research_new/data/japanese_mapping/japanese_mapping_master/icd_master_utf8.csv"
    cui_master_path = "app/my_research_new/data/japanese_mapping/japanese_mapping_master/cui_master.csv"
    cui_en_master_path = "app/my_research_new/data/japanese_mapping/japanese_mapping_master/cui_master_inc_en.csv"
    mondo_obo_path = "app/my_research_new/synEHR/data/mondo/mondo.obo"
    output_path = (
        "app/my_research_new/data/japanese_mapping/primekg_disease_with_japanese.csv"
    )

    add_japanese_with_icd_cui_and_en_v2(
        primekg_path,
        icd_master_path,
        cui_master_path,
        cui_en_master_path,
        mondo_obo_path,
        output_path,
    )