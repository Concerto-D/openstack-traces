# -*- coding: utf-8 -*-
import json
import statistics

import matplotlib.pyplot as plt
import click

import yaml
# necessary import for the yaml object in the results
from execo_engine import *


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
        Calculate means for a group of experiment, remote/local/cached
        with std
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
            "std": statistics.stdev(remotes)
        },
        "cached": {
            "mean": statistics.mean(cacheds),
            "std": statistics.stdev(cacheds)
        },
        "local": {
            "mean": statistics.mean(locales),
            "std": statistics.stdev(locales)
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


def generate_tex_table(ansible_means, aeolus_means, madeus_means, aeolus_gains, madeus_gains):
    """"
        From results in the tables, builds a TeX table for our papere
    """
    with open("tab_openstack_results.tex", "w") as f:
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
        f.write("\n540s &\n485s &\n334s \\\\\n & & aeolus & \n269s &\n259s &\n232s \\\\\n & & madeus & \n156s &")
        f.write("\n158s &\n136s \\\\")
        f.write("\n\\cmidrule{2-6}& \\multirow{3}{*}{\\STAB{\\rotatebox[origin=c]{90}{min}}}  & ansible  &")
        f.write("\n523s &\n473s &\n326s \\\\\n & & aeolus &\n257s &\n249s &\n223 \\\\\n & & madeus &")
        f.write("\n141s &\n143s &\n123s \\\\\n\\bottomrule\\end{tabular}")


@click.group()
def cli():
    pass


@cli.command(help="Gives the means and std from results for open stack deployment benchmarks and the percentage"
                  "of gain from aeolus and madeus compared to the ansible deployment and generates corresponding"
                  "LaTeX table")
@click.option("-rp", "--result_path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="The path containing the file results_deployment_times")
def analyze(result_path):
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

    generate_tex_table(ansible_means, aeolus_means, madeus_means, aeolus_gains, madeus_gains)


@cli.command(help="Create gantt graph from result file and saves it to svg format")
@click.option("-f", "--filepath",
              type=click.Path(exists=False),
              required=True,
              help="The path containing the json file with times for gantt")
def creategantt(filepath):
    cached_dag2t_results = get_results(filepath)
    title = filepath +".svg"
    create_figure(cached_dag2t_results, title)


def get_results(filepath):
    results = {}
    # we get all result in one dict
    for i in range(10):
        filename = filepath + "_" + str(i) + ".json"
        with open(filename, "r") as f:
            data = json.load(f)
            for component in data:
                # print("Component {s}".format(s=component))
                # print(data[component])
                if component not in results.keys():
                    results[component] = {}
                    for behaviour in data[component]:
                        # print("Behaviour {b}".format(b=behaviour))
                        # print(data[component][behaviour])
                        results[component][behaviour] = []
                        for transition in data[component][behaviour]:
                            # print("Transition {t}".format(t=transition))
                            results[component][behaviour].append({
                                "name": transition["name"],
                                "starts": [transition["start"]],
                                "ends": [transition["end"]]
                            })
                            # print(results[component][behaviour])
                else:
                    for behaviour in data[component]:
                        # print("Behaviour {b}".format(b=behaviour))
                        for transition in data[component][behaviour]:
                            # print("Transition {t}".format(t=transition))
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


def create_figure(results, name: str):
    # TODO: sort results for sequential graphs -> sorting the data that is in a list in a dict...
    figure = plt.figure()
    ax = plt.subplot()
    max_time = 0
    i = 0
    labels = []
    ticks = []
    colors = ['b', 'r', 'g', 'c', 'm', 'y', 'k', 'tab:blue', 'tab:orange', 'tab:gray', 'tab:brown', 'lime']
    for element in results:
        color = colors[i % 12]
        # for each element, have a color and cycle it
        # every step is under the deploy keyword in the json result file
        for item in results[element]["deploy"]:
            # get max time
            if item["end"] > max_time:
                max_time = item["end"]
            ax.broken_barh([(item["start"], (item["end"] - item["start"]))], (2 * i + 0.75, 1),
                           facecolors=color)
            # shorten long names
            if len(element) > 4:
                if element == 'keystone':
                    element = 'kst'
                elif element == 'memcached':
                    element = 'mem'
                elif element == 'mariadb':
                    element = 'mdb'
                elif element == 'rabbitmq':
                    element = 'rmq'
                elif element == 'openvswitch':
                    element = 'ovs'
                elif element == 'haproxy':
                    element = 'hap'
                elif element == 'common':
                    element = 'com'
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


if __name__ == '__main__':
    cli()
