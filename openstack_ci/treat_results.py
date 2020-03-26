import os
import fnmatch
import matplotlib.pyplot as plt


def get_lines(date):
    """
       Calculates how many builds for a given date
    """
    filenames = []
    filenames = find(date, "results")
    count_builds = 0
    builds_already_seen = []
    for i in filenames:
        path = i
        with open(path, "r") as reader:
            for line in reader.readlines():
                current_build = line
                if current_build not in builds_already_seen:
                    builds_already_seen.append(current_build)
                    count_builds += 1
    return count_builds


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def make_figure(results):
    names = []
    for element in results.keys():
        names.append(element[3:])
    values = list(results.values())
    colors = ['r', 'b', 'y', 'g', 'c', 'm', 'k', 'tab:purple', 'tab:orange']

    fig = plt.figure()
    ax = fig.add_subplot(111)
    y_pos = [0, 2, 4, 6, 8, 10, 12, 14, 16]
    plt.xticks(y_pos, names)
    ax.bar(y_pos, values, color=colors)
    plt.ylabel("Deployments of Kolla-ansible")
    # plt.show()
    plt.savefig("kolla_deployments.png", format="png")


if __name__ == "__main__":
    # changer ça pour adapter aux données récupérées
    results = {
        "20.02.19": 0,
        "20.02.20": 0,
        "20.02.21": 0,
        "20.02.22": 0,
        "20.02.23": 0,
        "20.02.24": 0,
        "20.02.25": 0,
        "20.02.26": 0,
        "20.02.27": 0
        }
    for result in results:
        date_str = "results_20{date}_*".format(date=result)
        results[result] = get_lines(date_str)
        print("For the date 20{date}, there are {nb} results".format(date=result,
                                                                   nb=results[result]))
    make_figure(results)
