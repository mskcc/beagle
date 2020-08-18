'''
From https://hackersandslackers.com/extract-data-from-complex-json-python/
Modified to return values if the key refers to a list
'''

import sys,os
import json

def extract_values(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    arr.append(v)
                elif isinstance(v, (dict, list)):
                    extract(v, arr, key)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    results = set(results)
    return list(results)

def getitems(obj):

  def getkeys(obj, stack):
    for k, v in obj.items():
      k2 = ([k] if k else []) + stack # don't return empty keys
      if v and isinstance(v, dict):
        for c in getkeys(v, k2):
          yield c
      else: # leaf
        yield k2

  def getvalues(obj):
    for v in obj.values():
      if not v: continue
      if isinstance(v, dict):
        for c in getvalues(v):
          yield c
      else: # leaf
        yield v if isinstance(v, list) else [v]

  return list(getkeys(obj,[])), list(getvalues(obj))
