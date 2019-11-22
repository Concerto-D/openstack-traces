# -*- coding: utf-8 -*-

import click
import plotly.graph_objects as go

import json
import os


@click.group()
def cli():
    pass


@cli.command(help="Create graphs from results for ssh benchmarks")
@click.option("-p", "--path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="Path to the results directory")
@click.option("-exp",
              type=click.Choice(['parallel', 'sequential'], case_sensitive=False),
              required=True,
              help="Whether the benchmark is parallel or sequential")
@click.option("--title", "-t",
              required=True,
              help="Title of the graph to be plotted")
def analyze(path, exp, title):
    """Analyze the results and produce graphs for it"""
    # From the path we get the files we need
    config_file = path + "/concerto_config.json"
    result_file = path + "/times.json"
    is_parallel = exp == 'parallel'
    # First, we recover configuration details from the configjson file
    with open(config_file, "r") as conf:
        config = json.load(conf)
        nb_repeats = config["nb_repeats"]
        if config["sleep_time"] is not None:
            sleep_time = config["sleep_time"]
            title += " with sleep time of {sleep} seconds".format(sleep=sleep_time)
        if is_parallel:
            list_nb_components = config["list_nb_components"]
            list_nb_parallel_transitions = config["list_nb_parallel_transitions"]
        else:
            list_chain_length = config["list_chain_length"]
    # Then we get the results
    with open(result_file, "r") as result:
        results = json.load(result)
        if is_parallel:
            # We work to make the graph for one parallel transition, several components
            fig = graph_for_1par_xcomp(results, list_nb_components, title)
            fig.show()
            # TODO: deal with orca installation
            # export_png(fig, "1par_XComp.png")
            fig2 = graph_for_1comp_xpar(results, list_nb_parallel_transitions, title)
            # Next we work on making the graph for X parallel transition, 1 component
            fig2.show()
        # for the sequential
        else:
            fig = figure_dry_run_seq(results, list_chain_length, title)
            fig.show()


def graph_for_1comp_xpar(results, list_nb_parallel_transitions, title):
    results_one_comp = []
    # We get all results for the 1 component
    for transition in list_nb_parallel_transitions:
        results_one_comp.append(results[str(transition)]["1"])
    max_times = []
    min_times = []
    averages = []
    for transition in range(len(results_one_comp)):
        runs = results_one_comp[transition]["runs"]
        avg = results_one_comp[transition]["average"]
        min_time = min(runs)
        min_times.append(min_time)
        max_time = max(runs)
        max_times.append(max_time)
        averages.append(avg)
    min_trace = create_trace(list_nb_parallel_transitions, min_times, "scatter", "Min values")
    max_trace = create_trace(list_nb_parallel_transitions, max_times, "scatter", "Max values")
    avg_trace = create_trace(list_nb_parallel_transitions, averages, "scatter", "Average")
    trace_data = [min_trace, max_trace, avg_trace]
    fig = create_figure(trace_data, "Parallel Transitions", "Time", title, False)
    return fig


def graph_for_1par_xcomp(results, list_nb_components, title):
    results_one_tr = results["1"]
    max_times = []
    min_times = []
    averages = []
    stds = []
    ideals = []
    avg_time_for_one_comp = results["1"]["average"]
    for comp in results_one_tr:
        runs = results_one_tr[comp]["runs"]
        avg = results_one_tr[comp]["average"]
        averages.append(avg)
        stds.append(results_one_tr[comp]["average"])
        ideals.append(avg_time_for_one_comp * int(comp))
    avg_trace = create_trace(list_nb_components, averages, "scatter", "Experimental", stds)
    ideal_trace = create_trace(list_nb_components, ideals, "scatter", "Theoretical", None)
    trace_data = [avg_trace, ideal_trace]
    fig = create_figure(trace_data, "Components", "Time", title, False)
    return fig


def figure_dry_run_seq(results, list_chain_length, title):
    averages = []
    ideals = []
    avg_time_for_one_comp = results["1"]["average"]
    stds = []
    for chain_length in list_chain_length:
        chain = str(chain_length)
        runs = results[chain]["runs"]
        avg = results[chain]["average"]
        averages.append(avg)
        ideals.append(avg_time_for_one_comp * chain_length)
        stds.append(results[chain]["std"])

    avg_trace = create_trace(list_chain_length, averages, "scatter", "Experimental", stds)
    ideal_trace = create_trace(list_chain_length, ideals, "scatter", "Theoretical", None)
    trace_data = [avg_trace, ideal_trace]
    fig = create_figure(trace_data, "Components", "Time", title, False)
    return fig


def create_trace(x_values, y_values, trace_type, title, stds):
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


def create_figure(fig_data, x_name, y_name, title, category):
    if category:
        fig_type = "category"
    else:
        fig_type = "linear"
    fig_layout = {
        "title": title,
        "xaxis": {
            "title": x_name,
            "type": fig_type
        },
        "yaxis": {
            "title": y_name
        }
    }
    figure = go.Figure(data=fig_data, layout=fig_layout)
    return figure


def export_png(figure, file_name):
    if not os.path.exists("img"):
        os.mkdir("img")
    figure.write_image(file_name)


if __name__ == '__main__':
    cli()
