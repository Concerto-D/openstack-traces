#!/usr/bin/env python
import logging
from typing import List

from experiment_utilities.remote_host import RemoteHost
from experiment_utilities.reserve_g5k import G5kReservation
from experiment_utilities.concerto_g5k import ConcertoG5k


def run_experiment(list_chain_length, nb_repeats, conf, working_directory,
                   force_deployment=True, destroy=False):
    with G5kReservation(conf, force_deployment, destroy) as g5k:
        concerto_machine = g5k.get_hosts_info(role='concerto')[0]
        print("Concerto: %s" % str(concerto_machine))
        concerto_config = {
            "concerto_host": concerto_machine,
            "list_chain_length": list_chain_length,
            "nb_repeats": nb_repeats
        }

        with g5k.ansible_to("concerto") as ansible_to_concerto:
            ansible_to_concerto.apt(name=["python3", "git"], state="present")

        with RemoteHost(concerto_machine["address"], remote_user="root") as concerto_host:
            with ConcertoG5k(
                    remote_host=concerto_host,
                    remote_exp_dir=ConcertoG5k.DEFAULT_CONCERTO_DIR_IN_GIT + '/tests/sequential_test',
                    python_file='assembly.py',
                    concerto_config=concerto_config,
                    local_wd=working_directory
            ) as concerto_g5k:
                concerto_g5k.execute(timeout="45m")
                concerto_g5k.get_files(['stdout', 'stderr', 'results.gpl', 'results.json', 'times.json'])


def perform_experiment(list_chain_length: List[int], nb_repeats: int,
                       working_directory: str = 'exp'):
    import yaml
    from os import makedirs

    with open("conf.yaml") as f:
        conf = yaml.load(f)

    makedirs(working_directory, exist_ok=True)
    with open(working_directory + '/g5k_config.yaml', 'w') as g5k_config_file:
        yaml.dump(conf, g5k_config_file)

    run_experiment(list_chain_length, nb_repeats, conf, working_directory)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    perform_experiment(
        list_chain_length=[1, 5, 25, 100],
        nb_repeats=5
    )
