import json
import base64
from urllib.parse import unquote
import pandas as pd
import os

entries = []
# read all files
har_directory = "har_sources"
for filename in os.listdir(har_directory):
    full_path = os.path.join(har_directory,filename)
    if os.path.isfile(full_path):
        with open(full_path,encoding="utf-8") as f:
            net_logs = json.load(f)
            entries.extend(net_logs["log"]["entries"])

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
# print(recipes)

# create source of truth list
elements = set()
for recipe in recipes:
    elements.update(recipe)
elements = list(elements)
print("Total Elements: " + str(len(elements)))

# generate matrice
icmat = pd.DataFrame(index=elements, columns=elements)
icmat = icmat.fillna("")
for recipe in recipes:
    if icmat.at[recipe[0],recipe[1]] != recipe[2] and icmat.at[recipe[0],recipe[1]] != "":
        print("Found differing recipes.")
        exit(1)
    if icmat.at[recipe[1], recipe[0]] != recipe[2] and icmat.at[recipe[1], recipe[0]] != "":
        print("Found differing recipes.")
        exit(1)
    icmat.at[recipe[0],recipe[1]] = recipe[2]
    icmat.at[recipe[1], recipe[0]] = recipe[2]
# print(icmat)
# print("Fire + Water = " + icmat.at["Fire","Water"])

def print_all_iterations():
    starting_elements = {"Water", "Fire", "Wind", "Earth"}
    # gen graph step by step
    curr_elements = starting_elements.copy()
    print("Iteration 0")
    print(curr_elements)

    inp = "something"
    iteration = 0
    while inp != "q":
        iteration += 1

        reactions = []
        new_elements = set()
        for fe in curr_elements:
            for se in curr_elements:
                res = icmat.at[fe, se]
                if res != "Nothing" and res != "" and res not in curr_elements and res not in new_elements:
                    reactions.append(fe + " + " + se + " = " + res)
                    new_elements.add(res)

        print("Iteration " + str(iteration))
        print("\tStarting Elements: " + str(curr_elements))
        for reaction in reactions:
            print("\t\t" + reaction)
        print("\tNew Elements: " + str(new_elements))

        curr_elements = curr_elements.union(new_elements)

        if len(new_elements) == 0:
            print("No more new elements.")
            break
        else:
            inp = input()

def find_shortest_path_to(destination):
    starting_elements = ["Water", "Fire", "Wind", "Earth"]

    curr_elements = starting_elements.copy()
    curr_elements_path = [[()] for _ in range(len(starting_elements))]

    print("Iteration 0")
    print(curr_elements)

    iteration = 0
    while True:
        iteration += 1

        new_elements = []
        new_elements_path = []
        for fe in zip(curr_elements,curr_elements_path, strict=True):
            for se in zip(curr_elements,curr_elements_path, strict=True):
                res = icmat.at[fe[0], se[0]]
                if res != "Nothing" and res != "" and res not in curr_elements and res not in new_elements:
                    new_elements.append(res)
                    result_reaction = (fe[0],se[0],res)

                    path_to_new_element = fe[1].copy()
                    # insert at the right places
                    for ser in se[1]:
                        if ser not in path_to_new_element:
                            found_first = False
                            found_second = False
                            for i in range(len(path_to_new_element)):
                                r = path_to_new_element[i]
                                if r == ():
                                    continue
                                if r[2] == ser[0]:
                                    found_first = True
                                if r[2] == ser[1]:
                                    found_second = True
                                if found_first and found_second:
                                    path_to_new_element.insert(i+1,ser)
                                    break
                            if found_first == False or found_second == False:
                                path_to_new_element.append(ser)
                    path_to_new_element.append(result_reaction)
                    new_elements_path.append(path_to_new_element)

        print("Iteration " + str(iteration))
        print("\tStarting Elements: " + str(curr_elements))
        print("\tNew Elements: " + str(new_elements))
        # print("\tNew Element Paths" + str(new_elements_path))

        if destination in new_elements:
            destination_index = new_elements.index(destination)
            print("")
            print('Created "' + destination + '" in ' + str(len(new_elements_path[destination_index])-1) + ' steps.')
            print("Reactions: ")
            for reaction in new_elements_path[destination_index]:
                if not reaction:
                    continue
                print("\t" + reaction[0] + " + " + reaction[1] + " = " + reaction[2])
            break

        curr_elements = curr_elements + new_elements
        curr_elements_path = curr_elements_path + new_elements_path

        if len(new_elements) == 0:
            print("No more new elements.")
            break

def print_missing_combos():
    for first_el in elements:
        for second_el in elements:
            if icmat.at[first_el,second_el] == "":
                print(first_el + " + " + second_el + " = ???")
        input()

# print_all_iterations()
find_shortest_path_to("Obsidian")
# print_missing_combos()