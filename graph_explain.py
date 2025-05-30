import json
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sparql_util import get_friendly_name
from tqdm import tqdm

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



def split_by_operators(s):
    pattern = r' ((?:>=|<=|!=|>|<|=)) '
    parts = re.split(pattern, s)
    return [part for part in parts if part]

with open("output/All_cached_mid_names.json","r") as f:
    mid_names = json.load(f)


def get_name(mid):
    if mid in mid_names:
        return mid_names[mid]
    else:
        name = get_friendly_name(mid)
        mid_names[mid] = name
        return name
        

with open("output/key_explain.json","r") as f:
    key_explain = json.load(f)

with open("output/merge_split_data.json","r") as f:
    data = json.load(f)

def explain_find(sub_graph, all_rel):
    node = sub_graph[-1]
    key = get_key(all_rel, sub_graph)
    subgraph_explain = key_explain[key][12:-1]

    if len(sub_graph) == 2 or len(sub_graph) == 3:
        # type1/type2
        if "ns:" in sub_graph[0]:
            e1name = get_name(sub_graph[0])
            e1name = "*" + e1name + "*"
        else:
            e1name = sub_graph[0]
            assert e1name[0] == "?"
        subgraph_explain = subgraph_explain.replace("?entity1", e1name)
    else:
        # type3
        if "ns:" in sub_graph[0]:
            e1name = get_name(sub_graph[0])
            e1name = "*" + e1name + "*"
        else:
            e1name = sub_graph[0]
            assert e1name[0] == "?"
        
        if "ns:" in sub_graph[2]:
            e2name = get_name(sub_graph[2])
            e2name = "*" + e2name + "*"
        else:
            e2name = sub_graph[2]
            assert e2name[0] == "?"
        subgraph_explain = subgraph_explain.replace("?entity1", e1name).replace("?entity2", e2name)
    
    subgraph_explain = f"Find {subgraph_explain}, assign it to {node}"
    # 处理exists问题
    return subgraph_explain

mid_pattern = r'ns:[m|g]\.[a-z0-9_]+'
type_pattern = r'ns:[a-z_]+\.[a-z_]+'
variable_pattern = r'\?[A-Za-z0-9_]+'
str_pattern = r'\"[A-Za-z0-9_\+\- ]+\"'
float_pattern = r"\"[-+]?\d+\.\d+\""
# integer_pattern = r'\"[-+]?\d+\"'

variable2integer_pattern = r'xsd:integer\(\?[A-Za-z0-9_]+\)'
variable2float_pattern = r'xsd:float\(\?[A-Za-z0-9_]+\)'
variable2str_pattern = r'str\(\?[A-Za-z0-9_]+\)'
variable2datetime_pattern = r'xsd:date[T|t]ime\(\?[A-Za-z0-9_]+\)'

equal_relation_explain = {"=": "be", "!=": "not be"}
number_relation_explain = {"<": "be smaller than", ">": "be larger than", "<=": "not be larger than", ">=": "not be smaller than"}
time_relation_explain = {"<": "be earlier than", ">": "be later than", "<=": "not be later than", ">=": "not be earlier than"}

def explain_filter(filter, id=None):
    s_filter = split_by_operators(filter)
    assert len(s_filter) == 3, f"{id}: not implement FILTER explain {filter}, {s_filter}"
    e1 = s_filter[0].strip()
    e2 = s_filter[2].strip()
    r = s_filter[1].strip()
    if re.fullmatch(variable_pattern, e1)!=None and (re.fullmatch(mid_pattern, e2) or re.fullmatch(type_pattern,e2)):
        # ?x = ns:XXX
        e2 = "*"+get_name(e2) + "*"
        return [f"{e1} should {equal_relation_explain[r]} {e2}"]
    elif re.fullmatch(variable_pattern, e1)!= None and "@en" in e2 and r == "=":
        # ?street_address = "2100 Woodward Avenue"@en
        e2_str = e2.split('@')[0]
        # print(f"{e1} should {equal_relation_explain[r]} a string {e2_str}")
        # raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
        return [f"{e1} should {equal_relation_explain[r]} a string {e2_str}"]
    elif e1 == "?trailers" and "http://" in e2 and r == "=":
        # ?trailers = http://youtu.be/0bdZWrW6HnA
        e2_str = f"\"{e2}\""
        return [f"{e1} should {equal_relation_explain[r]} a string {e2_str}"]
    elif re.fullmatch(variable2str_pattern, e1)!=None and re.fullmatch(str_pattern,e2):
        # str(?sk0) = "Country"
        e1_var = re.findall(variable_pattern, e1)[0]
        return [f"{e1_var} should {equal_relation_explain[r]} a string {e2}"]
        # str(?sk0) = "Country"
    
    elif re.fullmatch(variable_pattern, e1)!= None and re.fullmatch(float_pattern, e2)!=None and r == "=":
        # ?adjusted_value = "103696598044.0"
        # print(f"{e1} should {equal_relation_explain[r]} a float {e2}")
        return [f"{e1} should {equal_relation_explain[r]} a float {e2}"]
        

    elif re.fullmatch(variable_pattern, e1)!= None and re.fullmatch(str_pattern, e2)!=None and r == "=":
        # ?season_number = "0"
        # print(f"{e1} should {equal_relation_explain[r]} a string {e2}")
        return [f"{e1} should {equal_relation_explain[r]} a string {e2}"]
    elif re.fullmatch(variable2integer_pattern, e1)!= None and "^^<http://www.w3.org/2001/XMLSchema#integer>" in e2:
        # xsd:integer(?num) < "2"^^<http://www.w3.org/2001/XMLSchema#integer>
        if r in ["<", ">", "<=", ">="]:
            e1_var = re.findall(variable_pattern, e1)[0]
            e2_num = e2.split('^^')[0][1:-1]
            # print(f"{e1_var} should {number_relation_explain[r]} {e2_num}")
            return [f"{e1_var} should {number_relation_explain[r]} {e2_num}"]
        else:
            raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}") 
    
    elif re.fullmatch(variable2datetime_pattern, e1)!= None and "^^xsd:dateTime" in e2:
        # xsd:datetime(?sk1) <= "2015-08-10"^^xsd:dateTime
        e1_var = re.findall(variable_pattern, e1)[0]
        datetime_str = e2.split('^^')[0][1:-1]
        if datetime_str == "2015-08-10":
            datetime_str = "*NOW*"
        return [f"{e1_var} should {time_relation_explain[r]} {datetime_str}"]
    
    elif re.fullmatch(variable_pattern, e1) and "^^<http://www.w3.org/2001/XMLSchema#dateTime>" in e2:
        # ?from = "1943-03-20"^^<http://www.w3.org/2001/XMLSchema#dateTime>
        if r in ["<", ">", "<=", ">="]:
            # 处理时间关系
            e2_date_str = e2.split('^^')[0][1:-1]
            date_str_len = len(e2_date_str.split("-"))
            if date_str_len == 3:
                # ?num > "2009-01-02"^^<http://www.w3.org/2001/XMLSchema#dateTime>
                # print(f"{e1} should {time_relation_explain[r]} {e2_date_str}")
                # raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
                if e2_date_str == "2015-08-10":
                    e2_date_str = "*NOW*"
                return [f"{e1} should {time_relation_explain[r]} {e2_date_str}"]
            elif date_str_len == 2:
                # ?num < "1940"^^<http://www.w3.org/2001/XMLSchema#dateTime>
                e2_date_str = e2_date_str + "-01"
                # print(f"{e1} should {time_relation_explain[r]} {e2_date_str}")
                # raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
                return [f"{e1} should {time_relation_explain[r]} {e2_date_str}"]
            elif date_str_len == 1:
                # ?num < "1940"^^<http://www.w3.org/2001/XMLSchema#dateTime>
                e2_date_str = e2_date_str + "-01-01"
                # print(f"{e1} should {time_relation_explain[r]} {e2_date_str}")
                # raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
                return [f"{e1} should {time_relation_explain[r]} {e2_date_str}"]

            else:
                raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
        elif r == "=":
            e2_date_str = e2.split('^^')[0][1:-1]
            date_str_len = len(e2_date_str.split("-"))
            if date_str_len == 3:
                # print(e2_date_str)
                assert e2_date_str != "2015-08-10", "?var = NOW exists"
                e2_date_obj = datetime.strptime(e2_date_str, "%Y-%m-%d")
                next_day = e2_date_obj + relativedelta(days=1)
                e2_next_date_str = next_day.strftime("%Y-%m-%d")
                explain1 = f"{e1} should {time_relation_explain['>=']} {e2_date_str}"
                explain2 = f"{e1} should {time_relation_explain['<']} {e2_next_date_str}"
                # print(explain1, explain2)
                # raise Exception("DDDDDDDDDDDD")
                return [explain1, explain2]
            elif date_str_len == 2:
                e2_date_str = e2_date_str + "-01"
                e2_date_obj = datetime.strptime(e2_date_str, "%Y-%m-%d")
                next_month = e2_date_obj + relativedelta(months=1)
                e2_next_month_str = next_month.strftime("%Y-%m-%d")
                explain1 = f"{e1} should {time_relation_explain['>=']} {e2_date_str}"
                explain2 = f"{e1} should {time_relation_explain['<']} {e2_next_month_str}"
                # print(explain1, explain2)
                # raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
                return [explain1, explain2]
            elif date_str_len == 1:
                e2_date_str = e2_date_str + "-01-01"
                e2_date_obj = datetime.strptime(e2_date_str, "%Y-%m-%d")
                next_year = e2_date_obj + relativedelta(years=1)
                e2_next_year_str = next_year.strftime("%Y-%m-%d")
                explain1 = f"{e1} should {time_relation_explain['>=']} {e2_date_str}"
                explain2 = f"{e1} should {time_relation_explain['<']} {e2_next_year_str}"
                # print(explain1, explain2)
                return [explain1, explain2]
            else:
                raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
        else:
            raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
    
    elif re.fullmatch(variable2datetime_pattern, e1)!= None and re.fullmatch(variable2datetime_pattern, e2)!=None:
        # sd:float(?xl) > xsd:float(?l)
        e1_var = re.findall(variable_pattern, e1)[0]
        e2_var = re.findall(variable_pattern, e2)[0]
        return [f"{e1_var} should {time_relation_explain[r]} {e2_var}"]
    elif re.fullmatch(variable_pattern, e1)!= None and re.fullmatch(variable_pattern, e2)!=None:
        if e1 in ['?from', '?to', '?start', '?end'] and e2 in ['?from', '?to', '?start', '?end']:
            # ?from < ?end
            return [f"{e1} should {time_relation_explain[r]} {e2}"]
        elif r in ['=','!=']:
            #?x = ?y
            return [f"{e1} should {equal_relation_explain[r]} {e2}"]
        else:
            raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")
    elif re.fullmatch(variable2float_pattern, e1)!= None and re.fullmatch(variable2float_pattern, e2)!=None:
        # sd:float(?xl) > xsd:float(?l)
        e1_var = re.findall(variable_pattern, e1)[0]
        e2_var = re.findall(variable_pattern, e2)[0]
        return [f"{e1_var} should {number_relation_explain[r]} {e2_var}"]
    
        
    else:
        raise Exception(f"{id}: not implement FILTER explain {filter}, {e1} {r} {e2}")

explain_data = []
for d in tqdm(data):
    if d['id'] in ["WebQTest-125_1a62d9d147cf3e424ef19ee9201200fd","WebQTrn-1719_a43a955cf355469ce6d17c2e05867b29"]:
        continue
    if "splited_graph" not in d:
        print(f"no splited_graph in {d['id']}")
        continue
    
    all_rel = d['all_rel']
    sparql_explain = []
    

    for sub_graph in d["splited_graph"]:
        node = sub_graph[-1]
        subgraph_explain = explain_find(sub_graph, all_rel)
        node_filter_explain = []
        if all_rel[node]['is_try']:
            assert len(all_rel[node]['filter']) == 1, f"{d['id']}: more than 1 filter try"
            filter_explains = explain_filter(all_rel[node]['filter'][0], id=d['id'])
            assert len(filter_explains) == 1, f"{d['id']}: more than 1 filter try explain"
            subgraph_explain = subgraph_explain + f". If {node} exists, {filter_explains[0]}"
        else:
            if len(all_rel[node]['filter'])!= 0:
                for f in all_rel[node]['filter']:
                    filter_explains = explain_filter(f, id=d['id'])
                    for f_explain in filter_explains:
                        node_filter_explain.append(f"Make sure {f_explain}")
                    # node_filter_explain.append(f"Make sure {filter_explain}")
        sparql_explain.append(subgraph_explain)
        for f_explain in node_filter_explain:
            sparql_explain.append(f_explain)
    
    if d['order'] != None:
        if d['order']['order'] == "ASC":
            order = "ascending"
        elif  d['order']['order'] == "DESC":
            order = "descending"
        else:
            raise Exception(f"{d['id']}: not implement order {d['order']}")
        
        if "datetime" in d['order']['var'] or "dateTime" in d['order']['var']:
            var = re.findall(variable_pattern, d['order']['var'])[0]
            var = "datetime "+var
        elif "float" in d['order']['var']:
            var = re.findall(variable_pattern, d['order']['var'])[0]
            var = "float "+var
        elif "integer" in d['order']['var']:
            var = re.findall(variable_pattern, d['order']['var'])[0]
            var = "integer "+var
        elif d['order']['var'][0] == "?":
            var = d['order']['var']
        else:
            raise Exception(f"{d['id']}: not implement order {d['order']}")

        if d['order']['start'] ==0 and d['order']['len'] == 1:
            order_explain = f"Sort the result based on {var} in {order} order and keep the first result"
            # print(order_explain)
            sparql_explain.append(order_explain)
        elif d['order']['start'] ==1 and d['order']['len'] == 1:
            order_explain = f"Sort the result based on {var} in {order} order and keep the second result"
            # print(order_explain)
            # raise Exception(f"{d['id']}: not implement order {d['order']}")
            sparql_explain.append(order_explain)
        elif d['order']['start'] ==0 and d['order']['len'] > 1:
            order_explain = f"Sort the result based on {var} in {order} order and keep the top {d['order']['len']} result"
            # print(order_explain)
            # raise Exception(f"{d['id']}: not implement order {d['order']}")
            sparql_explain.append(order_explain)
        else:
            raise Exception(f"{d['id']}: not implement order {d['order']}")
    
    d['all_sparql_explain'] = sparql_explain
    final_explain = ""
    for step_cnt, exp in enumerate(sparql_explain):
        final_explain += f"Step{step_cnt+1}: {exp}.\n"
    final_explain = final_explain+f"Finally the answer is {d['AnsE']}.\n"
    d['sparql_explain'] = final_explain
    explain_data.append(d)
    
    # print(final_explain)
    # print(d['graph_sparql'])
    # print("====================")

with open("output/All_cached_mid_names.json","w") as f:
    json.dump(mid_names,f )

with open("output/merge_explain_data.json", "w") as f:
    json.dump(explain_data, f)
