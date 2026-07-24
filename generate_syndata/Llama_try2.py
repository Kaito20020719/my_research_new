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
        "content": "あなたは優秀な医者です。臨床録を作成してください。"
    },
    {
        "role": "user", 
        "content": """糖尿病の患者の臨床録を作成してください。
        症状はLate onset、Increased waist to hip ratio、Insulin resistance、Type II diabetes mellitus、Autosomal dominant inheritanceを使ってください。
        薬はdrug以下の中から選んでください。薬は複数選択しても構いません。薬は必ず1つ以上選択してください。薬のリストは以下です。
        Troglitazone
        Acetohexamide
        Chlorpropamide
        Glimepiride
        Dulaglutide
        Gemigliptin
        Semaglutide
        Tofogliflozin
        Luseogliflozin
        Trelagliptin
        Empagliflozin
        Alogliptin
        Canagliflozin
        Voglibose
        Albiglutide
        Ipragliflozin
        Teneligliptin
        Anagliptin
        Miglitol
        Buformin
        Linagliptin
        Metformin
        Tolbutamide
        Lobeglitazone
        Acarbose
        Sitagliptin
        Dapagliflozin
        Saxagliptin
        Carbutamide
        Gliquidone
        Lixisenatide
        Glipizide
        Vildagliptin
        Glibornuride
        Glisoxepide
        Gliclazide
        Liraglutide
        Insulin glargine
        Mitiglinide
        Repaglinide
        Insulin lispro
        Omarigliptin
        Evogliptin
        Ertugliflozin
        Tolazamide
        Pioglitazone
        Insulin human
        Nateglinide
        Glyburide"""   
        },
]

outputs = pipeline(
    messages,
    max_new_tokens=256,
)
print(outputs[0]["generated_text"][-1])
