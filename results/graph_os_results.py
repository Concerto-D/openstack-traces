# -*- coding: utf-8 -*-
import json
import statistics
import fnmatch
import os

import matplotlib.pyplot as plt
import click
import numpy

import yaml
# necessary import for the yaml object in the results
from execo_engine import *
from matplotlib.gridspec import GridSpec


def format_results(results):
    """
    Taking in the yaml object with all the results and returns tables of all the results without failure,
    and a table per experiment
    :param results: a list of yaml objects
        (example: {'failure': 0, 'params':{'registry':'remote', 'repeat':3, 'test_type': 'seq_1t'}, 'time': 499.00})
    :return:
            - elements : a list of all experiments
            - seq_nt4 : all experiments of type seq_nt4
            - dag_nt4 : all experiments of type dag_nt4 (madeus)
            - seq_1t : all experiments of type seq_1t (ansible)
            - dag_2t : all experiments of type dag_2t (aeolus)
    """
    elements = []
    dag_nt4 = []
    seq_1t = []
    dag_2t = []
    seq_nt4 = []
    for element in results:
        if element['failure'] == 0:
            # we take only the elements that haven't failed
            elements.append(element)
            if element['params']['test_type'] == 'seq_nt4':
                seq_nt4.append(element)
            elif element['params']['test_type'] == 'dag_nt4':
                dag_nt4.append(element)
            elif element['params']['test_type'] == 'seq_1t':
                seq_1t.append(element)
            elif element['params']['test_type'] == 'dag_2t':
                dag_2t.append(element)
    return elements, seq_nt4, dag_nt4, seq_1t, dag_2t


def calc_mean(exp_table):
    """
        Calculate means, std, mins, and maxes for a group of experiment, remote/local/cached
    """
    remotes = []
    locales = []
    cacheds = []
    for exp in exp_table:
        if exp["params"]["registry"] == 'local':
            locales.append(exp["time"])
        elif exp["params"]["registry"] == 'remote':
            remotes.append(exp["time"])
        elif exp["params"]["registry"] == 'cached':
            cacheds.append(exp["time"])
    results = {
        "remote": {
            "mean": statistics.mean(remotes),
            "std": statistics.stdev(remotes),
            "min": min(remotes),
            "max": max(remotes)
        },
        "cached": {
            "mean": statistics.mean(cacheds),
            "std": statistics.stdev(cacheds),
            "min": min(cacheds),
            "max": max(cacheds)
        },
        "local": {
            "mean": statistics.mean(locales),
            "std": statistics.stdev(locales),
            "min": min(locales),
            "max": max(locales)
        }
    }
    return results


def calc_gains(exp_table, ref_table):
    """
        Calculate % gained on an experiment with a table as reference
        :param exp_table: the experiment to calculate gain from
        :param ref_table: the reference values
        :return:
    """
    result = {
        "remote": 100 - (exp_table["remote"]["mean"] / ref_table["remote"]["mean"] * 100),
        "cached": 100 - (exp_table["cached"]["mean"] / ref_table["cached"]["mean"] * 100),
        "local": 100 - (exp_table["local"]["mean"] / ref_table["local"]["mean"] * 100)
    }

    return result


def generate_tex_table(ansible_means, aeolus_means, madeus_means, aeolus_gains, madeus_gains, tex_name):
    """"
        From results in the tables, builds a TeX table for our paper
    """
    if not tex_name.endswith(".tex"):
        file_name = tex_name + ".tex"
    else:
        file_name = tex_name
    with open(file_name, "w") as f:
        f.write("\n\\begin{tabular}{cll|ccc}\n")
        f.write("\\toprule\n")
        f.write("& & & remote & local & cached \\\\\n")
        f.write("\n\\midrule\n"
                "\\multirow{9}{*}{\\STAB{\\rotatebox[origin=c]{90}{measured}}} & \\multirow{3}{*}{\\STAB{\\rotatebox[origin=c]{90}{mean}}}  & ansible  &")
        f.write("\n{ans_rem_mean}s &".format(ans_rem_mean=int(ansible_means["remote"]["mean"])))
        f.write("\n{ans_loc_mean}s &".format(ans_loc_mean=int(ansible_means["local"]["mean"])))
        f.write("\n{ans_cac_mean}s \\\\".format(ans_cac_mean=int(ansible_means["cached"]["mean"])))
        f.write("\n & & aeolus &")
        f.write("\n{aeo_rem_mean}s &".format(aeo_rem_mean=int(aeolus_means["remote"]["mean"])))
        f.write("\n{aeo_loc_mean}s &".format(aeo_loc_mean=int(aeolus_means["local"]["mean"])))
        f.write("\n{aeo_cac_mean}s \\\\".format(aeo_cac_mean=int(aeolus_means["cached"]["mean"])))
        f.write("\n & & madeus &")
        f.write("\n{mad_rem_mean}s &".format(mad_rem_mean=int(madeus_means["remote"]["mean"])))
        f.write("\n{mad_loc_mean}s &".format(mad_loc_mean=int(madeus_means["local"]["mean"])))
        f.write("\n{mad_cac_mean}s \\\\".format(mad_cac_mean=int(madeus_means["cached"]["mean"])))
        f.write("\n\\cmidrule{2-6}& \\multirow{3}{*}{\\STAB{\\rotatebox[origin=c]{90}{gain}}}  & ansible  &")
        f.write("\n0\\% &\n0\\% &\n0\\% \\\\\n & & aeolus &")
        f.write("\n{aeo_rem_gain}\\% &\n{aeo_loc_gain}\\% &\n{aeo_cac_gain}\\% \\\\".format(
            aeo_rem_gain=int(aeolus_gains["remote"]), aeo_loc_gain=int(aeolus_gains["local"]),
            aeo_cac_gain=int(aeolus_gains["cached"])))
        f.write("\n & & madeus &")
        f.write("\n{mad_rem_gain}\\% &\n{mad_loc_gain}\\% &\n{mad_cac_gain}\\% \\\\".format(
            mad_rem_gain=int(madeus_gains["remote"]), mad_loc_gain=int(madeus_gains["local"]),
            mad_cac_gain=int(madeus_gains["cached"])))
        f.write("\n\\cmidrule{2-6}& \\multirow{3}{*}{\\STAB{\\rotatebox[origin=c]{90}{std}}}  & ansible  &")
        f.write("\n{ans_rem_std}s &".format(ans_rem_std=int(ansible_means["remote"]["std"])))
        f.write("\n{ans_loc_std}s &".format(ans_loc_std=int(ansible_means["local"]["std"])))
        f.write("\n{ans_cac_std}s \\\\".format(ans_cac_std=int(ansible_means["cached"]["std"])))
        f.write("\n & & aeolus &")
        f.write("\n{aeo_rem_std}s &".format(aeo_rem_std=int(aeolus_means["remote"]["std"])))
        f.write("\n{aeo_loc_std}s &".format(aeo_loc_std=int(aeolus_means["local"]["std"])))
        f.write("\n{aeo_cac_std}s \\\\".format(aeo_cac_std=int(aeolus_means["cached"]["std"])))
        f.write("\n & & madeus &")
        f.write("\n{mad_rem_std}s &".format(mad_rem_std=int(madeus_means["remote"]["std"])))
        f.write("\n{mad_loc_std}s &".format(mad_loc_std=int(madeus_means["local"]["std"])))
        f.write("\n{mad_cac_std}s \\\\".format(mad_cac_std=int(madeus_means["cached"]["std"])))
        f.write("\n\\midrule")
        f.write("\n\\multirow{6}{*}{\\STAB{\\rotatebox[origin=c]{90}{theoretical}}} & \\multirow{3}{*}{\\STAB{\\rotatebox[origin=c]{90}{max}}}  & ansible  &")
        f.write("\n{ans_rem_max}s &".format(ans_rem_max=int(ansible_means["remote"]["max"])))
        f.write("\n{ans_loc_max}s &".format(ans_loc_max=int(ansible_means["local"]["max"])))
        f.write("\n{ans_cac_max}s \\\\".format(ans_cac_max=int(ansible_means["cached"]["max"])))
        f.write("\n & & aeolus &")
        f.write("\n{aeo_rem_max}s &".format(aeo_rem_max=int(aeolus_means["remote"]["max"])))
        f.write("\n{aeo_loc_max}s &".format(aeo_loc_max=int(aeolus_means["local"]["max"])))
        f.write("\n{aeo_cac_max}s \\\\".format(aeo_cac_max=int(aeolus_means["cached"]["max"])))
        f.write("\n & & madeus &")
        f.write("\n{mad_rem_max}s &".format(mad_rem_max=int(madeus_means["remote"]["max"])))
        f.write("\n{mad_loc_max}s &".format(mad_loc_max=int(madeus_means["local"]["max"])))
        f.write("\n{mad_cac_max}s \\\\".format(mad_cac_max=int(madeus_means["cached"]["max"])))
        f.write("\n\\cmidrule{2-6}& \\multirow{3}{*}{\\STAB{\\rotatebox[origin=c]{90}{min}}}  & ansible  &")
        f.write("\n{ans_rem_min}s &".format(ans_rem_min=int(ansible_means["remote"]["min"])))
        f.write("\n{ans_loc_min}s &".format(ans_loc_min=int(ansible_means["local"]["min"])))
        f.write("\n{ans_cac_min}s \\\\".format(ans_cac_min=int(ansible_means["cached"]["min"])))
        f.write("\n & & aeolus &")
        f.write("\n{aeo_rem_min}s &".format(aeo_rem_min=int(aeolus_means["remote"]["min"])))
        f.write("\n{aeo_loc_min}s &".format(aeo_loc_min=int(aeolus_means["local"]["min"])))
        f.write("\n{aeo_cac_min}s \\\\".format(aeo_cac_min=int(aeolus_means["cached"]["min"])))
        f.write("\n & & madeus &")
        f.write("\n{mad_rem_min}s &".format(mad_rem_min=int(madeus_means["remote"]["min"])))
        f.write("\n{mad_loc_min}s &".format(mad_loc_min=int(madeus_means["local"]["min"])))
        f.write("\n{mad_cac_min}s \\\\".format(mad_cac_min=int(madeus_means["cached"]["min"])))
        f.write("\n\\bottomrule\n\\end{tabular}")


@click.group()
def cli():
    pass


@cli.command(help="Generates a performance comparison graph for the various assembly benchmarks")
@click.option("-rp", "--result_path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="The path containing the file results_deployment_times")
@click.option("-f", "--fig_name",
              type=str,
              required=True,
              help="Name for the resulting svg file of the figure")
def performcomparison(result_path, fig_name):
    # From the path we get the files we need
    result_file = result_path + '/results_deployment_times'
    with open(result_file, "r") as f:
        results = yaml.load(f)
    successful_exps, seq_nt4_exps, dag_nt4_exps, seq_1t_exps, dag_2t_exps = format_results(results)
    ansible_means = calc_mean(seq_1t_exps)
    madeus_means = calc_mean(dag_nt4_exps)
    aeolus_means = calc_mean(dag_2t_exps)
    madeus_gains = calc_gains(madeus_means, ansible_means)
    aeolus_gains = calc_gains(aeolus_means, ansible_means)
    data = [ansible_means, aeolus_means, madeus_means, aeolus_gains, madeus_gains]
    fig = plt.figure(constrained_layout=True)
    gs = GridSpec(2, 3, figure=fig)
    generate_histogram(data, gs, fig)
    box_plot_data_1 = [
        [
            data[0]["remote"]["max"],
            data[0]["remote"]["mean"],
            data[0]["remote"]["min"]
        ],
        [
            data[0]["local"]["max"],
            data[0]["local"]["mean"],
            data[0]["local"]["min"]
        ],
        [
            data[0]["cached"]["max"],
            data[0]["cached"]["mean"],
            data[0]["cached"]["min"]
        ]
    ]
    std_1 = [
        data[0]["remote"]["std"],
        data[0]["local"]["std"],
        data[0]["cached"]["std"]
    ]
    box_plot_data_2 = [
        [
            data[1]["remote"]["max"],
            data[1]["remote"]["mean"],
            data[1]["remote"]["min"]
        ],
        [
            data[1]["local"]["max"],
            data[1]["local"]["mean"],
            data[1]["local"]["min"]
        ],
        [
            data[1]["cached"]["max"],
            data[1]["cached"]["mean"],
            data[1]["cached"]["min"]
        ]
    ]
    std_2 = [
        data[1]["remote"]["std"],
        data[1]["local"]["std"],
        data[1]["cached"]["std"]
    ]
    box_plot_data_3 = [
        [
            data[2]["remote"]["max"],
            data[2]["remote"]["mean"],
            data[2]["remote"]["min"]
        ],
        [
            data[2]["local"]["max"],
            data[2]["local"]["mean"],
            data[2]["local"]["min"]
        ],
        [
            data[2]["cached"]["max"],
            data[2]["cached"]["mean"],
            data[2]["cached"]["min"]
        ]
    ]
    std_3 = [
        data[2]["remote"]["std"],
        data[2]["local"]["std"],
        data[2]["cached"]["std"]
    ]
    generate_box_plot(box_plot_data_1, std_1, gs[-1, 0], fig, True)  # ansible
    generate_box_plot(box_plot_data_2, std_2, gs[-1, -2], fig, False)  # aeolus
    generate_box_plot(box_plot_data_3, std_3, gs[1:, -1], fig, False)  # madeus

    # save the result
    if fig_name.endswith(".svg"):
        name = fig_name
    else:
        name = fig_name + ".svg"
    fig.savefig(name, format="svg", bbox_inches='tight')


def generate_box_plot(data, std, coordinates, fig, first):
    # not a box_plot
    box_plot = fig.add_subplot(coordinates)
    if first:
        box_plot.set_ylabel("Time (s)")
    bar_width = 15
    line_width = 1
    colours = ["blue", "red", "green"]
    for i in range(3):
        diff_max_min = data[i][0] - data[i][2]
        box_plot.bar(x=i * bar_width,
                     height=diff_max_min,
                     width=bar_width,
                     bottom=data[i][2],
                     linewidth=line_width,
                     facecolor="White",
                     edgecolor='k')
        eb = box_plot.errorbar(x=i * bar_width,
                         y= data[i][1],
                         xerr=5, yerr=std[i],
                         ecolor=colours[i],
                         fmt='none')
        elines = eb.get_children()
        elines[1].set_color('k')
    box_plot.tick_params(
        axis='x',  # changes apply to the x-axis
        which='both',  # both major and minor ticks are affected
        bottom=False,  # ticks along the bottom edge are off
        top=False,  # ticks along the top edge are off
        labelbottom=False)  # labels along the bottom edge are off
    box_plot.grid(True, axis='y')
    box_plot.set_axisbelow(True)


def autolabel(rects, ax, over_text, text_data=None):
    """
    Attach a text label above each bar displaying its height if there is no string under_text
    Other wise displays a text under the bar
    """
    i = 0
    max_height = 0
    for rect in rects:
        height = rect.get_height()
        if max_height < height:
            max_height = height
        # adapt the position of the ratio in the bar
        if max_height > 530:
            diff = 90
        else:
            diff = 50
        text = '%d' % int(height)
        color = 'black'
        if not over_text:
            height = rect.get_height() - diff
            text = "{:.2f}".format(text_data[i] / 100.00)
            color = 'white'
        ax.text(rect.get_x() + rect.get_width()/2., height, str(text)[:4],
                ha='center', va='bottom', color=color)
        i = i + 1


def generate_histogram(data, gs, fig):
    histo = fig.add_subplot(gs[0, :])
    bar_data = [
        [int(data[0]["remote"]["mean"]), int(data[1]["remote"]["mean"]), int(data[2]["remote"]["mean"])],
        [int(data[0]["local"]["mean"]), int(data[1]["local"]["mean"]), int(data[2]["local"]["mean"])],
        [int(data[0]["cached"]["mean"]), int(data[1]["cached"]["mean"]), int(data[2]["cached"]["mean"])]
    ]
    percent_data = [
        [100, 100 - int(data[3]["remote"]), 100 - int(data[4]["remote"])],
        [100, 100 - int(data[3]["local"]), 100 - int(data[4]["local"])],
        [100, 100 - int(data[3]["cached"]), 100 - int(data[4]["cached"])]
    ]
    x = numpy.arange(3)
    histo.spines['right'].set_visible(False)
    histo.spines['top'].set_visible(False)
    ax = plt.bar(x, bar_data[0], color='blue', width=0.25, label="remote")
    autolabel(ax, histo, True)
    autolabel(ax, histo, False, percent_data[0])
    ax2 = plt.bar(x + 0.25, bar_data[1], color='red', width=0.25, label="local")
    autolabel(ax2, histo, True)
    autolabel(ax2, histo, False, percent_data[1])
    ax3 = plt.bar(x + 0.5, bar_data[2], color='green', width=0.25, label="cached")
    autolabel(ax3, histo, True)
    autolabel(ax3, histo, False, percent_data[2])
    histo.set_xticks([0.25, 1.25, 2.25])
    histo.set_xticklabels(['ansible', 'aeolus', 'madeus'])
    handles, labels = histo.get_legend_handles_labels()
    plt.legend(handles, labels)
    histo.set_xlabel("Assemblies")
    histo.set_ylabel("Time (s)")


@cli.command(help="Gives the means and std from results for open stack deployment benchmarks and the percentage"
                  "of gain from aeolus and madeus compared to the ansible deployment and generates corresponding"
                  "LaTeX table")
@click.option("-rp", "--result_path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="The path containing the file results_deployment_times")
@click.option("-tn", "--tex_name",
              type=str,
              required=True,
              help="Name for the resulting tex file of the table")
def analyze(result_path, tex_name):
    """
        Analyze the results and produce tables for the means, % gains and std
        May contain rounding inaccuracies
    """
    # From the path we get the files we need
    result_file = result_path + '/results_deployment_times'
    with open(result_file, "r") as f:
        results = yaml.load(f)
    successful_exps, seq_nt4_exps, dag_nt4_exps, seq_1t_exps, dag_2t_exps = format_results(results)
    ansible_means = calc_mean(seq_1t_exps)
    madeus_means = calc_mean(dag_nt4_exps)
    aeolus_means = calc_mean(dag_2t_exps)
    print("Ansible means: remote: {remote}s, local: {local}s, cached: {cached}s".format(
        remote=int(ansible_means["remote"]["mean"]),
        local=int(ansible_means["local"]["mean"]),
        cached=int(ansible_means["cached"]["mean"])))
    print("Madeus means: remote: {remote}s, local: {local}s, cached: {cached}s".format(
        remote=int(madeus_means["remote"]["mean"]),
        local=int(madeus_means["local"]["mean"]),
        cached=int(madeus_means["cached"]["mean"])))
    print("Aeolus means: remote: {remote}s, local: {local}s, cached: {cached}s".format(
        remote=int(aeolus_means["remote"]["mean"]),
        local=int(aeolus_means["local"]["mean"]),
        cached=int(aeolus_means["cached"]["mean"])))
    print("Ansible std: remote: {remote}s, local: {local}s, cached: {cached}s".format(
        remote=int(ansible_means["remote"]["std"]),
        local=int(ansible_means["local"]["std"]),
        cached=int(ansible_means["cached"]["std"])))
    print("Madeus std: remote: {remote}s, local: {local}s, cached: {cached}s".format(
        remote=int(madeus_means["remote"]["std"]),
        local=int(madeus_means["local"]["std"]),
        cached=int(madeus_means["cached"]["std"])))
    print("Aeolus std: remote: {remote}s, local: {local}s, cached: {cached}s".format(
        remote=int(aeolus_means["remote"]["std"]),
        local=int(aeolus_means["local"]["std"]),
        cached=int(aeolus_means["cached"]["std"])))

    madeus_gains = calc_gains(madeus_means, ansible_means)
    aeolus_gains = calc_gains(aeolus_means, ansible_means)
    print("Madeus gains: remote: {remote}%, local: {local}%, cached: {cached}%".format(
        remote=int(madeus_gains["remote"]),
        local=int(madeus_gains["local"]),
        cached=int(madeus_gains["cached"])))
    print("Aeolus gains: remote: {remote}%, local: {local}%, cached: {cached}%".format(
        remote=int(aeolus_gains["remote"]),
        local=int(aeolus_gains["local"]),
        cached=int(aeolus_gains["cached"])))

    generate_tex_table(ansible_means, aeolus_means, madeus_means, aeolus_gains, madeus_gains, tex_name)


@cli.command(help="Create gantt graph from result file and saves it to svg format")
@click.option("-f", "--filepath",
              type=click.Path(file_okay=False),
              required=True,
              help="The path containing the json files with times for gantt")
@click.option("-n", "--namepattern",
              type=str,
              required=True,
              help="The name pattern of the json files (results_cached_dag_nt4 for example)")
@click.option("-nb", "--number",
              type=int,
              required=True,
              help="The number of result json files")
def creategantt(filepath, namepattern, number):
    """
        Gets results and creates the appropriate gantt graph
        :param filepath: the path of the file
        :param namepattern: the file namepattern (to which we add _[x].json where x is a number
        :param number: the number of files following the pattern, it's the [x] above
        :return: nothing
    """
    cached_dag2t_results = get_results(filepath, namepattern, number)
    title = namepattern +".svg"
    create_figure(cached_dag2t_results, title)


def get_results(file_path, name_pattern, number):
    """
        Aggregates results from files matching a pattern into a single dictionary
        :param file_path: the path of the file
        :param name_pattern: the file name_pattern (to which we add _[x].json where x is a number
        :param number: the number of files following the pattern, it's the [x] above
        :return: the results as a dictionary
    """
    results = {}
    # we get all result in one dict
    for i in range(number):
        filename = file_path + name_pattern + "_" + str(i) + ".json"
        with open(filename, "r") as f:
            data = json.load(f)
            for component in data:
                if component not in results.keys():
                    results[component] = {}
                    for behaviour in data[component]:
                        results[component][behaviour] = []
                        for transition in data[component][behaviour]:
                            results[component][behaviour].append({
                                "name": transition["name"],
                                "starts": [transition["start"]],
                                "ends": [transition["end"]]
                            })
                else:
                    for behaviour in data[component]:
                        for transition in data[component][behaviour]:
                            results[component][behaviour] = add_start_and_end(
                                results[component][behaviour], transition["name"], transition["start"],
                                transition["end"])
    # we calc the mean value for transition starts and ends
    for component in results:
        for behaviour in results[component]:
            for transition in results[component][behaviour]:
                transition["start"] = statistics.mean(transition["starts"])
                transition["end"] = statistics.mean(transition["ends"])
    return results


def add_start_and_end(behaviour, name, start, end):
    result = behaviour
    for transition in result:
        if name == transition["name"]:
            transition["ends"].append(end)
            transition["starts"].append(start)
    return result


def sort_seq_results(results):
    """
        Sorts the results according to the smallest start value
        results are a dict containing items with lists and we want to sort on the start value of each
    """
    elements = []
    res = []
    for element in results:
        for item in results[element]["deploy"]:
            item["component"] = element
            # we need to add the component name or we lost it
            elements.append(item)
    elements.sort(key=lambda x: x["start"], reverse=True)
    for el in elements:
        res.append(
            {
                "component": el["component"],
                "name": el["name"],
                "start": el["start"],
                "end": el["end"]
            }
        )
    return res


def shorten_comp_name(name: str):
    """Shortens component names to allow for better readability"""
    element_name = name
    if len(name) > 4:
        if name == 'keystone':
            element_name = 'kst'
        elif name == 'memcached':
            element_name = 'mem'
        elif name == 'mariadb':
            element_name = 'mdb'
        elif name == 'rabbitmq':
            element_name = 'rmq'
        elif name == 'openvswitch':
            element_name = 'ovs'
        elif name == 'haproxy':
            element_name = 'hap'
        elif name == 'common':
            element_name = 'com'
    return element_name


def create_figure(results, name: str):
    figure = plt.figure()
    ax = plt.subplot()
    max_time = 0
    i = 0
    color_number = 0
    labels = []
    ticks = []
    colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k', 'tab:blue', 'tab:orange', 'tab:gray', 'tab:brown', 'lime', 'fuchsia']
    # sequential means we need to sort the results to display it properly
    if "seq" in name:
        results = sort_seq_results(results)
        components = []
        for element in results:
            # for each component, have a color
            if not any(d["component"] == element["component"] for d in components):
                components.append(
                    {
                        "component": element["component"],
                        "color": colors[color_number]
                    }
                )
                color_number = color_number + 1
            # get the right color for the component
            color_picked = next(item.get("color") for item in components if item["component"] == element["component"])
            # get max time
            if element["end"] > max_time:
                max_time = element["end"]
            ax.broken_barh([(element["start"], (element["end"] - element["start"]))], (2 * i + 0.75, 1),
                           facecolors=color_picked)
            # shorten long names
            element_name = shorten_comp_name(element["component"])
            transition = element["name"]
            if element["name"] == 'upgrade_api_db':
                transition = 'upapidb'
            elif element["name"] == 'upgrade_db':
                transition = 'updb'
            labels.append(element_name + "." + transition)
            ticks.append(2 * i + 1)
            i += 1
    else:
        for element in results:
            color_picked = colors[color_number % 13]
            color_number += 1
            # for each element, have a color and cycle it
            # every step is under the deploy keyword in the json result file
            looping = results[element]["deploy"]
            for item in looping:
                # get max time
                if item["end"] > max_time:
                    max_time = item["end"]
                ax.broken_barh([(item["start"], (item["end"] - item["start"]))], (2 * i + 0.75, 1),
                               facecolors=color_picked)
                # shorten component name on graph
                element = shorten_comp_name(element)
                # for some, shorten long name of transition
                transition = item["name"]
                if item["name"] == 'upgrade_api_db':
                    transition = 'upapidb'
                elif item["name"] == 'upgrade_db':
                    transition = 'updb'
                labels.append(element + "." + transition)
                ticks.append(2 * i + 1)
                i += 1

    ax.set_xlim(0, max_time + 10)
    ax.set_ylim(0, i * 2)
    ax.set_ylabel('Transitions')
    ax.set_xlabel('Time (s)')
    ax.grid(True)
    # ax.set_ylim(0,)
    ax.set_yticks(ticks)
    ax.set_yticklabels(labels)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    figure.savefig(name, format="svg", bbox_inches='tight')


@cli.command(help="Creates data for table of pull information (% and s) of nova  ")
@click.option("-f", "--filepath",
              type=click.Path(file_okay=False),
              required=True,
              help="The path containing the results")
@click.option("-n", "--number",
              type=int,
              required=True,
              help="The number of json files of each type (nb of experiments)")
def tableofpulls(filepath, number):
    cluster_name = "Cluster"
    if "nova" in filepath:
        cluster_name = "Nova"
    elif "ecotype" in filepath:
        cluster_name = "Ecotype"
    # first we get the pull times of madeus
    print("===============================================")
    print("{c} pull information for nova component ".format(c=cluster_name))
    cached_filename_base = filepath + "/results_cached_dag_2t_"
    cached_aeolus_pull, cached_aeolus_mean = get_mean_pull_and_mean_total(cached_filename_base, number)

    local_filename_base = filepath + "/results_local_dag_2t_"
    local_aeolus_pull, local_aeolus_mean = get_mean_pull_and_mean_total(local_filename_base, number)

    remote_filename_base = filepath + "/results_remote_dag_2t_"
    remote_aeolus_pull, remote_aeolus_mean = get_mean_pull_and_mean_total(remote_filename_base, number)

    print("*********** Aeolus ***********************")
    print("*********** Cached ***********************")
    calc_percentage(cached_aeolus_pull, cached_aeolus_mean)
    print("*********** Local ************************")
    calc_percentage(local_aeolus_pull, local_aeolus_mean)
    print("*********** Remote ************************")
    calc_percentage(remote_aeolus_pull, remote_aeolus_mean)

    cached_filename_base = filepath + "/results_cached_dag_nt4_"
    cached_madeus_pull, cached_madeus_mean = get_mean_pull_and_mean_total(cached_filename_base, number)

    local_filename_base = filepath + "/results_local_dag_nt4_"
    local_madeus_pull, local_madeus_mean = get_mean_pull_and_mean_total(local_filename_base, number)

    remote_filename_base = filepath + "/results_remote_dag_nt4_"
    remote_madeus_pull, remote_madeus_mean = get_mean_pull_and_mean_total(remote_filename_base, number)
    print("\n\n*********** Madeus ***********************")
    print("*********** Cached ***********************")
    calc_percentage(cached_madeus_pull, cached_madeus_mean)
    print("*********** Local ************************")
    calc_percentage(local_madeus_pull, local_madeus_mean)
    print("*********** Remote ************************")
    calc_percentage(remote_madeus_pull, remote_madeus_mean)


def get_mean_pull_and_mean_total(filebase, number):
    pull_times = []
    max_times = []
    for i in range(number):
        filename = filebase + str(i) + ".json"
        max_time = 0
        with open(filename, "r") as f:
            data = json.load(f)
            for component in data:
                for transition in data[component]:
                    for action in data[component][transition]:
                        if component == 'nova':
                            if action["name"] == "pull":
                                time = action["end"] - action["start"]
                                pull_times.append(time)
                        if action["end"] > max_time:
                            max_time = action["end"]
            max_times.append(max_time)
    if len(pull_times) > 0:
        mean_pull_time = statistics.mean(pull_times)
    else:
        mean_pull_time = 0
    max_mean_time = statistics.mean(max_times)
    return mean_pull_time, max_mean_time


def calc_percentage(pull_time, total_duration):
    percentage = pull_time / total_duration * 100
    print("\tPull mean time {t}s ".format(t=str(pull_time)[:4]))
    print("\tMean max time {t}s ".format(t=str(total_duration)[:6]))
    print("\tPull percentage over total time {p}%".format(p=str(percentage)[:4]))


if __name__ == '__main__':
    cli()
