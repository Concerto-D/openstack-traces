
import matplotlib.pyplot as plt
import click

import json
import statistics

@click.group()
def cli():
    pass


@cli.command(help="Create graphs from results for ssh benchmarks")
@click.option("-drp", "--dryrun_path",
              type=click.Path(exists=True, file_okay=False),
              required=True,
              help="Path to the results directory for the dry-run part")
@click.option("-exp",
              type=click.Choice(['parallel', 'sequential'], case_sensitive=False),
              required=True,
              help="Whether the benchmark is parallel or sequential")
def analyze(dryrun_path, exp):
    """Analyze the results and produce graphs for it"""
    # From the path we get the files we need
    dry_run_config_file = dryrun_path + "/concerto_config.json"
    dry_run_result_file = dryrun_path + "/times.json"

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

    if is_parallel:
        # first we load up the dry run results in a trace
        with open(dry_run_result_file, "r") as result:
            results = json.load(result)
            fig_1par_comp = graph_for_1par_xcomp(results, list_nb_components, "dryrun")
            fig_1par_comp.savefig("evaluations_par_component.svg", format="svg")
            fig_1comp_xpar = graph_for_1comp_xpar(results, list_nb_parallel_transitions, "dryrun")
            fig_1comp_xpar.savefig("evaluations_par_transitions.svg", format="svg")
    else:
        with open(dry_run_result_file, "r") as result:
            results = json.load(result)
            fig_sequentiel = graph_seq(results, list_chain_length, "dryrun")
            fig_sequentiel.savefig("evaluations_sequential.svg", format="svg")


def graph_for_1par_xcomp(results, list_nb_comp, exp_data):
    """Produces a figure
    from data of a parallel assembly, specifically for 1 parallel transition X components"""
    results_one_tr = results["1"]
    averages = []
    stds = []
    ideals = []
    medians = []
    for comp in results_one_tr:
        avg = results_one_tr[comp]["average"]
        medians.append(statistics.median(results_one_tr[comp]["runs"]))
        averages.append(avg)
        stds.append(results_one_tr[comp]["std"])
        # in theory if all components have one transition of 5 seconds, they should all finish in 5 sec or so
        ideals.append(5)
    if exp_data is "dryrun":
        figure = plt.figure()
        ax = plt.subplot()
        # adding the ideal curve
        plt.plot(list_nb_comp, ideals, label="theoretical")
        # adding the average curve with std as error
        # ax.errorbar(list_nb_comp, averages, yerr=stds, label="Madeus")
        ax.errorbar(list_nb_comp, medians, yerr=stds, label="Madeus")
        plt.ylabel("Time (s)")
        # ax.set_ylim(bottom=4.8, auto=True, top=5.2)
        ax.set_xticks([1, 5, 10, 15, 20, 30, 40, 50])

        plt.xlabel("Number of Components")
        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.legend(loc="upper left")
        return figure


def graph_for_1comp_xpar(results, list_nb_parallel_transitions, exp_type):
    """Produces a figure
    from data of a parallel assembly, specifically for 1 component X parallel transitions"""
    results_one_comp = []
    # We get all results for the 1 component
    for transition in list_nb_parallel_transitions:
        results_one_comp.append(results[str(transition)]["1"])
    averages = []
    stds = []
    ideals = []
    medians = []
    for transition in range(len(results_one_comp)):
        avg = results_one_comp[transition]["average"]
        std = results_one_comp[transition]["std"]
        medians.append(statistics.median(results_one_comp[transition]["runs"]))
        averages.append(avg)
        stds.append(std)
        ideals.append(5)

    if exp_type is "dryrun":
        figure = plt.figure()
        ax = plt.subplot()
        # adding the ideal curve
        plt.plot(list_nb_parallel_transitions, ideals, label="theoretical")
        # adding the average curve with std as error
        # ax.errorbar(list_nb_parallel_transitions, averages, yerr=stds, label="Madeus")
        ax.errorbar(list_nb_parallel_transitions, medians, yerr=stds, label="Madeus")
        plt.ylabel("Time (s)")
        # ax.set_ylim(bottom=4.8, auto=True, top=5.2)
        ax.set_xticks([1, 5, 10, 20])

        plt.xlabel("Number of Transitions")
        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.legend(loc="upper left")
        return figure


def graph_seq(results, list_chain_length, exp_data):
    """Produces a figure
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
        figure = plt.figure()
        ax = plt.subplot()
        # adding the ideal curve
        plt.plot(list_chain_length, ideals, label="theoretical")
        # adding the average curve with std as error
        ax.errorbar(list_chain_length, averages, yerr=stds, label="Madeus")

        ax.set_xticks([1, 5, 10, 25, 100])
        plt.ylabel("Time (s)")

        plt.xlabel("Number of Components")
        # Hide the right and top spines
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        plt.legend(loc="upper left")
        return figure


if __name__ == '__main__':
    cli()



