from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm
import json

def get_model_output(prompt, model, tokenizer):
    input_ids = tokenizer.apply_chat_template([{"role":"user","content":prompt}], return_tensors="pt").to("cuda")
    output = model.generate(input_ids, max_length=1024,do_sample=False)
    # lora 需要截取
    generated_text = tokenizer.decode(output[0][len(input_ids[0]):], skip_special_tokens=True).strip()
    # generated_text = tokenizer.decode(output[0], skip_special_tokens=True).strip()
    return generated_text

model_dir = "your-finetuned-model-dir"
model = AutoModelForCausalLM.from_pretrained(model_dir, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_dir)


with open("output/webqsp_test_prompt.json", "r") as f:
    webqspdata = json.load(f)

print("generate test plan for webqsp test")
for d in tqdm(webqspdata):
    prompt = d['prompt']
    plan = get_model_output(prompt, tokenizer=tokenizer, model=model)
    error_cnt = 0
    while error_cnt<3 and plan[:5] != "Step1":
        plan = get_model_output(prompt, tokenizer=tokenizer, model=model)
        error_cnt +=1
    if plan[:5] != "Step1":
        print(f"unable to generate vaild plan of {d['id']}")
        print(plan)
    d['test_plan'] = plan

with open("output/webqsp_test_plan.json", "w") as f:
    json.dump(webqspdata, f)


    

with open("output/cwq_test_prompt.json", "r") as f:
    cwqdata = json.load(f)
print("generate test plan for cwq test")
for d in tqdm(cwqdata):
    prompt = d['prompt']
    plan = get_model_output(prompt, tokenizer=tokenizer, model=model)
    error_cnt = 0
    while error_cnt<3 and plan[:5] != "Step1":
        plan = get_model_output(prompt, tokenizer=tokenizer, model=model)
        error_cnt +=1
    if plan[:5] != "Step1":
        print(f"unable to generate vaild plan of {d['id']}")
        print(plan)
    d['test_plan'] = plan

with open("output/cwq_test_plan.json", "w") as f:
    json.dump(cwqdata, f)