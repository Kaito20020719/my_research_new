#primekgのkg.csvから、疾患の病名とKG内での疾患IDとソース名のリストを作る
import pandas as pd

# 1. kg.csv を読み込む
df = pd.read_csv('app/my_research_new/data/kg.csv', low_memory=False)

# 2. x側 または y側 が "disease" の行のみを抽出する
disease_nodes_x = df[df['x_type'] == 'disease'][['x_id', 'x_name', 'x_source']].drop_duplicates()
disease_nodes_x.columns = ['disease_id', 'disease_name_en', 'source']

disease_nodes_y = df[df['y_type'] == 'disease'][['y_id', 'y_name', 'y_source']].drop_duplicates()
disease_nodes_y.columns = ['disease_id', 'disease_name_en', 'source']

# 3. 重複を排除して「PrimeKGが持つ英語の病名＆IDリスト」を作る
primekg_diseases = pd.concat([disease_nodes_x, disease_nodes_y]).drop_duplicates()

#output_dir = "/app/synEHR/my_research/data/"
#primekg_diseases.to_csv(output_dir + "disease_sources.csv", index=False, encoding='utf-8')

print(primekg_diseases['source'].unique())