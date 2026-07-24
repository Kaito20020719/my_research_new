#PrimeKGから、特定の病気に関連する症状や薬の情報を抽出するスクリプト
import pandas as pd

file_path = "/home/chikaishi.23071/kadai2026/asignment-2026/synEHR/my_research/kg.csv"
kg_df = pd.read_csv(file_path,sep=",", engine='python')

target_disease_name = "type 2 diabetes mellitus"

#xとyにtarget_disease_nameが含まれる行をフィルタリング
filtered_df = kg_df[(kg_df['x_name'].str.lower() == target_disease_name.lower()) | 
                    (kg_df['y_name'].str.lower() == target_disease_name.lower())]#lower()で全て小文字に変換して比較することで、大文字小文字の違いを無視

#filtered_dfの内容を表示(関係がどのような文言かを確認するため)
"""
print(f"--- '{target_disease_name}' に関連する行の抽出結果 ---")
if not filtered_df.empty:
    filtered_df.to_csv("/home/chikaishi.23071/kadai2026/asignment-2026/synEHR/my_research/diabetes.csv", index=False, header=False)
else:
    print(f"⚠️ '{target_disease_name}' に関連する行は見つかりませんでした。")
"""
#==========================================
#1.disease_nameに関わる症状（phenotype）をピクアップ
symptoms_df = filtered_df[filtered_df['relation'] == 'disease_phenotype_positive']

#diabetesがx側、ｙ側にいるかで、相手ノードを取得
symptoms_x = symptoms_df[symptoms_df['y_name'].str.lower() == target_disease_name.lower()]['x_name']
symptoms_y = symptoms_df[symptoms_df['x_name'].str.lower() == target_disease_name.lower()]['y_name']
symptoms_list = pd.concat([symptoms_x, symptoms_y]).unique()

print(f"--- '{target_disease_name}' に関連する症状 ---")
print(symptoms_list[:20])
#==========================================
#2.薬（治療薬）のリストをピックアップ
drugs_df = filtered_df[filtered_df['relation'] == 'indication']#indicationは「適応症」の意味で、薬がどの病気に効くかを示す関係性

drugs_x = drugs_df[drugs_df['y_name'].str.lower() == target_disease_name.lower()]['x_name']
drugs_y = drugs_df[drugs_df['x_name'].str.lower() == target_disease_name.lower()]['y_name']
drugs_list = pd.concat([drugs_x, drugs_y]).unique()

print(f"--- '{target_disease_name}' に関連する薬 ---")
print(drugs_list[:20])

#==========================================
#4.csvに保存する
output_dir = "/home/chikaishi.23071/kadai2026/asignment-2026/synEHR/my_research/"
pd.Series(symptoms_list).to_csv(output_dir + "t2dm_symptoms.csv", index=False, header=["symptom"], encoding='utf-8')
pd.Series(drugs_list).to_csv(output_dir + "t2dm_drugs.csv", index=False, header=["drug"], encoding='utf-8')

print(f"✨ '{target_disease_name}' に関連する症状と薬の情報を '{output_dir}' に保存しました。")