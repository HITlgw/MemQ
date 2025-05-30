import json

with open("data/webqsp/WebQSP.train.json","r", encoding="utf-8") as f:
    webqsp_train_ori = json.load(f)['Questions']
with open("data/cwq/ComplexWebQuestions_test.json","r",encoding="utf-8") as f:
    cwq_test_ori = json.load(f)

with open("data/webqsp/WebQSP.test.json", "r",encoding="utf-8") as f:
    webqsp_test_ori = json.load(f)['Questions']

webqsp_topicE = {}
webqsp_test = []
for d in webqsp_test_ori:
    id = d['QuestionId']
    question = d['RawQuestion']
    ori_sparql = d['Parses'][0]['Sparql']
    BegE = d['Parses'][0]['TopicEntityMid']
    if not BegE:
        print(d)
        continue
    webqsp_test.append({"id":id,"question":question,"ori_sparql":ori_sparql,"BegE":"ns:"+BegE})
    webqsp_topicE[id] = BegE

with open("output/my_webqsp_test.json","w",encoding="utf-8") as f:
    json.dump(webqsp_test,f)

for d in webqsp_train_ori:
    id = d['QuestionId']
    BegE = d['Parses'][0]['TopicEntityMid']
    webqsp_topicE[id] = BegE

cwq_test = []
for d in cwq_test_ori:
    id = d['ID']
    question = d['question']
    ori_sparql = d['sparql']
    BegE = webqsp_topicE[d['webqsp_ID']]
    cwq_test.append({"id":id,"question":question,"ori_sparql":ori_sparql,"BegE":"ns:"+BegE})

with open("output/my_cwq_test.json","w",encoding="utf-8") as f:
    json.dump(cwq_test,f)

