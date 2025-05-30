import json

INPUT_TEMPLATE = """You are given a problem to solve step by step. Each step should begin with either "Find", "Make sure" or "Rank". Finally, you need to output which one is the final answer. The steps should logically follow from one another, where each step builds on the outcome of the previous steps. 
Each step should be simple, clear, and directly related to achieving the overall goal. Some topic entities you can use to start the plan are provided below.

Question:
{question}

Topic Entity:
{topic_entity}

Plan:
"""

with open("output/All_cached_mid_names.json","r") as f:
    mid_names = json.load(f)


with open("output/merge_explain_data.json","r") as f:
    data = json.load(f)


finetune_data = []

for d in data:
    question = d['question']
    topic_entity = "*" + mid_names[d['main_path'][0]] + "*"
    source = INPUT_TEMPLATE.format(question=question, topic_entity = topic_entity)
    target = d['sparql_explain']
    finetune_data.append({"instruction": source,"input":"","output": target})

with open("output/memq_finetune_data.json","w") as f:
    json.dump(finetune_data,f)
print(len(finetune_data))