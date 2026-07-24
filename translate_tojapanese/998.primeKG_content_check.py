import pandas as pd

file_path = "/home/chikaishi.23071/kadai2026/asignment-2026/synEHR/my_research/kg.csv"
kg_df = pd.read_csv(file_path,sep=",", engine='python')

#データの概要確認
print(kg_df.head())
#print(kg_df.info())
#print(kg_df.describe())

# ノードのタイプ（種類）にどんなものがあるか確認する
#print(kg_df['x_type'].unique())

# 関係性（エッジ）の種類にどんなものがあるか確認する
#print(kg_df['relation'].unique())

#target_disease = kg_df[kg_df['x_type'] == 'disease']
# 'x_name' 列に含まれるユニークな病名を抽出して DataFrame に変換（どのような病名があるか確認）
#disease_names = pd.DataFrame(target_disease['x_name'].unique(), columns=['disease_name'])
#diabetes = disease_names[disease_names['disease_name'].str.contains('diabetes', case=False, na=False)]
#print(diabetes)
#pd.DataFrame(disease_names, columns=['disease_name']).to_csv("/home/chikaishi.23071/kadai2026/asignment-2026/synEHR/my_research/disease_names.csv", index=False, header=False)

