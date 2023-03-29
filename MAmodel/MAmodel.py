from __future__ import annotations
import graphlib
from operator import le
from pprint import pprint
from turtle import color
import typing
from matplotlib import use
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import random
import itertools 
import copy
import sys
import json

from typing import Callable, Optional,Union,Any
import yaml

from typing import TYPE_CHECKING


sys.setrecursionlimit(10**7) 


def _attach_scc_id(self)->tuple[Union[nx.MultiDiGraph,nx.DiGraph],int]:
        """attach scc_id to nx.Digraph and nx.MultiDigraph
        
        Attach scc_id (same value for same scc) as an attribute to the graph.

        Returns:
            tuple[Union[nx.MultiDiGraph,nx.DiGraph],int]: Graph after scc_id is assigned, Number of SCCs.
        """
        assert(isinstance(self,nx.MultiDiGraph) or isinstance(self,nx.DiGraph))

        scc_id = 1
        
        for comp in sorted(nx.strongly_connected_components(self), key=len, reverse=True):
            for node in comp:
                self.nodes[node]["scc_id"] = scc_id
            scc_id += 1

        return self,scc_id-1



class MAModel():
    """MA model

    Attributes:
        graph(nx.MultiDigraph):the graph of the model. This has a lot of attributes such as graph.graph["label_list"].More information about the attributes attached are located in the ripository.
        only_attack(bool):Specifies whether the model is likely to contain edges other than the attack edges as True or False. self.convert_subset_cond_to_simple_cond don't work properly when only_attack attributes is False.
    """

    def __init__(self):
        
        self.graph : nx.MultiDiGraph= None
        self.only_attack = None
        nx.MultiDiGraph.attach_scc_id = _attach_scc_id
        nx.DiGraph.attach_scc_id = _attach_scc_id

        self.__DASH1 = 10000       #support -> attack
        self.__DASH2 = 100000000   #complex_cond -> simple_cond 

        return
    
    def read_yaml(self,path:str) -> None:
        """
        Read the .yml file specified to create the model.

        Args:
            path (str): the path to the .yml file

        """



        self.graph = nx.MultiDiGraph()
        G = self.graph

        ymlstr = ""
        with open(path,'r') as f:
            ymlstr = f.read()


        ymlinfo = yaml.full_load(ymlstr)

        # constract graph

        nodes = ymlinfo["nodes"]
        G.add_nodes_from(nodes)

        edgeinfo = ymlinfo["edges"]

        only_attack = True

        for content in edgeinfo:
            u = content[0]
            v = content[1]
            is_attack = content[2]

            only_attack = only_attack and is_attack

            color = "hogehoge"

            if is_attack:
                color = "red"
            else:
                color = "blue"


            G.add_edge(u,v,attack=is_attack,color=color)
        
        self.only_attack = only_attack

        # setting attributes with yaml

        # graph

        G.graph['label_list'] = ymlinfo["attr_graph"]["label_list"]

        # node

        attr_node = ymlinfo["attr_node"]
        
        for node in G.nodes():
            G.nodes[node]['label'] = attr_node['label'][node]
            G.nodes[node]['skew_type'] = attr_node['skew_type'][node]


            if not attr_node["use_subset_cond"]:
                G.nodes[node]['conditions'] = [ tuple(c) for c in  attr_node['conditions'][node] ]
            else:
                def subset_to_tuple(c):
                    c[3] = tuple(c[3])
                    return c
                G.nodes[node]['conditions'] = [ tuple(subset_to_tuple(c)) for c in  attr_node['conditions'][node] ]
            
            if "weights" not in attr_node:
                G.nodes[node]['weight'] = 1
                print("Warning: weight is not specified in the model. weight is set to 1.",file=sys.stderr)
            else :
                G.nodes[node]['weight'] = attr_node['weights'][node]

            if 'opinion' in attr_node:
                G.nodes[node]['opinion'] = attr_node['opinion'][node]




        return

    def save_yaml(self,path:str = "output.yml"):
        """
        save the model in .yml format.
        you can use the saved model using read_yaml method.

        Args:
            path (str, optional): path to the new .yml file. Defaults to "output.yml".

        """

        content = {
            "nodes" : [],
            "edges" : [],
            "attr_graph" : {
                "label_list" : []
            },
            "attr_node":{
                "label" : {},
                "skew_type":{},
                "use_subset_cond":{},
                "conditions":{},
                "weights":{}       
            }
        }

        content["nodes"] = list(self.graph.nodes)
        
        for (u,v,c) in self.graph.edges(keys=False,data="attack"):
            content["edges"].append([u,v,c])
        
        content["attr_graph"]["label_list"] = self.graph.graph["label_list"]

        use_subset_cond = False

        def subset_to_list(c):

            if len(c) == 3:
                return c
            if len(c) == 4:
                return [c[0],c[1],c[2],list(c[3])]
            
            assert(False,"error")

            return

        for node in self.graph.nodes:
            
            content["attr_node"]["label"][node] = self.graph.nodes[node]["label"]
            content["attr_node"]["skew_type"][node] = self.graph.nodes[node]["skew_type"]
            content["attr_node"]["conditions"][node] = [subset_to_list(c) for c in self.graph.nodes[node]["conditions"]]        
            use_subset_cond = len(self.graph.nodes[node]["conditions"][0]) == 4

            content["attr_node"]["weights"][node] = self.graph.nodes[node]["weight"]

            if "opinion" in self.graph.nodes[node]:

                if "opinion" not in content["attr_node"]:
                    content["attr_node"]["opinion"] = {}
                content["attr_node"]["opinion"][node] = self.graph.nodes[node]["opinion"]
        
        content["attr_node"]["use_subset_cond"] = use_subset_cond


        with open(path,"w") as file:
            yaml.dump(content,file)
        
        return
            




    def init_graph(self,num_vertex:int = 10,max_indegree:int = 4,max_outdegree:int = 4,only_attack = False,avoid_self_loop = False,attach_weight = True)->nx.MultiDiGraph:
        """initialize the graph
        Create the initial graph of a random test. Instead of receiving the parameters for graph generation from the standard input, the graph is created from the arguments.
        In addition, this also assign [1,2,3] to the "label_list" of the graph.

        Args:
            num_vertex (int, optional): the number of vertices. 12 or so will take several minutes to enumerate all the labels. Defaults to 10.
            max_indegree (int, optional): maximum number of indegrees allowed. Defaults to 4.
            max_outdegree (int, optional): maximum number of outdegrees allowed. Defaults to 4.
            only_attack (bool, optional): specify whether to allow support on the edge.
            avoid_self_loop (bool, optional): specify whether to avoid creating self-loops. Defaults to False.
        
        Returns:
            nx.MultiDigraph : generated graph (same id as self.graph)


        """

        self.only_attack = only_attack
        
        G = nx.MultiDiGraph()
        G.add_nodes_from(range(num_vertex))

        max_num_edge = min(max_indegree,max_outdegree) * num_vertex
        
        num_edge = max_num_edge * random.random() * (random.random() ** 0.3) # The number of EDGEs is biased toward the smaller


        cnt_edges = 0
        
        doubled = set([]) # Check for the same in the edges. (Tail,Head,Attack)

        
        failed_num = 0

        while cnt_edges < num_edge:
            
            if failed_num == num_vertex * 2+1:
                break
            
            tail = random.randint(0,num_vertex-1)
            head = random.randint(0,num_vertex-1)
            
            if only_attack:
                attack = 1
            else:
                attack = random.randint(1,2) 
            
            if len(G.out_edges(nbunch=tail)) >= max_outdegree or len(G.in_edges(nbunch=head)) >= max_indegree or (tail,head,attack) in doubled:
                failed_num += 1
                continue

            if avoid_self_loop and tail == head:
                failed_num += 1
                continue
            
            doubled.add((tail,head,attack))
            failed_num = 0
            
            attack = (attack == 1)
            color = ("red" if attack else "blue")
            G.add_edge(tail,head,attack = attack,color = color)
            cnt_edges += 1
        
        self.graph = G
        self.graph.graph['label_list'] = [1,2,3]

        # attach weight to each node

        for node in G.nodes():
            if attach_weight:
                G.nodes[node]['weight'] = random.randint(1,5)
            else:
                G.nodes[node]['weight'] = 1

        return G


    def attach_label_randomly(self):
        """Give the model a random real label.
        """

        G = self.graph
        for node in G.nodes():
            G.nodes[node]['label'] = random.choice(G.graph['label_list'])

        return


    def attach_scc_id(self)->tuple[nx.MultiDiGraph,int]:
        """
        Apply the scc algorithm to the graph and attach scc_id (same value for the same scc) as an attribute.
        Side Effect: Assign scc_id to the model's graph


        Returns:
            tuple[nx.MultiDiGraph,int]: Graph after assignment, number of SCCs.

        """
        G = self.graph
        scc_id = 1
        
        for comp in sorted(nx.strongly_connected_components(G), key=len, reverse=True):
            for node in comp:
                G.nodes[node]["scc_id"] = scc_id
            scc_id += 1
        
        
        return G,scc_id-1


    def attach_skew_types(self,only:str = 'neutral')->nx.MultiDiGraph:
        """
        give skew_type as an attribute of a vertex of a graph at random.

        'neutral' is neutral.
        'L1' is l1-skew.
        'L2' is l2-skew.'

        Args:
            only(str): [specify restriction on skew type to be granted." L1", "L2", "neutral", "any" can be specified, 
            and if any is specified, the type is not limited."
            If "neutral" is specified, only neutral is assigned as skew type.
            The same applies other skew labels

        Returns:
            nx.MultiDiGraph: [Graph after skew_type is given].
        """

        G = self.graph
        
        for node in list(G.nodes):
            skew_types = ['neutral','L1','L2']
            G.nodes[node]['skew_type'] = skew_types[random.randint(0,2)]
            #print(skew_types[random.randint(0,2)])
            
            if only in ['L1','L2','neutral']:
                G.nodes[node]['skew_type'] = only
        
        return G


    def attach_conditions(self,use_extended_conditions : bool = False) -> nx.MultiDiGraph:
        """attach conditions to the MA model

        Conditional data is randomly given to MAModel.
        If extended conditional data is not used, conditional data in the form [(+,n1,n2),(-,m1,m2)] is given.
        Extended condition data means [(+,3,4,(1,2,3,4,5))] etc.
        The subset of predecessors of the vertices in the condition data is represented by a tuple, and each condition data is placed in a list.

        Args:
            use_extended_conditions (bool) : Whether extended condition data is used or not.1~5 extended condition data are given for each vertex.

        Returns:
            [nx.MultiDigraph]: [graph with condition data].
        """

        # Use the form (sign,x,y) for the case where the subset of predecessors is not used.
        if not use_extended_conditions:

            G = self.graph
            

            # Add a condition attribute to a vertex before giving the vertex condition data.
            # We don't want to have exactly the same conditions, so we'll manage the condition data by set for now.
            for index in list(G.nodes):
                G.nodes[index]["conditions"] = set([])
            
            # Give each vertex two condition data. 
            for index in list(G.nodes):
                
                for sign in ['+','-']:
                    
                    # Upper limit of random numbers for use in generating condition data (number of edges extending from within predecessors + 1)
                    random_max = len(list(G.predecessors(index))) + 1
                    
                    n1 = 0
                    n2 = random_max
                    
                    m1 = 0
                    m2 = random_max
                    
                    boundary_tuple = (-100,-100)
                    
                    if sign == '+':
                        x1 = random.randint(n1,n2) 
                        x2 = random.randint(x1,n2)
                        boundary_tuple = (x1,x2)
                    else:
                        y1 = random.randint(m1,m2)
                        y2 = random.randint(y1,m2)
                        boundary_tuple = (y1,y2)

                    G.nodes[index]['conditions'].add((sign,*boundary_tuple))
                    
                # Change the set to list.
                G.nodes[index]['conditions'] = list(G.nodes[index]['conditions'])
                    

            return G

        #For the case of using extended condition data
        else:

            def generate_subset(S:tuple) -> tuple:
                """[Randomly generate a subset of the tuple given the tuple of pred."].

                Args:
                    S (tuple): [tuple of predecessor].

                Returns:
                    tuple: [Returns the empty set if the generated subset.input is the empty set. Otherwise, return a non-empty set."]
                """
                
                res_list = []
                
                if S == ():
                    return ()
                
                set_size = len(S)
                
                bits_max = (1<<set_size) - 1
                
                bits = random.randint(1,bits_max)
                
                for i in range(set_size):
                    if ((bits >> i) & 1):
                        res_list.append(S[i])
                
                res_list.sort()
                return tuple(res_list)

            G = self.graph

            # Add a condition attribute to a vertex before giving the vertex condition data.
            # We don't want to have exactly the same conditions, so we'll manage the condition data by set for now.
            for index in list(G.nodes):
                G.nodes[index]["conditions"] = set([])
            
            # Give 1-5 condition data for each vertex 
            for index in list(G.nodes):

                num_conditions = random.randint(1,5)
                
                for i in range(num_conditions):

                    sign = random.choice(['+','-'])
                

                    # Createing a subset from the predecessors
                    pred_subset = generate_subset(tuple(G.predecessors(index)))
                    
                    # Upper limit of random numbers for use in generating condition data (number of edges extending from within predecessors + 1)
                    random_max = 0
                    
                    for u,v,k in list(G.in_edges(nbunch=index,keys=True)):
                        assert(v == index)
                        if u in pred_subset:
                            random_max += 1
                        
                    random_max += 1
                    
                    n1 = 0
                    n2 = random_max
                    
                    m1 = 0
                    m2 = random_max
                    
                    boundary_tuple = (-100,-100)
                    
                    if sign == '+':
                        x1 = random.randint(n1,n2) 
                        x2 = random.randint(x1,n2)
                        boundary_tuple = (x1,x2)
                    else:
                        y1 = random.randint(m1,m2)
                        y2 = random.randint(y1,m2)
                        boundary_tuple = (y1,y2)

                    G.nodes[index]['conditions'].add((sign,*boundary_tuple,pred_subset))
                    
                # Chanage the set to the list.
                G.nodes[index]['conditions'] = list(G.nodes[index]['conditions'])
                    
            return G




    def visualize(
        self,
        notes = "",
        title = "result",
        path_to_save_dir="generated_pic/",
        vis_features : list[str] = ['label','conditions','predicted_labels','weight','opinion'],
        form : str = "",
        add_description : bool = True):
        """
        Display networkx directed graphs (MultiDiGraph).
        It supports the display of attributes.
        Args:
            notes (str, optional): [description]. Defaults to "".
            title (str, optional): [title to save]. Defaults to "result".
            path_to_save_dir (str, optional): [destination path]. Defaults to "generated_pic/".
            vis_features(list[str],optional): Select attributes to display
            form(str,optional):Whether to use the notation for the paper or not. If not, use "", if so, use the string for the output type.
                                "index.label.skew".
            add_description(bool,optional):Whether to add a dummy vertex for description
        """
        graph = self.graph

        num_vertex = len(list(graph.nodes))
        max_indegree = 0
        max_outdegree = 0
        
        
        # Find the max of indegree,outdegree.
        # Note that there may be multiple edges.
        for node in list(graph.nodes):
            max_indegree  = max(max_indegree,
                                len(graph.in_edges(nbunch=node))
                            )
            max_outdegree = max(max_outdegree,
                                len(graph.out_edges(nbunch=node))
                                )
        
        
        #SCC
        graph,num_scc_group = self.attach_scc_id()
        
        def set_visinfo(node:int,attributes:list[str]= vis_features):
            """
            A function that attaches info to each vertex for use in visualization. 

            Args:
                node (int): a natural number representing a vertex.
                attributes (list[str], optional): key of information to visualize. Defaults to ['skew_type','label','conditions','predicted_labels','scc_id'].
            """

            info = ""

            def get_alphabetical_notation(node_index:int) -> str:
                    num_DASH2 = node_index//self.__DASH2
                    num_DASH1 = (node_index - num_DASH2 * self.__DASH2) // self.__DASH1
                    chrcode = node_index - num_DASH2 * self.__DASH2 - num_DASH1 * self.__DASH1

                    alphabetical_notaiton : str = f"{chr( ord('a')+ chrcode)}" + "\'" * num_DASH2 + "*" * num_DASH1

                    return alphabetical_notaiton


            if form == "index.label.skew":

                index = get_alphabetical_notation(node)

                info = f"{index}:l{graph.nodes[node]['label']}:{graph.nodes[node]['skew_type'][0:2]}\n"

                # Separate cases by whether or not extended condition data is used.
                if len(graph.nodes[node]['conditions'][0]) == 4:
                    str_conditions = []
                    for c in graph.nodes[node]['conditions']:
                        str_c :Any = list(copy.deepcopy(c))
                        list_subset = copy.deepcopy(list(str_c[3]))
                    
                        str_c[3] = tuple([ chr(ord('a') + index) for index in list_subset])
                        str_c = tuple(str_c)
                        str_conditions.append(str_c)
                    info += f"{str_conditions}\n"


                else:
                    info += f"{graph.nodes[node]['conditions']}\n"

                
                # weight

                info += f"w:{graph.nodes[node]['weight']}\n"
            
            else:
                assert(form == "")
                info = f"node_index:{node}\n"
                
                for attr in attributes:
                    
                    try:
                    
                        info += f"{attr}:{graph.nodes[node][attr]}\n"
                    
                    except:
                        pass
            
            
            graph.nodes[node]['vis_info'] = info
            
            return
        
        # setting vis_info to each node
        for node in list(graph.nodes):
            set_visinfo(node=node)
            

        # Put information about indegree max and such in description.
        def make_description():
            
            description = notes + "\n" 
            description+= f"num vertex:{num_vertex}\n"
            description+=f"num edges:{graph.number_of_edges()}\n"
            description+= f"max indegree:{max_indegree}\nmax outdegree:{max_outdegree} \n" 
            description+= f"scc_groups:{num_scc_group}compomnents"
            return description
        
        description = make_description()
        
        # settiing color
        cm_name = 'jet' 
        cm = plt.get_cmap(cm_name,num_scc_group+1)
        
        # setting drawing
        for node in list(graph.nodes):
            # rgb expressed in 0-1 values
            color_rgb = cm(graph.nodes[node]['scc_id'])[:3]
            #Change to rgb string in hexadecimal notation
            graph.nodes[node]['color'] = mcolors.to_hex(color_rgb)
            graph.nodes[node]['penwidth'] = 5 #頂点を囲む線の太さ
        
        graph.graph['overlap'] = "prism"
        
        # placement parameter for sfdp,fdp
        graph.graph['K'] = 1.2
        # placement parameter for sfdp
        graph.graph['repulsiveforce'] = 1.4
        
        
        
        # Convert this to agraph class (PyGraphviz)
        G_pgv = nx.nx_agraph.to_agraph(graph)

        
        # Make the information visible by putting vis_info in the label.
        for node in G_pgv.nodes():
            G_pgv.get_node(node).attr["label"] = graph.nodes[int(node)]["vis_info"]   
        
        
        
        # Add dummy vertices to explain the generated visualizetion
        if add_description:
            G_pgv.add_node("description",label = description,shape = "box",color = "gray",style = "filled")
        
        # Optional prog=[‘neato’|’dot’|’twopi’|’circo’|’fdp’|’nop’] will use specified graphviz layout method.
        # fdp is recommended.
        # ValueError: Program osage is not one of: neato, dot, twopi, circo, fdp, nop, gc, acyclic, gvpr, gvcolor, ccomps, sccmap, tred, sfdp, unflatten.
        G_pgv.draw(path_to_save_dir+f"{title}.pdf",prog='fdp',args='-Gnodesep=1')
        
        return 




    def predict_labels(self,u:int)->list:
        """
        For a vertex u, return the labels predicted by the surrounding vertices in a list format.
        Modifies the judges and predicted_labels attributes of node.

        Args:
            u (int): natural number of the vertex to be predicted

        Returns:
            list[int]: list of predicted labels
        """
        G = self.graph
        
        label_list = G.graph['label_list']
        skew_type = G.nodes[u]['skew_type']
        
        G.nodes[u]['judges'] = []
        
        # Calculate the judgement for each condition
        judges :list[_Judge] = []
        
        for c in G.nodes[u]['conditions']:
            judge = _Judge()
            judge.make_a_judge(condition=c,ma_model=self,u=u)
            judges.append(judge)
            
            
        # Make an overall judgment based on the judgment calculated for each condition.
        
        overall_judge = _Judge(judge="S8",skew_type=skew_type)
        
        for judge in judges:
            judge.skew_type = skew_type
            overall_judge = (overall_judge + judge)
            
        
        # Rearrange the format of S1, S2, etc. into a list and return it.
        to_list = [
            None,
            [label_list[0]],                                #S1
            [label_list[1]],                                #S2
            [label_list[2]],                                #S3
            [label_list[0],label_list[1]],                  #S4
            [label_list[0],label_list[2]],                  #S5
            [label_list[1],label_list[2]],                  #S6
            [label_list[0],label_list[1],label_list[2]],    #S7
            []                                              #S8
        ]

        self.graph.nodes[u]["predicted_labels"] = to_list[int(overall_judge.judge[1])]
        
        return to_list[int(overall_judge.judge[1])]

   

    def _split_predecessor_by_label(self,vertex_index:int,label:int,target:Any) -> list[int]:
        """Function to get the predecessor for each vertex label.

        Args:
            vertex_index (int): name of target vertex]: [name of target vertex
            label (int): [which label vertices to collect].
            target (Union[bool,str]): [Specify which vertices to focus on, the attacker or the supporter. True if only the attacker, false if only the supporter, "any" if both.
            No vertices are duplicated if both are specified].

        Returns.
            [list(int)]: [result].
        """


        graph = self.graph

        res_list = []
        
        # search for (u,v,attack) such that v == vertex_index.
        for u,v,attack in graph.in_edges(nbunch = vertex_index,data = "attack"):
            
            assert(attack is not None)
            assert(type(u) == int)
            
            if attack == target:
                if label == "any":
                    res_list.append(u)
                    continue
                
                if graph.nodes[u]['label'] == label:
                    res_list.append(u)
                    continue
        
        return res_list


class _Judge:
    """
    Class for enabling the addition of decisions.
    
    Attributes:
    
    self.judge A place to put real judgments, represented by S1-S8.
    self.skew_type The skew_type needed to add up the judgments for each condition.
    
    """
    
    def __init__(self,judge=None,skew_type = None):
        """Initialization
      
        Args:
            judge (_type_, optional): _Judge by the condition. Defaults to None.
        """
        
        self.skew_type = None
        
        if skew_type is not None:
            self.skew_type = skew_type

        #S8 is the unit source in the addition of decisions.
        self.judge = 'S8'
        
        if judge is not  None:
            self.judge = judge
        
        return
    
    def make_a_judge(self,condition:tuple,ma_model:MAModel,u:int):
        """
        Require a per-condition data decision. Skew-type is not involved when making a judgment for each condition. Conditional data with subsets are supported.
        Conditional data with no subset is also supported.

        Args:
            condition (tuple): Condition
            mamodel(MAModel):model
            u: Vertex with condition passed as argument
        """
        
        G = ma_model.graph

        label_list = G.graph['label_list']
        
        Au = set(ma_model._split_predecessor_by_label(u,label_list[0],True)) | set(ma_model._split_predecessor_by_label(u,label_list[1],False)) 
        Bu = set(ma_model._split_predecessor_by_label(u,label_list[1],True)) | set(ma_model._split_predecessor_by_label(u,label_list[0],False))
        
        if len(condition) == 4:
            
            Au = Au & set(condition[3])
            Bu = Bu & set(condition[3])

        all_weight = 0
        A_weight = 0 # the bigger, the easier to be rej
        B_weight = 0 # the bigger, the easier to be acc


        
        for v in Au:
            A_weight += G.nodes[v]['weight']
            all_weight += G.nodes[v]['weight']
        
        for v in Bu:
            B_weight += G.nodes[v]['weight']
            all_weight += G.nodes[v]['weight']
        
        # 重みが全て1である時と同一のスケールにする。
        if all_weight == 0:
            A_weight = 0
            B_weight = 0
        else:
            average_weight = all_weight / (len(Au) + len(Bu))
            A_weight = A_weight/average_weight
            B_weight = B_weight/average_weight

            # print (f'A:{A_weight},B:{B_weight},all:{all_weight},average:{average_weight},u:{u}')
        
        # A_weight + B_weight shold be almost len(Au) + len(Bu)

        assert abs(A_weight + B_weight - len(Au) - len(Bu)) < 0.1


        # Judging from the ease of being acc. see Bu
        if condition[0] == '+':
            if B_weight < condition[1]:
                self.judge = 'S2'
            elif B_weight < condition[2]:
                self.judge = 'S4'
            else:
                self.judge = 'S1'
        
        # Judging from the ease of being rej. see Au.
        else:
            if A_weight < condition[1]:
                self.judge = 'S1'
            elif A_weight < condition[2]:
                self.judge = 'S4'
            else:
                self.judge = 'S2'
                
        G.nodes[u]['judges'].append(f'A:{A_weight},B:{B_weight},{self.judge}')

        return
    
    def __add__(self,other):
        """        
        Add up the decisions for each vertex.
        Note that it depends on skew_type.

        Args:
            other (_Judge): The other party of the addition.

        Raises:
            NotImplementedError: Raised when not implemented.

        Returns:
            _Judge: Result of _Judge addition performed. 
        """
        
        assert(self.skew_type == other.skew_type)
        
        skew_type = self.skew_type
        
        assert(isinstance(other,_Judge))
        assert(skew_type in ["neutral","L1","L2"])
        
        
        # Addition table of decisions when neutral.
        table_neutral = [
        #          S1   S2   S3   S4   S5   S6   S7   S8
            [None,None,None,None,None,None,None,None,None],
            [None,'S1','S3','S3','S5','S5','S3','S5','S1'],#S1
            [None,'S3','S2','S3','S6','S3','S3','S6','S2'],#S2
            [None,'S3','S3','S3','S3','S3','S3','S3','S3'],#S3
            [None,'S5','S6','S3','S7','S5','S6','S7','S4'],#S4
            [None,'S5','S3','S3','S5','S5','S3','S5','S5'],#S5
            [None,'S3','S3','S3','S6','S3','S3','S6','S6'],#S6
            [None,'S5','S6','S3','S7','S5','S6','S7','S7'],#S7
            [None,'S1','S2','S3','S4','S5','S6','S7','S8'],#S8
        ]
        
        # Addition table of decisions when L1 skew.
        
        table_L1 =[
        #          S1   S2   S3   S4   S5   S6   S7   S8
            [None,None,None,None,None,None,None,None,None],
            [None,"S1","S1",None,"S1",None,None,None,"S1"],#S1
            [None,"S1","S2",None,"S4",None,None,None,"S2"],#S2
            [None,None,None,None,None,None,None,None,None],#S3
            [None,"S1","S4",None,"S4",None,None,None,"S4"],#S4
            [None,None,None,None,None,None,None,None,None],#S5
            [None,None,None,None,None,None,None,None,None],#S6
            [None,None,None,None,None,None,None,None,None],#S7
            [None,"S1","S2",None,"S4",None,None,None,"S8"],#S8
        ]
        
        # Addition table of decisions when L2 skew.
        
        table_L2 = [
        #          S1   S2   S3   S4   S5   S6   S7   S8
            [None,None,None,None,None,None,None,None,None],
            [None,"S1","S2",None,"S4",None,None,None,"S1"],#S1
            [None,"S2","S2",None,"S2",None,None,None,"S2"],#S2
            [None,None,None,None,None,None,None,None,None],#S3
            [None,"S4","S2",None,"S4",None,None,None,"S4"],#S4
            [None,None,None,None,None,None,None,None,None],#S5
            [None,None,None,None,None,None,None,None,None],#S6
            [None,None,None,None,None,None,None,None,None],#S7
            [None,"S1","S2",None,"S4",None,None,None,"S8"],#S8
        ]
        
 
        # get the number to use the addition table.
        to_int = lambda judge:int(judge[1])
        
        if skew_type == 'neutral':
            
            # print(f"{to_int(self.judge)},{to_int(other.judge)}")
            # print(table_neutral[to_int(self.judge)][to_int(other.judge)])

            res_judge = _Judge(judge=table_neutral[to_int(self.judge)][to_int(other.judge)])
        
        if skew_type == 'L1':
            
            res_judge = _Judge(judge=table_L1[to_int(self.judge)][to_int(other.judge)])
            
        if skew_type == 'L2':
            
            res_judge = _Judge(judge=table_L2[to_int(self.judge)][to_int(other.judge)])
        
        res_judge.skew_type = skew_type
        
        return res_judge
    
    def __str__(self):
        return f"<judge:{self.judge}>"
    
    def __repr__(self) -> str:
        return f"<judge:{self.judge}>"


if __name__ == "__main__":
    # Confirmation of IO operation
    model = MAModel()
    path = input("input model path:")
    model.read_yaml(path)

    for node in model.graph.nodes():
        model.predict_labels(node)

    model.visualize(title = "simple",form = "index.label.skew",add_description=False)
    model.visualize(title="normal")
    
    model.save_yaml(path = "output.yml")
    model2 = MAModel()
    model2.read_yaml("output.yml")
    model2.visualize(title="model2")

    print ("end")