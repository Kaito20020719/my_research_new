import transformers
import torch

model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"

pipeline = transformers.pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": torch.bfloat16},
    device_map="auto",
)

messages = [
    {
        "role": "system", 
        "content": "あなたは優秀な医者です。以下の指示と記載ルールに厳密に従って、医学的整合性のとれた現実的な電子カルテ（臨床録）を作成してください。"
    },
    {
        "role": "user", 
        "content": """糖尿病患者の初診時の臨床録を作成してください。
実際の医療現場で標準的な【SOAP形式】を用いて、論理的かつ専門的に記述してください。

【1. 患者基本情報（必ず毎回異なる架空のデータを生成）】
- 氏名：「山田太郎」や「山田花子」は絶対に使用せず、ランダムで自然な日本人の氏名を生成してください。
- 年齢、性別、住所、診療日時

【2. 病態シナリオの選択（矛盾の回避）】
以下のキーワードリストから、**医学的な矛盾が生じないように関連するものをいくつか選択し**、シナリオのベースにしてください（すべてを使うと矛盾するため、適切な組み合わせのみを選択すること）。
- Late onset（遅発性）
- Increased waist to hip ratio（ウェストヒップ比の増加 / 内臓脂肪型肥満）
- Insulin resistance（インスリン抵抗性）
- Type II diabetes mellitus（2型糖尿病）
- Autosomal dominant inheritance（常染色体優性遺伝）

【3. カルテの記載ルール（SOAP形式）】
以下の構成に沿って、各項目を必ず記載してください。

**S (Subjective: 自覚症状・患者の訴え)**
- 主訴（患者自身の言葉で）
- 現病歴
- 既往歴、家族歴
- アレルギーの有無
- 飲酒歴（「毎日」「週2回」「飲まない」などの頻度を明記）
- 喫煙歴（「現在喫煙中（本数/日）」「過去に喫煙（禁煙時期）」「一度も吸っていない」を明記）

**O (Objective: 客観的所見・検査データ)**
- 身体所見（身長、体重など）
- 主要症状（医師から見た客観的な症状）
- 検査結果（血糖値、HbA1cなど）

**A (Assessment: 評価・診断)**
- 病名（選択したキーワードに基づく診断）
- 現在の病態に対する医師の医学的評価・考察

**P (Plan: 治療計画・方針)**
- 具体的な治療法（生活習慣指導など）
- 薬物療法（※必ず下記の【薬のリスト】から、患者の病態に合ったものを1つ以上選択し、ここに明記すること）
- 患者に伝えた治療方針の説明と、それに対する患者の反応（※もし患者が指導や特定の治療を断った場合は、その旨を客観的に記録すること）

【薬のリスト】
Troglitazone, Acetohexamide, Chlorpropamide, Glimepiride, Dulaglutide, Gemigliptin, Semaglutide, Tofogliflozin, Luseogliflozin, Trelagliptin, Empagliflozin, Alogliptin, Canagliflozin, Voglibose, Albiglutide, Ipragliflozin, Teneligliptin, Anagliptin, Miglitol, Buformin, Linagliptin, Metformin, Tolbutamide, Lobeglitazone, Acarbose, Sitagliptin, Dapagliflozin, Saxagliptin, Carbutamide, Gliquidone, Lixisenatide, Glipizide, Vildagliptin, Glibornuride, Glisoxepide, Gliclazide, Liraglutide, Insulin glargine, Mitiglinide, Repaglinide, Insulin lispro, Omarigliptin, Evogliptin, Ertugliflozin, Tolazamide, Pioglitazone, Insulin human, Nateglinide, Glyburide"""
    }
]
outputs = pipeline(
    messages,
    max_new_tokens=2048,
)
print(outputs[0]["generated_text"][-1])
