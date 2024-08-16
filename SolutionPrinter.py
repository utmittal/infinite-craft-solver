import json
import base64
from urllib.parse import unquote
import numpy as np
import pandas as pd

# read file
with open("har_sources/neal.fun.har",encoding="utf-8") as f:
    net_logs = json.load(f)

# get entries
entries = net_logs["log"]["entries"]

recipes = []
# parse all entries
count = 0
for entry in entries:
    # print(count)
    request = entry["request"]
    if not request["url"].startswith("https://neal.fun/api/infinite-craft/pair?"):
        continue
    first = request["queryString"][0]["value"]
    second = request["queryString"][1]["value"]

    response = entry["response"]
    if response["status"] == 500:
        # skip error responses
        continue
    if response["status"] != 200:
        # we haven't seen this before, investigate
        print(response)
        break

    content = response["content"]
    result_json = content["text"]
    if "encoding" in content.keys():
        if content["encoding"] == "base64":
            result_json = base64.b64decode(result_json)
        else:
            # we haven't seen this before, investigate
            print(response)
            break
    result = json.loads(result_json)["result"]

    # resolve url characters
    recipes.append([unquote(w) for w in [first,second,result]])

    # count for debugging purposes only
    count = count+1
print(recipes)

# create source of truth list
elements = set()
for recipe in recipes:
    elements.update(recipe)
elements = list(elements)
print(elements)

# generate matrice
