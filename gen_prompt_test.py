import json
from sparql_util import get_friendly_name
from tqdm import tqdm
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


def get_name(mid):
    if mid in mid_names:
        return mid_names[mid]
    else:
        name = get_friendly_name(mid)
        mid_names[mid] = name
        return name

with open("output/webqsp_test_graph.json","r") as f:
    webqspdata = json.load(f)

with open("output/cwq_test_graph.json","r") as f:
    cwqdata = json.load(f)


for d in tqdm(webqspdata):
    question = d['question']
    if len(d['main_path']) > 0:
        topic_entity = "*" + get_name(d['main_path'][0]) + "*"
    else:
        topic_entity = "*" + get_name(d['BegE']) + "*"
    prompt = INPUT_TEMPLATE.format(question=question, topic_entity = topic_entity)
    d['prompt'] = prompt
    # target = d['sparql_explain']

for d in tqdm(cwqdata):
    question = d['question']
    if len(d['main_path']) > 0:
        topic_entity = "*" + get_name(d['main_path'][0]) + "*"
    else:
        topic_entity = "*" + get_name(d['BegE']) + "*"
    prompt = INPUT_TEMPLATE.format(question=question, topic_entity = topic_entity)
    d['prompt'] = prompt

with open("output/All_cached_mid_names.json","w") as f:
    json.dump(mid_names,f )
with open("output/webqsp_test_prompt.json","w") as f:
    json.dump(webqspdata,f )
with open("output/cwq_test_prompt.json","w") as f:
    json.dump(cwqdata,f )
