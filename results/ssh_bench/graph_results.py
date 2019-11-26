# -*- coding: utf-8 -*-

import click
import plotly.graph_objects as go

import json
import os


@click.group()
def cli():
    pass


@cli.command(help="Create graphs from results for ssh benchmarks")
@click.option("-drp", "--dryrun_path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="Path to the results directory for the dry-run part")
@click.option("-sshp", "--ssh_path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="Path to the results directory for the ssh part.")
@click.option("-exp",
              type=click.Choice(['parallel', 'sequential'], case_sensitive=False),
              required=True,
              help="Whether the benchmark is parallel or sequential")
def analyze(dryrun_path, ssh_path, exp):
    """Analyze the results and produce graphs for it"""
    # From the path we get the files we need
    dry_run_config_file = dryrun_path + "/concerto_config.json"
    dry_run_result_file = dryrun_path + "/times.json"
    ssh_config_file = ssh_path + "/concerto_config.json"
    ssh_result_file = ssh_path + "/times.json"

    is_parallel = exp == 'parallel'
    # get the configuration details from the dry run config
    with open(dry_run_config_file, "r") as conf:
        config = json.load(conf)
        nb_repeats = config["nb_repeats"]
        if config["sleep_time"] is not None:
            sleep_time = config["sleep_time"]
        if is_parallel:
            list_nb_components = config["list_nb_components"]
            list_nb_parallel_transitions = config["list_nb_parallel_transitions"]
        else:
            list_chain_length = config["list_chain_length"]
    # get the config data from the  ssh config
    with open(ssh_config_file, "r") as conf:
        ssh_config = json.load(conf)
        nb_repeats = config["nb_repeats"]
        if ssh_config["sleep_time"] is not None:
            sleep_time = ssh_config["sleep_time"]
        if is_parallel:
            list_nb_components = ssh_config["list_nb_components"]
            list_nb_parallel_transitions = ssh_config["list_nb_parallel_transitions"]
        else:
            list_chain_length = config["list_chain_length"]

    figures = []
    # for the parallel results
    if is_parallel:
        # first we load up the dry run results in a trace
        trace_data_1par = []
        trace_data_1comp = []
        # we build the traces for both parallel experiments in dry run
        with open(dry_run_result_file, "r") as result:
            results = json.load(result)
            trace_data_par = graph_for_1par_xcomp(results, list_nb_components, "dryrun")
            trace_data_1par.extend(trace_data_par)
            trace_data_comp = graph_for_1comp_xpar(results, list_nb_parallel_transitions, "dryrun")
            trace_data_1comp.extend(trace_data_comp)
        # we build the traces for both parallel experiments with ssh
        with open(ssh_result_file, "r") as result:
            results = json.load(result)
            trace_data_par = graph_for_1par_xcomp(results, list_nb_components, None)
            trace_data_1par.extend(trace_data_par)
            trace_data_comp = graph_for_1comp_xpar(results, list_nb_parallel_transitions, None)
            trace_data_1comp.extend(trace_data_comp)

        # now that we have the traces we build the figures
        one_par_fig = create_figure(trace_data_1par, "Components", "Time", False)
        one_comp_fig = create_figure(trace_data_1comp, "Transitions", "Time", False)
        figures.append(one_par_fig)
        figures.append(one_comp_fig)
    else:
        trace_data = []
        with open(dry_run_result_file, "r") as result:
            results = json.load(result)
            trace_data.extend(trace_data_for_seq(results, list_chain_length, "dryrun"))
        with open(ssh_result_file, "r") as result:
            results = json.load(result)
            trace_data.extend(trace_data_for_seq(results, list_chain_length, None))
        fig = create_figure(trace_data, "Components", "Time", False)
        figures.append(fig)
    # display the figures
    i = 0
    for fig in figures:
        i += 1
        export_svg(fig, "{id}".format(id=str(i)))


def graph_for_1comp_xpar(results, list_nb_parallel_transitions, exp_type):
    """Produces trace data (an array of traces)
    from data of a parallel assembly, specifically for 1 component X parallel transitions"""
    results_one_comp = []
    # We get all results for the 1 component
    for transition in list_nb_parallel_transitions:
        results_one_comp.append(results[str(transition)]["1"])
    averages = []
    stds = []
    ideals = []
    for transition in range(len(results_one_comp)):
        avg = results_one_comp[transition]["average"]
        std = results_one_comp[transition]["std"]
        averages.append(avg)
        stds.append(std)
        ideals.append(5)
    if exp_type is "dryrun":
        exp = "dry-run"
    else:
        exp = "ssh-connections"
    avg_trace = create_trace(list_nb_parallel_transitions, averages, exp, stds)
    ideal_trace = create_trace(list_nb_parallel_transitions, ideals, "ideal", None)

    if exp_type is "dryrun":
        trace_data = [avg_trace, ideal_trace]
    else:
        trace_data = [avg_trace]
    return trace_data


def graph_for_1par_xcomp(results, list_nb_components, exp_data):
    """Produces trace data (an array of traces)
    from data of a parallel assembly, specifically for 1 parallel transition X components"""
    results_one_tr = results["1"]
    averages = []
    stds = []
    ideals = []
    avg_time_for_one_comp = results["1"]["1"]["average"]
    for comp in results_one_tr:
        avg = results_one_tr[comp]["average"]
        averages.append(avg)
        stds.append(results_one_tr[comp]["std"])
        # in theory if all components have one transition of 5 seconds, they should all finish in 5 sec or so
        ideals.append(avg_time_for_one_comp)
    if exp_data is "dryrun":
        exp = "dry-run"
        ideal_trace = create_trace(list_nb_components, ideals, "ideal", None)
    else:
        exp = "ssh-connections"
    avg_trace = create_trace(list_nb_components, averages, exp, stds)

    if exp_data is "dryrun":
        trace_data = [avg_trace, ideal_trace]
    else:
        trace_data = [avg_trace]
    return trace_data


def trace_data_for_seq(results, list_chain_length, exp_data):
    """Produces trace data (an array of traces) for a plot.ly figure
    from data of a sequential assembly"""
    averages = []
    ideals = []
    avg_time_for_one_comp = results["1"]["average"]
    stds = []
    for chain_length in list_chain_length:
        chain = str(chain_length)
        avg = results[chain]["average"]
        averages.append(avg)
        ideals.append(avg_time_for_one_comp * chain_length)
        stds.append(results[chain]["std"])

    if exp_data is "dryrun":
        exp = "dry-run"
        ideal_trace = create_trace(list_chain_length, ideals, "ideal " + exp, None)
    else:
        exp = "ssh-connections"
    avg_trace = create_trace(list_chain_length, averages, exp, stds)
    if exp_data is "dryrun":
        trace_data = [avg_trace, ideal_trace]
    else:
        trace_data = [avg_trace]
    return trace_data


def create_trace(x_values, y_values, title, stds):
    """Creates a trace out of data """
    if stds is not None:
        trace = go.Scatter(
            x=x_values,
            y=y_values,
            name=title,
            mode='lines+markers',
            error_y=dict(
                type='data',  # value of error bar given in data coordinates
                array=stds,
                visible=True
            )
        )
    else:
        trace = go.Scatter(
            x=x_values,
            y=y_values,
            name=title,
            mode='lines+markers'
        )

    return trace


def create_figure(fig_data, x_name, y_name, category):
    """"Creates a figure from the traces, with a legend on the graph, no title"""
    if category:
        fig_type = "category"
    else:
        fig_type = "linear"
    fig_layout = {
        "xaxis": {
            "title": x_name,
            "type": fig_type
        },
        "yaxis": {
            "title": y_name
        },
        "legend": {
            "x": 0.02,
            "y": 1,
            "bgcolor": "rgba(0, 0, 0, 0)"
        }
    }
    figure = go.Figure(data=fig_data, layout=fig_layout)
    return figure


def export_svg(figure, file_name):
    """Exports the plot to a svg image, requires orca installation
     see https://plot.ly/python/static-image-export/ """
    if not os.path.exists("img"):
        os.mkdir("img")
    figure.write_image(file_name + ".svg")


if __name__ == '__main__':
    cli()
