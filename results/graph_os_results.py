# -*- coding: utf-8 -*-
import json

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
            - dag_nt4 : all experiments of type dag_nt4
            - seq_1t : all experiments of type seq_1t
            - dag_2t : all experiments of type dag_2t
    """
    elements = []
    dag_nt4 = []
    seq_1t = []
    dag_2t = []
    seq_nt4 = []
    for element in results:
        if element['failure'] == 0:
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


@click.group()
def cli():
    pass


@cli.command(help="Create graphs from results for open stack deployment benchmarks")
@click.option("-rp", "--result_path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="The path containing the file results_deployment_times")
def analyze(result_path):
    """Analyze the results and produce graphs for it"""
    # From the path we get the files we need
    result_file = result_path + '/results_deployment_times'
    with open(result_file, "r") as f:
        results = yaml.load(f)

    successful_exps, seq_nt4_exps, dag_nt4_exps, seq_1t_exps, dag_2t_exps = format_results(results)


@cli.command(help="Create gantt graph from result file and saves it to svg format")
@click.option("-f", "--filepath",
              type=click.Path(exists=True),
              required=True,
              help="The path containing the json file with times for gantt")
@click.option("-n", "--name",
              type=click.Path(exists=False),
              required=True,
              help="Name of the file to be saved for the gantt svg")
def creategantt(filepath, name):

    # adds the extension to the file name if needed
    if not name.endswith(".svg"):
        name = name + ".svg"

    with open(filepath, "r") as f:
        results = json.load(f)
    figure = plt.figure()
    ax = plt.subplot()
    max_time = 0
    i = 0
    labels = []
    ticks = []
    colors = ['blue', 'red', 'orange', 'green', 'grey']
    for element in results:
        color = colors[i % 5]
        # for each element, have a color and cycle it
        # every step is under the deploy keyword in the json result file
        for item in results[element]["deploy"]:
            # get max time
            if item["end"] > max_time:
                max_time = item["end"]
            ax.broken_barh([(item["start"], (item["end"] - item["start"]))], (2 * i + 0.75, 1),
                           facecolors=(color))
            # shorten long names
            if len(element) > 4:
                if element == 'keystone':
                    element = 'kst'
                elif element == 'memcached':
                    element = 'mem'
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
