import json
import os
import unicodedata
import requests

class OncotreeDataHandler:
    def __init__(self):
        self.oncotree = self.fetch_oncotree_data()

    def fetch_oncotree_data(self):
        oncotree_dir = os.path.dirname(__file__)
        oncotree_json = os.path.join(oncotree_dir, 'data/oncotree.json')
        request = requests.get('http://oncotree.mskcc.org/api/tumorTypes').json()
        if 'error' in request: # load from file if error
            request = json.load(open(oncotree_json, 'r'))
        converted_data = self.convert_data_key(request)
        return converted_data

    def convert_data_key(self, data):
       d = dict()
       for node in data:
           name = node['name']
           level = node['level']
           parent = node['parent']
           code = node['code']
           data_node = OncotreeNode(node)
           d[code] = data_node
       return d

    def find_by_code(self, code):
        code_upper  = code.upper()
        try:
            return self.oncotree[code_upper]
        except KeyError:
            print("Code does not exist; defaulting to TISSUE")
            return self.oncotree["TISSUE"]

    def get_parent_list_by_code(self, code, result):
        node = self.find_by_code(code)
        parent = node.parent
        result.append(node)
        if parent is not None:
            return self.get_parent_list_by_code(parent, result)
        else:
            return result

    def find_shared_nodes_by_code_list(self, code_list):
        list_of_sets = list()
        for code in code_list:
            node_data = set(self.get_parent_list_by_code(code, []))
            list_of_sets.append(node_data)
        ancestral_nodes = set.intersection(*list_of_sets)
        return ancestral_nodes

    def get_highest_level_shared_node(self, shared_nodes):
        max_level = -1
        node_to_return = None
        for node in shared_nodes:
            level = node.level
            if node.level > max_level:
                max_level = node.level
                node_to_return = node
        return node_to_return

class OncotreeNode:
    def __init__(self, data):
        self.code = data['code']
        self.name = data['name']
        self.level = data['level']
        self.parent = data['parent']

    def __key(self):
        return (self.code, self.name, self.level, self.parent)

    def __eq(x, y):
        return x.__key() == y.__key()

    def __hash__(self):
        return hash(self.__key())

    def __repr__(self):
        return "OncotreeNode(CODE: %s, NAME: %s, LEVEL: %i, PARENT: %s)" % (self.code, self.name, self.level, self.parent)
