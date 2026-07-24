#日本語訳されたcsvの内容を確認する
import pandas as pd

df = pd.read_csv("app/synEHR/my_research/data/kg.csv" , sep=',', low_memory=False)
dfx= df[df['x_type'] == 'disease']["x_name"]
dfy = df[df['y_type'] == 'disease']["y_name"]
df= pd.concat([dfx, dfy]).drop_duplicates()

print(len(df), "unique disease names in PrimeKG")

df_merge = pd.read_csv("app/synEHR/my_research/data/primekg_disease_with_japanese.csv", sep=',', low_memory=False)
df_merge.columns = ['disease_id', 'disease_name_en', 'disease_name_ja', 'source', 'ICD10_code', 'CUI_code']
print(len(df_merge), "disease nodes with codes in PrimeKG")
no_codes = df_merge[df_merge['ICD10_code'].isnull() & df_merge['CUI_code'].isnull()]
print(f"両方のコードが入っていない疾患数: {len(no_codes)}")
print(f"両方のコードが入っていないs疾患名の例: {no_codes['disease_name_en'].head(10).tolist()}")
no_japanese = df_merge[df_merge['disease_name_ja'].isnull()]
print(f"日本語病名が紐付いていない疾患数: {len(no_japanese)}")
print(f"日本語病名が紐付いていない疾患の例: {no_japanese['disease_name_en'].head(10).tolist()}")

exist_code_not_japanese = df_merge[(df_merge['ICD10_code'].notnull() | df_merge['CUI_code'].notnull()) & df_merge['disease_name_ja'].isnull()]
print(f"コードはあるが日本語病名が紐付いていない疾患数: {len(exist_code_not_japanese)}")
print(f"コードはあるが日本語病名が紐付いていない疾患の例: {exist_code_not_japanese['disease_name_en'].head(10).tolist()}")
