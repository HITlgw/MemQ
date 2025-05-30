import json



def get_key(all_rel, nodes):
    
    if len(nodes) == 2:
        # type1
        if " UNION " in all_rel[nodes[1]]['relation']:
            relations = all_rel[nodes[1]]['relation'].split(" UNION ")
            assert len(relations) == 2
            if " + " in relations[0] and " + " in relations[1]:
                
                [sube1, sube2] = relations[0].split(" + ")
                tmpname1 = "?cvt0"
                [sube3, sube4] = relations[1].split(" + ")
                tmpname2 = "?cvt1"
                if not all_rel[nodes[1]]['reversed']:
                    key = f"{{ ?entity1 {sube1} ?cvt0 . ?cvt0 {sube2} ?entity2 }}UNION{{ ?entity1 {sube3} ?cvt1 . ?cvt1 {sube4} ?entity2 }}"
                else:
                    key = f"{{ ?entity2 {sube1} ?cvt0 . ?cvt0 {sube2} ?entity1 }}UNION{{ ?entity2 {sube3} ?cvt1 . ?cvt1 {sube4} ?entity1 }}"
                return key
            else:
                if not all_rel[nodes[1]]['reversed']:
                    key = f"{{ ?entity1 {relations[0]} ?entity2 }}UNION{{ ?entity1 {relations[1]} ?entity2 }}"
                else:
                    key = f"{{ ?entity2 {relations[0]} ?entity1 }}UNION{{ ?entity2 {relations[1]} ?entity1 }}"
                return key
        else:
            if not all_rel[nodes[1]]['reversed']:
                key = f"?entity1 {all_rel[nodes[1]]['relation']} ?entity2"
            else:
                key = f"?entity2 {all_rel[nodes[1]]['relation']} ?entity1"
            return key
    elif len(nodes) == 3:
        if " UNION " in all_rel[nodes[2]]['relation'] or " UNION " in all_rel[nodes[1]]['relation']:
            raise Exception("not implement type2 UNION")
        else:
            if not all_rel[nodes[1]]['reversed']:
                key1 = f"?entity1 {all_rel[nodes[1]]['relation']} ?cvt"
            else:
                key1 = f"?cvt {all_rel[nodes[1]]['relation']} ?entity1"
            
            if not all_rel[nodes[2]]['reversed']:
                key2 = f"?cvt {all_rel[nodes[2]]['relation']} ?entity2"
            else:
                key2 = f"?entity2 {all_rel[nodes[2]]['relation']} ?cvt"
            
            key = key1 +" .\n" + key2
            return key
        # type2
    else:
        if " UNION " in all_rel[nodes[-1]]['relation']:
            raise Exception("not implement type3 UNION")
        else:
        # type3
            if not all_rel[nodes[1]]['reversed']:
                key1 = f"?entity1 {all_rel[nodes[1]]['relation']} ?cvt"
            else:
                key1 = f"?cvt {all_rel[nodes[1]]['relation']} ?entity1"
            
            if not all_rel[nodes[2]]['reversed']:
                key2 = f"?cvt {all_rel[nodes[2]]['relation']} ?entity2"
            else:
                key2 = f"?entity2 {all_rel[nodes[2]]['relation']} ?cvt"
            
            if not all_rel[nodes[3]]['reversed']:
                key3 = f"?cvt {all_rel[nodes[3]]['relation']} ?entity3"
            else:
                key3 = f"?entity3 {all_rel[nodes[3]]['relation']} ?cvt"
            
            key = key1 +" .\n" + key2 + " .\n" + key3
            return key


merge_data = []
all_key = {"1":[],"2":[],"3":[]}

with open("output\webqsp_train_cvt_list.json","r") as f:
    webqspdata = json.load(f)
with open("output\cwq_train_cvt_list.json","r") as f:
    cwqdata = json.load(f)

for d in webqspdata:
    merge_data.append(d)

for d in cwqdata:
    merge_data.append(d)

for d in merge_data:
    if d['cvt_list'] == None:
        # print(d['id'])
        continue
    # print(d['graph_sparql'])
    cvt_list = d['cvt_list']
    splited_graph = []
    all_rel = d['all_rel']
    type2_cvt = {}
    for node in d["nodeorder"]:
        if "ns:" in node or cvt_list[node]:
            continue
        else:
            father = all_rel[node]['father']
            if "ns:" in father or not cvt_list[father]:
                # father 不是cvt
                type1 = [father, node]
                splited_graph.append(type1)
                key = get_key(all_rel, type1)
                # assert key in key_explain, key
                # print(type1)
                # print(key)
            else:
                # father 是cvt
                grandfather = all_rel[father]['father']
                
                assert "ns:" in grandfather or cvt_list[grandfather] == False, "grandfather is cvt"
                
                if father not in type2_cvt:
                    type2 = [grandfather, father, node]
                    splited_graph.append(type2)
                    type2_cvt[father] = type2
                    key = get_key(all_rel, type2)
                    all_key["2"].append(key)
                else:
                    type2 = type2_cvt[father]
                    type3 = [type2[0], type2[1], type2[2], node]
                    splited_graph.append(type3)
                    key = get_key(all_rel, type3)
                    all_key["3"].append(key)
    d['splited_graph'] = splited_graph


with open("output/all_key.json","w") as f:
    json.dump(all_key,f)

with open("output/merge_split_data.json", "w") as f:
    json.dump(merge_data, f)
