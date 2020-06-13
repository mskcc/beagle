
def fix_query_list(request_query, key_list):
    query_dict = dict(request_query)
    for single_param in query_dict:
        query_value = query_dict.get(single_param)
        if query_value:
            if single_param in key_list:
                if type(query_value) == list:
                    if ',' in query_value[0]:
                        query_dict[single_param] = query_value[0].split(",")
                    else:
                        query_dict[single_param] = query_value
                else:
                    query_dict[single_param] = [query_value]
            else:
                query_dict[single_param] = query_value[0]
    return query_dict