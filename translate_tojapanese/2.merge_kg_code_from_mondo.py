#PrimeKGのdisease_idに対して、mondo.oboからICD10とCUIを紐付けるコードです。
import pandas as pd
import re

# -------------------------------------------------------------
# Step 1. mondo.obo から対応表を抽出する
# -------------------------------------------------------------
print("Mondo.obo の解析を開始します...")

mondo_file_path = "/app/synEHR/data/mondo/mondo.obo"

mondo_maps = []
current_id = None
current_term = False

xref_pattern = re.compile(r'^\s*xref:\s*(ICD10CM|ICD10|UMLS)\s*:\s*([^\s{]+)', re.IGNORECASE)
prop_pattern = re.compile(r'^\s*property_value:\s*skos:exactMatch\s+(ICD10CM|ICD10|UMLS)\s*:\s*([^\s"]+)', re.IGNORECASE)

with open(mondo_file_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.rstrip('\r\n')
        
        if line.strip() == "[Term]":
            current_term = True
            current_id = None
            continue
        
        if line.startswith("[") and line.endswith("]"):
            current_term = False
            
        if not current_term:
            continue
            
        if line.startswith("id:"):
            current_id = line.split("id:")[1].strip()
            
        elif line.startswith("xref:"):
            match = xref_pattern.match(line)
            if match:
                prefix = match.group(1).upper()
                code = match.group(2).strip()
                if prefix in ["ICD10CM", "ICD10"]:
                    mondo_maps.append({'disease_id': current_id, 'mapped_id': code, 'target_type': 'ICD10'})
                elif prefix == "UMLS" and code.startswith('C'):
                    mondo_maps.append({'disease_id': current_id, 'mapped_id': code, 'target_type': 'CUI'})
                    
        elif line.startswith("property_value:"):
            match = prop_pattern.match(line)
            if match:
                prefix = match.group(1).upper()
                code = match.group(2).strip()
                if prefix in ["ICD10CM", "ICD10"]:
                    mondo_maps.append({'disease_id': current_id, 'mapped_id': code, 'target_type': 'ICD10'})
                elif prefix == "UMLS" and code.startswith('C'):
                    mondo_maps.append({'disease_id': current_id, 'mapped_id': code, 'target_type': 'CUI'})

# DataFrameに変換
df_mondo_maps = pd.DataFrame(mondo_maps)

# マッピング用の辞書を作成
def extract_pure_num(mondo_id_str):
    return mondo_id_str.upper().replace('MONDO:', '').strip()

df_mondo_maps['num_id'] = df_mondo_maps['disease_id'].apply(extract_pure_num)

# 各IDに対する辞書を作成
dict_icd = df_mondo_maps[df_mondo_maps['target_type'] == 'ICD10'].groupby('num_id')['mapped_id'].apply(lambda x: ','.join(sorted(set(x)))).to_dict()
# ★ここを 'UMLS' から 'CUI' に修正しました
dict_cui = df_mondo_maps[df_mondo_maps['target_type'] == 'CUI'].groupby('num_id')['mapped_id'].apply(lambda x: ','.join(sorted(set(x)))).to_dict()

print("Mondoの辞書化が完了しました。")

# -------------------------------------------------------------
# Step 2 & 3. PrimeKGリストの読み込みとマッピング
# -------------------------------------------------------------
print("PrimeKG の疾患リストを読み込んで結合します...")
df_primekg = pd.read_csv("/app/synEHR/my_research/data/disease_sources.csv")

def map_primekg_id(primekg_id, code_dict):
    if pd.isna(primekg_id):
        return None
    
    sub_ids = str(primekg_id).split('_')
    
    found_codes = set()
    for sid in sub_ids:
        cleaned_sid = sid.strip().zfill(7)
        if cleaned_sid in code_dict:
            for code in code_dict[cleaned_sid].split(','):
                found_codes.add(code)
                
    if found_codes:
        return ','.join(sorted(found_codes))
    return None

print("ICD10コードを紐付けています...")
df_primekg['ICD10_code'] = df_primekg['disease_id'].apply(lambda x: map_primekg_id(x, dict_icd))

print("CUIコードを紐付けています...")
df_primekg['CUI_code'] = df_primekg['disease_id'].apply(lambda x: map_primekg_id(x, dict_cui))

# 結果を保存
output_path = "/app/synEHR/my_research/data/primekg_disease_with_codes.csv"
df_primekg.to_csv(output_path, index=False, encoding='utf-8')

print("\n--- 処理が完了しました！ ---")
print(f"出力ファイル: {output_path}")
print(f"総疾患数: {len(df_primekg)}")
print(f"ICD10が紐付いた件数: {df_primekg['ICD10_code'].notna().sum()}")
print(f"CUIが紐付いた件数: {df_primekg['CUI_code'].notna().sum()}")