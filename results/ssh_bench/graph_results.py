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
def analyze(path, exp):
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
            fig = graph_for_1par_Xcomp(results, list_nb_components)
            fig.show()
            # TODO: deal with orca installation
            # export_png(fig, "1par_XComp.png")
            fig2 = graph_for_1comp_Xpar(results, list_nb_parallel_transitions)
            # Next we work on making the graph for X parallel transition, 1 component
            fig.show()

            
def graph_for_1comp_Xpar(results, list_nb_parallel_transitions):
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
    fig = create_figure(trace_data, "Parallel Transitions", "Time", "One component, X parallel transitions")
    return fig


def graph_for_1par_Xcomp(results, list_nb_components):
    results_one_tr = results["1"]
    max_times = []
    min_times = []
    averages = []
    for comp in results_one_tr:
        print(comp)
        print(results_one_tr[comp])
        runs = results_one_tr[comp]["runs"]
        avg = results_one_tr[comp]["average"]
        min_time = min(runs)
        min_times.append(min_time)
        max_time = max(runs)
        max_times.append(max_time)
        averages.append(avg)
    min_trace = create_trace(list_nb_components, min_times, "scatter", "Min values")
    max_trace = create_trace(list_nb_components, max_times, "scatter", "Max values")
    avg_trace = create_trace(list_nb_components, averages, "scatter", "Average")
    trace_data = [min_trace, max_trace, avg_trace]
    fig = create_figure(trace_data, "Components", "Time", "One parallel transition, X components")            
    return fig
                
                    
def create_trace(x_values, y_values, trace_type, title):
    trace = go.Scatter(
        x = x_values,
        y = y_values,
        name = title,
        mode='lines+markers'
    )
    return trace        


def create_figure(fig_data, x_name, y_name, title):
    fig_layout = {
        "title": title,
        "xaxis": {
            "title": x_name
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
