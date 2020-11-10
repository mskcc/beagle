from copy import deepcopy as deepcopy

def fix_query_list(request_query, key_list):
    query_dict = dict(request_query)
    new_query_dict = deepcopy(query_dict)
    for single_param in query_dict:
        query_value = query_dict.get(single_param)
        if '[]' in single_param:
            new_param = single_param.replace('[]','')
            new_query_dict[new_param] = new_query_dict.pop(single_param)
            single_param = new_param
        if query_value:
            if single_param in key_list:
                if type(query_value) == list:
                    if ',' in query_value[0]:
                        new_query_dict[single_param] = query_value[0].split(",")
                    else:
                        new_query_dict[single_param] = query_value
                else:
                    new_query_dict[single_param] = [query_value]
            else:
                new_query_dict[single_param] = query_value[0]
    return new_query_dict
