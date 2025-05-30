from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cdist
import numpy as np
import re
import json
import networkx as nx
from sparql_util import get_result

variablepattern = r"\?[A-Za-z0-9_]+"
midnamepattern = r"\*(.+)\*"
integer_pattern = r'[-+]?\d+'

filterfloatpattern = r"a float (\"[-+]?\d+\.\d+\")"
filterstrpattern = r"a string (\"[^\"]+\")"
filterdatetimepattern = r"(\d{4}-\d{2}-\d{2})"

sortdatetimepattern = r"datetime (\?[A-Za-z0-9_]+)"
sortintegerpattern = r"integer (\?[A-Za-z0-9_]+)"
sortfloatpattern = r"float (\?[A-Za-z0-9_]+)"

findpattern = r"Find (.+), assign it to (\?[A-Za-z0-9_]+)\."
makesurepattern = r"Make sure (.+)\."
                # Sort the result based on datetime ?sk0 in descending order and keep the first result.
sortpattern = r"Sort the result based on (.+) in (descending|ascending) order and keep the (.+) result\."
finallypattern = r"Finally the answer is (\?[A-Za-z0-9_]+)\."
existspattern = r"Find (.+), assign it to (\?[A-Za-z0-9_]+)\. If (\?[A-Za-z0-9_]+) exists, ([^.]+)\."
     


with open('output/key_explain.json','r') as f:
    all_key = json.load(f)

explain_key ={}
for k in all_key:
    explain = all_key[k]
    if explain in explain_key:
        if len(k.split(".\n")) == 3:
            assert explain_key[explain]["is_tri"] == True
        else:
            assert explain_key[explain]["is_tri"] == False
        explain_key[explain]["infounit"].append(k)
    else:
        if len(k.split(" .\n")) == 3:
            explain_key[explain] = {"infounit":[k], "is_tri":True}
        else:
            explain_key[explain] = {"infounit":[k], "is_tri":False}


explain_list = list(explain_key.keys())

model = SentenceTransformer('model/all-MiniLM-L6-v2')
existing_embeddings = model.encode(explain_list, convert_to_tensor=False) 



def common_words_similarity(explain, ref_explain):
    # 转换为小写并拆分为单词列表
    words1 = explain.lower().split()
    words2 = ref_explain.lower().split()
    
    # 计算共同单词的数量
    common_words = set(words1) & set(words2)
    return len(common_words)/len(set(words1))


gamma = 0.6
alpha = 0.9
def get_infounit(explain, is_tri=False):
    query_embedding = model.encode([explain], convert_to_tensor=False) 
    # 计算与所有现有句子的余弦相似度（使用负余弦距离，因为cdist默认计算距离）
    distances = cdist(query_embedding, existing_embeddings, metric='cosine')[0]  # shape: [n_sentences]
    similarities = 1 - distances  # 转换为相似度
    # 过滤example
    if is_tri:
        for i, tmp_explain in enumerate(explain_list):
            if not explain_key[tmp_explain]['is_tri']:
                similarities[i] = 0
    else:
        for i, tmp_explain in enumerate(explain_list):
            if explain_key[tmp_explain]['is_tri']:
                similarities[i] = 0


    # 获取相似度最高的句子索引
    top_indices = np.argsort(similarities)[-8:][::-1]
    if is_tri:
        # print(explain_key[explain_list[top_indices[0]]]["infounit"], similarities[top_indices[0]])
        return explain_key[explain_list[top_indices[0]]]["infounit"], similarities[top_indices[0]]
        # print(explain_list[top_indices[0]])
    else:
        if similarities[top_indices[0]] > 0.99:
            return explain_key[explain_list[top_indices[0]]]["infounit"]
            # print(explain_list[top_indices[0]], explain_key[explain_list[top_indices[0]]]["infounit"])
        else:
            # print(similarities[top_indices])

            for i in top_indices:
                similarities[i] += gamma*common_words_similarity(explain, explain_list[i])
            top_similarity_idx = np.argsort(similarities)[-8:][::-1][0]
            top_similarity = similarities[top_similarity_idx]
            return_infounit_list = []
            for i in top_indices:
                if similarities[i] > alpha * top_similarity:
                    explain_iu = explain_key[explain_list[i]]["infounit"]
                    for iu in explain_iu:
                        return_infounit_list.append(iu)
                    # print(similarities[i] ,explain_list[i], explain_key[explain_list[i]]["infounit"])
            return return_infounit_list

def split_by_operators(s):
    pattern = r' ((?:>=|<=|!=|>|<|=)) '
    parts = re.split(pattern, s)
    return [part for part in parts if part]





def process_filter(f, idx=None):
    # 处理所有符号
    f = f.replace("should not be smaller than",">=").replace("should not be earlier than",">=")
    f = f.replace("should not be larger than","<=").replace("should not be later than","<=")
    f = f.replace("should be smaller than","<").replace("should be earlier than","<")
    f = f.replace("should be larger than",">").replace("should be later than",">")
    f = f.replace("should be","=").replace("should not be","!=")
    # 按符号拆分处理e1和e2
    f = split_by_operators(f)
    assert len(f) == 3, f"unable to parse filter {f}"
    e1 = f[0]
    e2 = f[2]
    op = f[1]
    if re.fullmatch(variablepattern, e1) and re.fullmatch(variablepattern, e2):
        # print(f"FILTER({e1} {op} {e2})")
        return f"FILTER({e1} {op} {e2})"
    elif re.fullmatch(variablepattern, e1) and e2 == "*NOW*":
        return f"FILTER(xsd:datetime({e1}) {op} \"2015-08-10\"^^xsd:dateTime)"
    elif re.fullmatch(variablepattern, e1) and re.fullmatch(midnamepattern, e2) and e2 != "*NOW*":
        # FILTER(?x = *Justin*)
        e2 = re.fullmatch(midnamepattern, e2).group(1)
        e2mids = get_mid_by_name(e2)
        expr = []
        for mid in e2mids:
            expr.append(f"{e1} {op} {mid}")
        if op == "=":
            expr = " OR ".join(expr)
        elif op == "!=":
            expr = " AND ".join(expr)
        else:
            raise Exception(f"DEBUG f: {f}")
        # if len(e2mids) > 1:
        #     print(f"FILTER({expr})")
        #     raise Exception(f"##### DEBUG f: {f}")
        if len(e2mids) == 0:
            print(f"{idx}: no mid found for {e2}")
            return ""

        return f"FILTER({expr})"
        # raise Exception(f"DEBUG f: {f}")
    elif re.fullmatch(variablepattern, e1) and re.fullmatch(filterfloatpattern, e2):
        # xsd:float(?number) = "1.8"^^xsd:float
        # print(re.fullmatch(filterfloatpattern, e2).group(1))
        e2 = re.fullmatch(filterfloatpattern, e2).group(1)
        # print(f"FILTER(xsd:float({e1}) {op} {e2}^^xsd:float)")
        return f"FILTER(xsd:float({e1}) {op} {e2}^^xsd:float)"
        # raise Exception(f"{idx} ## DEBUG f: {f} ")
    elif re.fullmatch(variablepattern, e1) and re.fullmatch(filterstrpattern, e2):
        e2 = re.fullmatch(filterstrpattern, e2).group(1)
        # print(f"FILTER(str({e1}) {op} {e2})")
        return f"FILTER(str({e1}) {op} {e2})"
        # raise Exception(f"{idx} ## DEBUG f: {f} ")
    elif re.fullmatch(variablepattern, e1) and re.fullmatch(filterdatetimepattern, e2):
        e2 = re.fullmatch(filterdatetimepattern, e2).group(1)
        # print(f"FILTER(xsd:datetime({e1}) {op} \"{e2}\"^^xsd:dateTime)")
        return f"FILTER(xsd:datetime({e1}) {op} \"{e2}\"^^xsd:dateTime)"
        # raise Exception(f"{idx} ## DEBUG f: {f} ")
    elif re.fullmatch(variablepattern, e1) and re.fullmatch(integer_pattern, e2):
        # e2 = re.fullmatch(filterintpattern, e2).group(1)
        return f"FILTER(xsd:integer({e1}) {op} \"{e2}\"^^xsd:integer)"
    else:
        raise Exception(f"{idx} ## Filter DEBUG f: {f}")

def eval_reusult(true_list, pred_list):
    true_set = set(true_list)
    pred_set = set(pred_list)

    intersection = true_set & pred_set
    
    # Precision: 预测正确的比例
    precision = len(intersection) / len(pred_set)
    
    # Recall: 真实值被预测到的比例
    recall = len(intersection) / len(true_set)
    
    # Hit@1: 第一个预测是否在真实列表中
    hit_at_1 = 1 if (len(pred_list) > 0 and pred_list[0] in true_set) else 0
    
    return precision, recall, hit_at_1

with open("output/All_cached_mid_names.json","r") as f:
    mid_names = json.load(f)
    
def get_mid_by_name(name):
    # TODO: 查找最相近的mid
    # return "ns:XXXXXXXX"
    mids = [key for key, value in mid_names.items() if value == name]
    if len(mids) == 0:
        return [key for key, value in mid_names.items() if value.lower() == name.lower()]
    else:
        # print(f"multiple mids found for name {name}")
        return mids

def process_find(e_new, explain, G, cvt_node_cnt, seen_type2, main_entity, idx=None):
    
    assert re.fullmatch( variablepattern, e_new), e_new
    
    all_entities = re.findall(r"(\*.+\*)",explain)
    all_variables = re.findall(variablepattern, explain)
    related_nodes = []
    for n in all_entities:
        related_nodes.append(n)
    for n in all_variables:
        related_nodes.append(n)
    
    # print(explain)
    # print(related_nodes)

    if len(related_nodes) == 1:
        # type1 or type2
        tmp = explain.replace(related_nodes[0],"?entity1")
        tmp = "?entity2 is "+ tmp
        # print(tmp)
        
        if re.fullmatch(midnamepattern, related_nodes[0]):
            all_e1_mid = get_mid_by_name(related_nodes[0][1:-1])
            if len(all_e1_mid) != 1:
                if main_entity in all_e1_mid:
                    e1 = main_entity
                else:
                    raise Exception(f"{idx}: more than 1 matched e1 for {related_nodes[0][1:-1]}")
            else:
                e1 = all_e1_mid[0]
        elif re.fullmatch(variablepattern, related_nodes[0]):
            e1 = related_nodes[0]
        else:
            raise Exception(f"{id}: not expected e1 {related_nodes[0]}")

        infounit = get_infounit(tmp, is_tri=False)
        # print(infounit)
        return_infounit = []
        for iu in infounit:
            # print(iu)
            if len(iu.split(" .\n")) == 2:
                seen_type2[(e_new,e1)] = f"?cvt_{cvt_node_cnt}"
                G.add_edge(e1, f"?cvt_{cvt_node_cnt}")
                G.add_edge(f"?cvt_{cvt_node_cnt}", e_new)
                # print(iu.replace("?entity2",e_new).replace("?entity1",e1).replace("?cvt",f"?cvt_{cvt_node_cnt}"))
                tmp_iu_sparql = iu.replace("?entity2",e_new).replace("?entity1",e1).replace("?cvt",f"?cvt_{cvt_node_cnt}")
                return_infounit.append(tmp_iu_sparql)
                G.add_edge(e1, f"?cvt_{cvt_node_cnt}", relation="")
                G.add_edge(f"?cvt_{cvt_node_cnt}", e_new, relation=tmp_iu_sparql)
                cvt_node_cnt+=1
                
            else:
                # print(iu.replace("?entity2",e_new).replace("?entity1",e1))
                tmp_iu_sparql = iu.replace("?entity2",e_new).replace("?entity1",e1)
                return_infounit.append(tmp_iu_sparql)
                G.add_edge(e1, e_new, relation=tmp_iu_sparql)

        return G, cvt_node_cnt, seen_type2, return_infounit
        # raise Exception("$$$$$$$$$ DEBUG: ")
    elif len(related_nodes) == 2:
        # type3
        tmp1 = explain.replace(related_nodes[0],"?entity1").replace(related_nodes[1],"?entity2")
        tmp1 = "?entity3 is " + tmp1
        infounit1, sim1 = get_infounit(tmp1, is_tri= True)
        tmp2 = explain.replace(related_nodes[0],"?entity2").replace(related_nodes[1],"?entity1")
        tmp2 = "?entity3 is " + tmp2
        infounit2, sim2 = get_infounit(tmp2, is_tri=True)
        # print(tmp1, tmp2)
        if sim1 > sim2:
            infounit = infounit1
        else:
            infounit = infounit2
        if re.fullmatch(variablepattern, related_nodes[0]):
            e1 = related_nodes[0]
        elif re.fullmatch(midnamepattern, related_nodes[0]):
            all_e1_mid = get_mid_by_name(related_nodes[0][1:-1])
            if len(all_e1_mid) != 1:
                # 如果有topic entity则选择topic entity
                if main_entity in all_e1_mid:
                    e1 = main_entity
                else:
                    raise Exception(f"{idx}: more than 1 matched e1 for {related_nodes[0][1:-1]}")
            else:
                e1 = all_e1_mid[0]
        else:
            raise Exception(f"{id} not implement type3 infounit")
        
        if re.fullmatch(variablepattern, related_nodes[1]):
            e2 = related_nodes[1]
        elif re.fullmatch(midnamepattern, related_nodes[1]):
            all_e1_mid = get_mid_by_name(related_nodes[1][1:-1])
            if len(all_e1_mid) != 1:
                raise Exception(f"{idx}: more than 1 matched e1 for {related_nodes[1][1:-1]}")
            else:
                e1 = all_e1_mid[0]
        else:
            raise Exception(f"{idx} not implement type3 infounit")
        
        # 获取e1 e2之间的节点，增加e3
        if (e1,e2) in seen_type2:
            cvtnode = seen_type2[(e1,e2)]
        elif (e2,e1) in seen_type2:
            cvtnode = seen_type2[(e2,e1)]
        else:
            print(f"{idx}: unseen type2 for {e1} and {e2}")
            return G, cvt_node_cnt, seen_type2, []
            # raise Exception(f"{idx} unseen type2 for {e1} and {e2}")
        # print(infounit[0].split(" .\n")[-1].replace("?cvt", cvtnode).replace("?entity3", e_new))
        tmp_iu_sparql = infounit[0].split(" .\n")[-1].replace("?cvt", cvtnode).replace("?entity3", e_new)
        return_infounit = [tmp_iu_sparql]
        G.add_edge(cvtnode, e_new, relation=tmp_iu_sparql)
        return G, cvt_node_cnt, seen_type2, return_infounit
        # raise Exception("$$$$$$$$$ DEBUG: ")
        
    else:
        raise Exception(f"{idx}: more than 2 nodes error")


SPARQL_TEMPLATE = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT {ansE}\nWHERE{{\n{where}\n}}\n{sort_sparql}"""


# with open("output/webqsp_test_plan.json", "r") as f:
#     testdata = json.load(f)
with open("output/cwq_test_plan.json", "r") as f:
    testdata = json.load(f)

not_evaluable_cnt = 0

total_precision = 0
total_recall = 0
total_hit_at_1 = 0

for idx, d in enumerate(testdata):
    # webqsp: 524,1162无法生成sparql; 1024,1231,1278,1582 
    # if idx in [524,541 ,1162,1024,1231,1278,1582]:
    #     not_evaluable_cnt+=1
    #     continue
    # cwq
    if idx in [632]:
        not_evaluable_cnt += 1
        continue

    if 'AnsE' in d:
        true_result = get_result(d['ori_sparql'], d['AnsE'])
    else:
        try:
            true_result = get_result(d['ori_sparql'], "?x")
        except:
            true_result = []
    d['true_result'] = true_result
    
    if "main_path" in d:
        main_entity = d["main_path"][0]
    else:
        main_entity = d["BegE"]
    cvt_node_cnt = 0
    plan = d['test_plan']
    steps = plan.split("\n")
    sort_sparql = ""
    ansE = ""
    all_step_sparql = []  
    # 记录type2的中间节点
    seen_type2 = {}
    G = nx.DiGraph()
    for s in steps:
        step = re.sub(r'Step\d+:\s*', '', s)
        # print(step)

        findmatch = re.fullmatch(findpattern, step)
        makesurematch = re.fullmatch(makesurepattern, step)
        sortmatch = re.fullmatch(sortpattern, step)
        finallymatch = re.fullmatch(finallypattern, step)
        existsmatch = re.fullmatch(existspattern, step)
        if findmatch:
            e_new = findmatch.group(2)
            explain = findmatch.group(1)
            G, cvt_node_cnt,seen_type2, return_infounit = process_find(e_new, explain, G, cvt_node_cnt, seen_type2,main_entity, idx)
            if len(return_infounit) == 1:
                all_step_sparql.append(return_infounit[0])
            else:
                tmp_step_sparql = []
                for x in return_infounit:
                    tmp_step_sparql.append(f"{{ {x} }}")
                tmp_step_sparql = "UNION".join(tmp_step_sparql)
                all_step_sparql.append(tmp_step_sparql)

        elif makesurematch:
            f = makesurematch.group(1)
            try:
                filter = process_filter(f, idx)
                if filter != "":
                    all_step_sparql.append(filter)
            except Exception as e:
                print(f"{idx} ## DEBUG f: {f}")
                raise e
            # print(filter)
        elif sortmatch:
            if sortmatch.group(2) == "descending":
                order = "DESC"
            else:
                order = "ASC"
            var = sortmatch.group(1)
            if re.fullmatch(variablepattern, var):
                # print(f"ORDER BY {order}({var})")
                sort_sparql = f"ORDER BY {order}({var})\n"
                # pass
            elif re.fullmatch(sortdatetimepattern, var):
                var = re.fullmatch(sortdatetimepattern, var).group(1)    
                # print(f"ORDER BY {order}(xsd:datetime({var}))")
                sort_sparql = f"ORDER BY {order}(xsd:datetime({var}))\n"
                # pass
            elif re.fullmatch(sortintegerpattern, var):
                # 按int排序自动转化为按float排序
                var = re.fullmatch(sortintegerpattern, var).group(1)
                # print(f"ORDER BY {order}(xsd:float({var}))")
                sort_sparql = f"ORDER BY {order}(xsd:float({var}))\n"
                pass
                # raise Exception(f"{idx} ## Sort DEBUG var: {var} {step} ")
            elif re.fullmatch(sortfloatpattern, var):
                var = re.fullmatch(sortfloatpattern, var).group(1)
                # print(f"ORDER BY {order}(xsd:float({var}))")
                sort_sparql = f"ORDER BY {order}(xsd:float({var}))\n"
                # pass
                # raise Exception(f"{idx} ## Sort DEBUG var: {var} {step} ")
            else:
                raise Exception(f"{idx} ## Sort DEBUG var: {var} {step} ")
            
            
            sortlen = sortmatch.group(3)

            if sortlen == "first":
                sort_sparql = sort_sparql + "LIMIT 1"
                # print("LIMIT 1")
                # pass
                # raise Exception(f"{idx} ## Sort DEBUG s: {s} ")
            elif sortlen == "second":
                sort_sparql = sort_sparql + "LIMIT 1\nOFFSET 1"
                # print("LIMIT 1")
                # print("OFFSET 1")
                # pass
                # raise Exception(f"{idx} ## Sort DEBUG sortlen: {sortlen} ")
            else:
                raise Exception(f"{idx} ## Sort DEBUG sortlen: {sortlen} ")
        elif finallymatch:
            # print("finally")
            ansE = finallymatch.group(1)
            final_filter = f"FILTER (!isLiteral({ansE}) OR lang({ansE}) = '' OR langMatches(lang({ansE}), 'en'))"
            all_step_sparql.append(final_filter)
            # print(f"SELECT DISTICT {ansE}")            
            # raise Exception(f"not match {s}")
            pass
        elif existsmatch:
            # print(existsmatch.group(1))
            assert existsmatch.group(2) == existsmatch.group(3), f"DEBUG exists not match: {existsmatch.group(2)} {existsmatch.group(3)}"
            # print(existsmatch.group(2))
            # print(existsmatch.group(3))
            # print(existsmatch.group(4))
            e_new = existsmatch.group(2)
            explain = existsmatch.group(1)
            G, cvt_node_cnt,seen_type2, return_infounit = process_find(e_new,explain, G, cvt_node_cnt, seen_type2, main_entity, idx)
            
            if len(return_infounit) > 0:
                exist_filter = process_filter(existsmatch.group(4), idx)
                exist_search = return_infounit[0]
                all_step_sparql.append(f"FILTER(NOT EXISTS {{ {exist_search} }} || EXISTS {{ {exist_search} .{exist_filter} }})")
            
        else:
            raise Exception(f"not match {s}")
    where = " .\n".join(all_step_sparql)
    reconstruct_sparql = SPARQL_TEMPLATE.format(ansE=ansE, where=where, sort_sparql=sort_sparql)
    d['reconstruct_sparql'] = reconstruct_sparql
    # print(reconstruct_sparql)
    # print(d['test_plan'])
        # print("")
    
    if len(true_result) >0:
        try:
            pred_result = get_result(reconstruct_sparql, ansE)
        except:
            print(f"{idx}: fail sparql")
            print(reconstruct_sparql)
            pred_result = []
        # 退化1：删除所有FILTER
        if len(pred_result) == 0:
            
            all_step_sparql1 = []
            for step_sparql in  all_step_sparql:
                if "FILTER" not in step_sparql:
                    all_step_sparql1.append(step_sparql)
            all_step_sparql1.append(f"FILTER({ansE} != {main_entity})")
            where1 = " .\n".join(all_step_sparql1)
            reconstruct_sparql1 = SPARQL_TEMPLATE.format(ansE=ansE, where=where1, sort_sparql="")
            d['reconstruct_sparql1'] = reconstruct_sparql1
            try:
                pred_result = get_result(reconstruct_sparql1, ansE)
                if len(pred_result)>0:
                    print(f"{idx}: XXXXXXX back1 work XXXXXXXX")
            except:
                print(f"{idx}: fail sparql1")
                print(reconstruct_sparql1)
                pred_result = []
        
        
        # 退化2：仅保留主要路径
        if len(pred_result) == 0:
            UG = nx.Graph(G)
            all_step_sparql2 = []
            all_paths = list(nx.all_simple_paths(UG, source=main_entity, target=ansE))
            if not all_paths:
                raise Exception(f"{idx}: back2 no path error")
            else:
                longest_path = max(all_paths, key=lambda x: len(x))
            for tmp_num in range(len(longest_path)-1):
                u = longest_path[tmp_num]
                v = longest_path[tmp_num+1]
                if G.has_edge(u, v):
                    tmp_edge_attrs = G.get_edge_data(u, v)
                    
                elif G.has_edge(v, u):
                    tmp_edge_attrs = G.get_edge_data(v, u)
                else:
                    raise Exception(f"{idx}: no path between {u} {v}")
                if tmp_edge_attrs['relation'] != "":
                    all_step_sparql2.append(tmp_edge_attrs['relation'])
            all_step_sparql1.append(f"FILTER({ansE} != {main_entity})")
            where2 = " .\n".join(all_step_sparql2)
            reconstruct_sparql2 = SPARQL_TEMPLATE.format(ansE=ansE, where=where2, sort_sparql="")
            d['reconstruct_sparql2'] = reconstruct_sparql2
            try:
                pred_result = get_result(reconstruct_sparql2, ansE)
                if len(pred_result)>0:
                    print(f"{idx}: XXXXXXX back2 work XXXXXXXX")
            except:
                print(f"{idx}: fail sparql1")
                print(reconstruct_sparql2)
                pred_result = []
            # raise Exception("XXXXXXXXXXXXXXXXXXXX")
        
        if len(pred_result) > 0:
            precision, recall, hit_at_1 = eval_reusult(true_list=true_result, pred_list=pred_result)
        else:
            precision = 0.0
            recall = 0.0
            hit_at_1 = 0
        total_precision += precision
        total_recall+= recall
        total_hit_at_1 += hit_at_1
        if precision<1 or recall<1:
            print(f"{idx}: p={precision}, r={recall}, h={hit_at_1}")
    else:
        not_evaluable_cnt += 1
        continue
    # print(reconstruct_sparql)
    # print(pred_result)
    # print(true_result)
    # print("============================")

total_num = len(testdata)-not_evaluable_cnt
avg_precision = total_precision/total_num
avg_recall = total_recall/total_num
avg_hit_at_1 = total_hit_at_1/total_num
f1 = 2*avg_precision*avg_recall/(avg_precision+avg_recall)

print("===========================================")
print(f"total evalable cnt = {total_num}")
print(f"hit@1 = {avg_hit_at_1}")
print(f"f1 = {f1}")

# with open("output/webqsp_test_reconstruct.json","w") as f:
#     json.dump(testdata,f)

with open("output/cwq_test_reconstruct.json","w") as f:
    json.dump(testdata,f)