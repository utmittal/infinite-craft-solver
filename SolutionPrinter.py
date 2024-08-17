import json
import base64
from urllib.parse import unquote
import os
import time
import matplotlib.pyplot as plt
from graphviz import Digraph

entries = []
# read all files
har_directory = "har_sources"
for filename in os.listdir(har_directory):
    full_path = os.path.join(har_directory, filename)
    if os.path.isfile(full_path):
        with open(full_path, encoding="utf-8") as f:
            net_logs = json.load(f)
            entries.extend(net_logs["log"]["entries"])

recipes = {}
nothing_recipes = {}    # for use in specific methods
elements = set()
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
        exit(1)

    content = response["content"]
    result_json = content["text"]
    if "encoding" in content.keys():
        if content["encoding"] == "base64":
            result_json = base64.b64decode(result_json)
        else:
            # we haven't seen this before, investigate
            print(response)
            exit(1)
    result = json.loads(result_json)["result"]

    # resolve url characters
    combo = tuple(unquote(w) for w in (first, second, result))

    # if result is Nothing, we don't add it to recipes. This makes future lookups simpler
    if result == "Nothing":
        nothing_recipes[(combo[0], combo[1])] = combo[2]
        nothing_recipes[(combo[1], combo[0])] = combo[2]
        continue

    if (combo[0], combo[1]) in recipes.keys() and recipes[(combo[0], combo[1])] != combo[2]:
        print("Found differing recipes.")
        exit(1)
    if (combo[1], combo[0]) in recipes.keys() and recipes[(combo[1], combo[0])] != combo[2]:
        print("Found differing recipes.")
        exit(1)
    recipes[(combo[0], combo[1])] = combo[2]
    recipes[(combo[1], combo[0])] = combo[2]
    elements.update(combo)

    # count for debugging purposes only
    count = count + 1
# print(recipes)

print("Total Elements: " + str(len(elements)))
print("Total Recipes: " + str(len(recipes) / 2))

starting_elements = {"Water", "Fire", "Wind", "Earth"}


def print_all_iterations(interactive=False, freq_graph=False):
    if interactive:
        print("Type q to quit.")

    # gen graph step by step
    curr_elements = starting_elements.copy()
    print("Iteration 0")
    print(curr_elements)
    graph_x = []
    graph_y = []
    if freq_graph:
        graph_x.append(0)
        graph_y.append(len(curr_elements))

    inp = "something"
    iteration = 0
    already_checked = set()
    while inp != "q":
        iteration += 1

        reactions = []
        new_elements = set()
        for fe in curr_elements:
            for se in curr_elements:
                fese = (fe, se)
                if fese not in already_checked and fese in recipes:
                    res = recipes[(fe, se)]
                    if res not in curr_elements and res not in new_elements:
                        reactions.append(fe + " + " + se + " = " + res)
                        new_elements.add(res)
                        already_checked.add((fe, se))
                        already_checked.add((se, fe))

        print("Iteration " + str(iteration))
        print("\tStarting Elements: " + str(curr_elements))
        for reaction in reactions:
            print("\t\t" + reaction)
        print("\tNew Elements: " + str(new_elements))

        if freq_graph:
            graph_x.append(iteration)
            graph_y.append(len(new_elements))

        curr_elements = curr_elements.union(new_elements)

        if len(new_elements) == 0:
            print("No more new elements.")
            break
        else:
            if interactive:
                inp = input()

    if freq_graph:
        plt.xkcd()
        plt.xlabel("Iteration")
        plt.ylabel("Count")
        plt.title("Number of new elements over time")
        plt.axis((0,70,0,100))
        plt.plot(graph_x, graph_y)
        plt.savefig("freq_graphs/" + time.strftime("%Y%m%d_%H%M%S") + ".png", bbox_inches='tight')
        # plt.show()


def find_shortest_path_to(destination):
    curr_elements = {}
    for el in starting_elements:
        curr_elements[el] = [()]

    print("Iteration 0")
    print(curr_elements.keys())

    iteration = 0
    while True:
        iteration += 1

        new_elements = {}
        for fe in curr_elements:
            for se in curr_elements:
                fese = (fe, se)
                if fese in recipes:
                    res = recipes[fese]
                    # gen path to result
                    path_to_new_element = curr_elements[fe].copy()
                    for ser in curr_elements[se]:
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
                                    path_to_new_element.insert(i + 1, ser)
                                    break
                            if found_first == False or found_second == False:
                                path_to_new_element.append(ser)
                    # add current combo to path
                    path_to_new_element.append((fe, se, res))

                    if res in curr_elements:
                        existing_res_path = curr_elements[res]
                        if len(path_to_new_element) < len(existing_res_path):
                            curr_elements[res] = path_to_new_element.copy()
                    elif res in new_elements:
                        existing_res_path = new_elements[res]
                        if len(path_to_new_element) < len(existing_res_path):
                            new_elements[res] = path_to_new_element.copy()
                    else:
                        # add result to new elements
                        new_elements[res] = path_to_new_element

        print("Iteration " + str(iteration))
        print("\tStarting Elements: " + str(curr_elements.keys()))
        print("\tNew Elements: " + str(new_elements.keys()))
        # print("\tNew Element Paths" + str(new_elements))

        if destination in new_elements:
            print("")
            print('Created "' + destination + '" in ' + str(len(new_elements[destination]) - 1) + ' steps.')
            print("Reactions: ")
            for reaction in new_elements[destination]:
                if not reaction:
                    continue
                print("\t" + reaction[0] + " + " + reaction[1] + " = " + reaction[2])
            break

        curr_elements = curr_elements | new_elements  # merge dicts

        if len(new_elements) == 0:
            print("No more new elements.")
            break


def print_missing_combos(interactive=False):
    if interactive:
        print("Type q to quit")

    checked = set()
    for first_el in elements:
        for second_el in elements:
            if (first_el, second_el) not in recipes:
                print(first_el + " + " + second_el + " = ???")
        if interactive:
            if input() == "q":
                break

def print_dag():
    dot = Digraph()
    for node in elements:
        dot.node(node)
    for edge in recipes:
        dot.edge(edge[0],recipes[edge])
        dot.edge(edge[1],recipes[edge])

    # dot.node("Fire")
    # dot.edge("Water",recipes[("Water","Water")])
    # dot.edge("Water",recipes[("Water","Earth")])
    # dot.edge("Earth", recipes[("Water", "Earth")])

    print(dot.source)
    dot.render(directory="dags", view=True)

def suggest_combos():
    curr_elements = starting_elements.copy()
    print("Iteration 0")
    print(curr_elements)

    iteration = 0
    already_checked = set()
    suggestions = set()
    while len(suggestions) <= 10:
        iteration += 1
        print("Iteration " + str(iteration))

        reactions = []
        new_elements = set()
        for fe in curr_elements:
            for se in curr_elements:
                fese = (fe, se)
                if fese not in recipes and fese not in nothing_recipes:
                    add = True
                    # filter out if we already have something starting with this element so
                    # that the suggestions are more varied
                    for sugstr in suggestions:
                        if fe in sugstr or se in sugstr:
                            add = False
                            break
                    if add:
                        suggestions.add(fese)
                    if len(suggestions) > 10:
                        break
                if fese not in already_checked and fese in recipes:
                    res = recipes[(fe, se)]
                    if res not in curr_elements and res not in new_elements:
                        reactions.append(fe + " + " + se + " = " + res)
                        new_elements.add(res)
                        already_checked.add((fe, se))
                        already_checked.add((se, fe))
            if len(suggestions) > 10:
                break

        curr_elements = curr_elements.union(new_elements)

        if len(new_elements) == 0:
            break

    print("--------------------------------------------------------")
    print("Suggestions")
    for sug in suggestions:
        print(sug[0] + " + " + sug[1] + " = ???")

start = time.time()
# print_all_iterations(interactive=False, freq_graph=True)
find_shortest_path_to("Pasta Pandaemonium")
# print_missing_combos()
# suggest_combos()
# print_dag()
end = time.time()
print(end - start)