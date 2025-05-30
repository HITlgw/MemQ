import networkx as nx
import re
import json



def get_unused_name(list, name):
    if name not in list:
        return name
    else:
        i = 0
        while name + str(i) in list:
            i += 1
        return name + str(i)
cnt1 = 0
cnt = 0

if __name__ == "__main__"

    # with open("output\webqsp_train_parse.json", "r") as f:
    with open("output\cwq_train_parse.json", "r") as f:
        train_parse = json.load(f)

    cleaned_data = []
    for idx,d in enumerate(train_parse):
        nodelist = set()
        allmid = set()
        bad_node_edges = []
        for e in d['where']:
            if "ns:" in e[0]:
                allmid.add(e[0])
            if "ns:" in e[2]:
                allmid.add(e[2])
            if ("ns:" not in e[0] and "?" not in e[0]) or ("ns:" not in e[2] and "?" not in e[2]):
                bad_node_edges.append(e)
            nodelist.add(e[0])
            nodelist.add(e[2])
        
        if len(bad_node_edges)>0:
            # 所有bad node 都在e[2]中
            for e in bad_node_edges:
                d['where'].remove(e)
                nodelist.add(e[0])
                tail = get_unused_name(nodelist, "?"+e[1].split(".")[-1])
                nodelist.add(tail)
                d['where'].append([e[0], e[1], tail])
                d['filter'].append(f"{tail} = {e[2]}")
        

        for ext in d['exists']:
            e = ext[1].split(" ")
            nodelist.add(e[0])
            nodelist.add(e[2])

        # 建图
        G = nx.DiGraph()
        for e in d['where']:
            G0 = nx.DiGraph(G)
            G0.add_edge(e[0], e[2], relation=e[1], is_try = False)
            if (not nx.is_directed_acyclic_graph(G0)) or len(nx.cycle_basis(nx.Graph(G0))) != 0:
                if "ns:" not in e[0] and "ns:" not in e[2]:
                    print(d['id'])
                    if e[2] != d['AnsE']:
                        tail = get_unused_name(nodelist, "?"+e[1].split(".")[-1])
                        nodelist.add(tail)
                        G.add_edge(e[0], tail, relation=e[1], is_try = False)
                        # TODO: 增加Filter
                        tmp = e[2]
                        d['filter'].append(f"{tail} = {tmp}")
                    else:
                        head = get_unused_name(nodelist, "?"+e[1].split(".")[-2])
                        nodelist.add(head)
                        G.add_edge(head, e[2], relation=e[1], is_try = False)
                        tmp = e[0]
                        d['filter'].append(f"{head} = {tmp}")
                else:
                    if ("ns:m." in e[2] or "ns:g." in e[2]) and e[2] in G.nodes():
                        tail = get_unused_name(nodelist, "?"+e[1].split(".")[-1])
                        nodelist.add(tail)
                        # TODO: 增加Filter
                        tmp = e[2]
                        try:
                            d['filter'].append(f"{tail} = {tmp}")
                        except:
                            print(d['id'])
                            print(d['ori_sparql'])
                    else:
                        tail = e[2]
                    
                    if ("ns:m." in e[0] or "ns:g." in e[0]) and e[0] in G.nodes():
                        head = get_unused_name(nodelist, "?"+ e[1].split(".")[-2])
                        nodelist.add(head)
                        # TODO: 增加Filter
                        tmp = e[0]
                        d['filter'].append(f"{head} = {tmp}")
                    else:
                        head = e[0]
                    
                    G.add_edge(head, tail, relation=e[1], is_try = False)
                    # else:
                    #     tail = get_unused_name(nodelist, "?"+e[1].split(".")[-1])
                    #     G.add_edge(e[0], tail, relation=e[1], is_try = False)
                        # TODO: 增加Filter
            else:
                G.add_edge(e[0], e[2], relation=e[1], is_try = False)

        for ext in d['exists']:
            e = ext[1].split(" ")
            G.add_edge(e[0], e[2], relation=e[1], is_try = True)
            tmp = ext[2].replace("FILTER", "").strip()[1:-1]
            d['filter'].append(tmp)
    
        # print(nx.to_dict_of_dicts(G))
        if not nx.is_directed_acyclic_graph(G) or len(nx.cycle_basis(nx.Graph(G)))>0:
            print(d['id'], "not DAG")
            cnt += 1
            # print(d['BegE'])
            print(d['ori_sparql'])
            
            # print(d['question'])
            # print(idx)
            continue
        
        # 找主要路径
        
        allmid = list(allmid)
        main_path = []
        if d['BegE'] in allmid:
            try:
                all_path = nx.all_simple_paths(nx.Graph(G), source=d['BegE'], target=d['AnsE'])
                # if len(all_path) > 1:
                #     print("begE more than 1 paths")
                for p in all_path:
                    cur_path = []
                    for tmp in p:
                        cur_path.append(tmp)
                    if len(cur_path) > len(main_path):
                        main_path = cur_path.copy()
                    # if len(list(p)) > len(main_path):
                    #     main_path = list(p)
            except:
                print(idx)
                print(f"{d['id']} main mid wrong")
                # print(d['BegE'])
                # print(d['ori_sparql'])
                # continue
        
        if len(main_path) == 0:
            for mid in allmid:
                try:
                    all_path = nx.all_simple_paths(nx.Graph(G), source=mid, target=d['AnsE'])
                    for p in all_path:
                        cur_path = []
                        for tmp in p:
                            cur_path.append(tmp)
                        if len(cur_path) > len(main_path):
                            main_path = cur_path.copy()
                            # print(f"change BegE from {d['BegE']} to {mid}")
                            d['BegE'] = mid
                except Exception as e:
                    print(f"no path for {mid} to {d['AnsE']}")
                    
        if len(main_path) == 0 :
            if len(allmid) != 0:
                cnt +=1
                print(allmid)
                print(f"{d['id']} no main path")
                print(d['ori_sparql'])
                continue
            # 没有Main Entity的情况 直接删除
            else:
                # print(d['ori_sparql'])
                # 有entity没main path
                print(f"{d['id']} no main entity")
                continue
        assert "ns:" in main_path[0], f"{d['id']}"
        d['BegE'] = main_path[0]


        # 确定访问顺序
        nodeorder = []
        components = list(nx.connected_components(nx.Graph(G)))
        if len(components) == 1:
            main_component = list(components[0])
            other_component = None
        elif len(components) == 2:
            if main_path[0] in components[0]:
                main_component = list(components[0])
                other_component = list(components[1])
            else:
                main_component = list(components[1])
                other_component = list(components[0])
        else:
            raise Exception("more than 2 components")
        
        begin_mid = []
        if not other_component:
            for node in main_path:
                nodeorder.append(node)
            dfs = nx.dfs_preorder_nodes(nx.Graph(G), source= main_path[0])
            for node in dfs:
                if node not in nodeorder:
                    nodeorder.append(node)
            begin_mid.append(main_path[0])
        else:
            # print(d['id'])
            for mid in allmid:

                if mid in main_component:
                    continue
                else:
                    assert len(begin_mid) == 0, "mid error in other_component"
                    begin_mid.append(mid)
                    
                    dfs = nx.dfs_preorder_nodes(nx.Graph(G), source= mid)
                    nodeorder.append(mid)
                    for node in dfs:
                        if node not in nodeorder:
                            nodeorder.append(node)
            
            begin_mid.append(main_path[0])
            for node in main_path:
                nodeorder.append(node)
            main_dfs = nx.dfs_preorder_nodes(nx.Graph(G), source= main_path[0])
            for node in main_dfs:
                if node not in nodeorder:
                    nodeorder.append(node)
        
        # 重命名非起始mid节点
        for mid in allmid:
            # 除了起始 mid 外，不会有其它节点超过 1 度
            # if G.degree(mid) > 1 and mid not in begin_mid:
            #     flag = True
            #     print(mid)
            if mid not in begin_mid :
                # print(begin_mid)
                assert G.degree(mid) == 1, mid+ d['id']
                if len(list(G.in_edges(mid, data=True))) != 0:
                    edge = list(G.in_edges(mid, data=True))[0]
                    rel = edge[2]['relation']
                    newname = get_unused_name(nodelist,"?"+rel.split(".")[-1])
                    nodelist.add(newname)
                else:
                    edge = list(G.out_edges(mid, data=True))[0]
                    rel = edge[2]['relation']
                    newname = get_unused_name(nodelist,"?"+rel.split(".")[-2])
                    nodelist.add(newname)
                nx.relabel_nodes(G, {mid: newname}, copy=False)
                d['filter'].append(f"{newname} = {mid}")
                new_order = []
                for node in nodeorder:
                    if node == mid:
                        new_order.append(newname)
                    else:
                        new_order.append(node)
                nodeorder=new_order
                # flag = True
        Gnodes = list(G.nodes())
        Gnodes.sort()
        Gorder = list(nodeorder)
        Gorder.sort()
        assert Gnodes == Gorder, f"not same {idx}"
        father_rel = {}
        for x in allmid:
            if x not in begin_mid:
                assert x not in Gorder, f"{x} in Gorder"
            else:
                for e in nx.dfs_edges(nx.Graph(G), source=x):
                    assert e[1] not in father_rel, f"{e[1]} in father_rel"
                    father_rel[e[1]] = e[0]
        
        all_rel = {}
        for node in Gorder:
            if "ns:" not in node:
                all_rel[node] = {"father":father_rel[node], "filter":[]}
                edge_data = G.get_edge_data(father_rel[node], node)
                if edge_data:
                    all_rel[node]["relation"] = edge_data["relation"]
                    all_rel[node]['reversed'] = False
                    all_rel[node]['is_try'] = edge_data['is_try']
                else:
                    edge_data = G.get_edge_data(node, father_rel[node])
                    all_rel[node]["relation"] = edge_data["relation"]
                    all_rel[node]['reversed'] = True
                    all_rel[node]['is_try'] = edge_data['is_try']
                assert node in father_rel
        
        for f in d['filter']:
            variable_pattern = r'\?[A-Za-z0-9_]+'
            matches = re.findall(variable_pattern, f)
            if len(matches) != 1 and len(matches)!= 2:
                print(f)
            all_rel[matches[0]]["filter"].append(f)
        # print(nodeorder)
        # print(nx.to_dict_of_dicts(G))
        # print(father_rel)
        d['G'] = nx.to_dict_of_dicts(G)
        d['nodeorder'] = nodeorder
        d['main_path'] = main_path
        d['all_rel'] = all_rel
        cleaned_data.append(d)

    # with open("output\webqsp_train_graph.json", "w") as f:
    with open("output\cwq_train_graph.json", "w") as f:
        json.dump(cleaned_data, f)