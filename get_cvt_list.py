import json
from sparql_util import get_result
from tqdm import tqdm
import networkx as nx
def get_unused_name(list, name):
    if name not in list:
        return name
    else:
        i = 0
        while name + str(i) in list:
            i += 1
        return name + str(i)

with open("output/cwq_train_graph.json","r") as f:
# with open("output/webqsp_train_graph.json","r") as f:
    train_graph = json.load(f)

not_evluable = []
for d in tqdm(train_graph):
    # if not d['id'] == "WebQTrn-757_ddd2303e3e67cfaa24a1990199bbc60a":
    #     continue
    # print("===============")
    # print(d['id'])

    all_rel = d['all_rel']
    # print(d['ori_sparql'])
    # print("=====")
    nodelist = []
    cvt_list = {}
    for n in d['nodeorder']:
        nodelist.append(n)
        cvt_list[n] = None
    all_cause = [f"FILTER (!isLiteral({d['AnsE']}) OR lang({d['AnsE']}) = '' OR langMatches(lang({d['AnsE']}), 'en'))"]
    
    for node in d['nodeorder']:
        if "ns:" in node:
            cvt_list[node] = False
            continue
        if not all_rel[node]['is_try']:
            # print(node, all_rel[node])
            if not all_rel[node]['reversed']:
                if " UNION " in all_rel[node]['relation']:
                    relations = all_rel[node]['relation'].split(" UNION ")
                    assert len(relations) == 2
                    # print(relations)
                    if " + " in relations[0] and " + " in relations[1]:
                        # print("888888",relations[0].split(" + "))
                        # print("888888",relations[1].split(" + "))
                        [sube1, sube2] = relations[0].split(" + ")
                        tmpname1 = get_unused_name(nodelist, "?tmp")
                        nodelist.append(tmpname1)
                        [sube3, sube4] = relations[1].split(" + ")
                        tmpname2 = get_unused_name(nodelist, "?tmp")
                        nodelist.append(tmpname2)
                        # print(f"{{ {all_rel[node]['father']} {sube1} {tmpname1} .\n {tmpname1} {sube2} {node} }}\nUNION\n{{ {all_rel[node]['father']} {sube3} {tmpname2} .\n {tmpname2} {sube4} {node} }}")
                        all_cause.append(f"{{ {all_rel[node]['father']} {sube1} {tmpname1} .\n {tmpname1} {sube2} {node} }}\nUNION\n{{ {all_rel[node]['father']} {sube3} {tmpname2} .\n {tmpname2} {sube4} {node} }}")
                    else:
                        # print(f"{{ {all_rel[node]['father']} {relations[0]} {node} }}\nUNION\n{{ {all_rel[node]['father']} {relations[1]} {node} }}")
                        all_cause.append(f"{{ {all_rel[node]['father']} {relations[0]} {node} }}\nUNION\n{{ {all_rel[node]['father']} {relations[1]} {node} }}")
                else:
                    # print(f"{all_rel[node]['father']} {all_rel[node]['relation']} {node}")
                    all_cause.append(f"{all_rel[node]['father']} {all_rel[node]['relation']} {node}")
            else:
                if " UNION " in all_rel[node]['relation']:
                    relations = all_rel[node]['relation'].split(" UNION ")
                    assert len(relations) == 2
                    if " + " in relations[0] and " + " in relations[1]:
                        [sube1, sube2] = relations[0].split(" + ")
                        tmpname1 = get_unused_name(nodelist, "?tmp")
                        nodelist.append(tmpname1)
                        [sube3, sube4] = relations[1].split(" + ")
                        tmpname2 = get_unused_name(nodelist, "?tmp")
                        nodelist.append(tmpname2)
                        # print(f"{{ {all_rel[node]['father']} {sube1} {tmpname1} .\n {tmpname1} {sube2} {node} }}\nUNION\n{{ {all_rel[node]['father']} {sube3} {tmpname2} .\n {tmpname2} {sube4} {node} }}")
                        all_cause.append(f"{{ {node} {sube1} {tmpname1} .\n {tmpname1} {sube2} {all_rel[node]['father']} }}\nUNION\n{{ {node} {sube3} {tmpname2} .\n {tmpname2} {sube4} {all_rel[node]['father']} }}")

                        # raise Exception("Not implemet Reversed UNION + ")
                    else:
                        # print(f"{{ {all_rel[node]['father']} {relations[0]} {node} }}\nUNION\n{{ {all_rel[node]['father']} {relations[1]} {node} }}")
                        all_cause.append(f"{{ {node} {relations[0]} {all_rel[node]['father']} . }}\nUNION\n{{ {node} {relations[1]} {all_rel[node]['father']} . }}")
                else:
                    # print(f"{node} {all_rel[node]['relation']} {all_rel[node]['father']}")
                    all_cause.append(f"{node} {all_rel[node]['relation']} {all_rel[node]['father']}")
                
            for f in all_rel[node]['filter']:
                # print(f"FILTER({f})")
                all_cause.append(f"FILTER({f})")

        else:
            tmpname = get_unused_name(nodelist, "?tmp")
            assert len(all_rel[node]['filter']) == 1 and not all_rel[node]['reversed']
            
            nodelist.append(tmpname)
            # print(f"FILTER(NOT EXISTS {{ {all_rel[node]['father']} {all_rel[node]['relation']} {tmpname} }} || EXISTS {{{all_rel[node]['father']} {all_rel[node]['relation']} {node} . FILTER({all_rel[node]['filter'][0]}) }})")
            all_cause.append(f"FILTER(NOT EXISTS {{ {all_rel[node]['father']} {all_rel[node]['relation']} {tmpname} }} || EXISTS {{{all_rel[node]['father']} {all_rel[node]['relation']} {node} . FILTER({all_rel[node]['filter'][0]}) }})")
            # raise Exception("not implement is try")
    where = " .\n".join(all_cause)
    orderby_cause = ""
    
    if d['order'] != None:
        if d['order']['start'] == 0:
            orderby_cause = f"ORDER BY {d['order']['order']}({d['order']['var']})\nLIMIT {d['order']['len']}"
        else:
            orderby_cause = f"ORDER BY {d['order']['order']}({d['order']['var']})\nLIMIT {d['order']['len']}\nOFFSET {d['order']['start']}"
    # graph_sparql = f"PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT {d['AnsE']}\nWHERE \n{{\n{where}\n}}\n"
    graph_sparql = f"PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT {d['AnsE']}\nWHERE \n{{\n{where}\n}}\n{orderby_cause}"
    d['graph_sparql'] = graph_sparql
    d['orderby'] = orderby_cause
    d['all_cause'] = all_cause

    try:
        graph_res = get_result(graph_sparql, d['AnsE'])
    except Exception as e:
        graph_res = []
    
    if len(graph_res) ==0:
        new_cause = []
        for x in all_cause:
            if "FILTER" not in x:
                new_cause.append(x)
        all_cause = new_cause
        where = " .\n".join(new_cause)
        orderby_cause = ""

        graph_sparql = f"PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT {d['AnsE']}\nWHERE \n{{\n{where}\n}}\n{orderby_cause}"
        try:
            graph_res = get_result(graph_sparql, d['AnsE'])
        except Exception as e:
            graph_res = []
    
    if len(graph_res) == 0:
        print(f"{d['id']} not evaluable")
        d['cvt_list'] = None
        not_evluable.append(d['id'])
        continue
    
    G = nx.Graph(d['G'])

    for node in G.nodes():
        if "ns:" in node:
            cvt_list[node] = False
            continue
        
        # 特殊关系判断
        if all_rel[node]['relation'] in [ "ns:film.actor.film", "ns:government.government_office_or_title.office_holders","ns:organization.organization.leadership","ns:government.political_appointer.appointees","ns:education.educational_institution.students_graduates","ns:film.film.release_date_s", "ns:film.film_character.portrayed_in_films","ns:government.governmental_body.members","ns:government.politician.government_positions_held","ns:government.governmental_jurisdiction.governing_officials"]:
                # 后面的是CVT
            if not all_rel[node]['reversed']:
                if G.degree(node) == 1:
                    print(f"{d['id']}: CVT node in leaf, please check")
                cvt_list[node] = True
                cvt_list[all_rel[node]['father']] = False
            else:
                cvt_list[node] = False
                cvt_list[all_rel[node]['father']] = True
            continue
        elif all_rel[node]['relation'] in ["ns:film.performance.film","ns:organization.leadership.person","ns:organization.leadership.role","ns:government.government_position_held.office_holder", "ns:government.government_position_held.from", "ns:education.education.student","ns:government.government_position_held.governmental_body","ns:film.performance.character", "ns:government.government_position_held.basic_title","ns:government.government_position_held.district_represented","ns:location.mailing_address.citytown","ns:government.government_position_held.office_position_or_title","ns:government.government_position_held.appointed_by"]:
            # 前面的是CVT
            if all_rel[node]['reversed']:
                if G.degree(node) == 1:
                    print(f"{d['id']}: CVT node in leaf, please check")
                cvt_list[node] = True
                cvt_list[all_rel[node]['father']] = False
            else:
                cvt_list[node] = False
                cvt_list[all_rel[node]['father']] = True
            continue
        if G.degree(node) == 1:
            cvt_list[node] = False
            continue
        else:       
            check_cause = []
            for w in all_cause:
                check_cause.append(w)
            check_cause.append(f"FILTER(EXISTS{{ {node} ns:type.object.name ?nodename }})")
            check_where = " .\n".join(check_cause)
            check_sparql = f"PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT {d['AnsE']}\nWHERE \n{{\n{check_where}\n}}\n{orderby_cause}"
            try:
                check_result = get_result(check_sparql, d['AnsE'])
                # print(node, check_result)
            except Exception as e:
                check_result = []
            if len(check_result) > 0:
                cvt_list[node] = False
            elif len(check_result) == 0 and len(graph_res)>0:
                cvt_list[node] = True
            else:
                print(f"{d['id']} not expected check result for {node}")
    d['cvt_list'] = cvt_list
    # print(d['graph_sparql'])
    # print(d['cvt_list'])

with open("output/cwq_train_cvt_list.json","w") as f:
# with open("output/webqsp_train_cvt_list.json","w") as f:
    json.dump(train_graph, f)
print(not_evluable)