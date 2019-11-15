#!/usr/bin/env python
import logging
from typing import List

from experiment_utilities.remote_host import RemoteHost
from experiment_utilities.reserve_g5k import G5kReservation
from experiment_utilities.concerto_g5k import ConcertoG5k


def run_experiment(list_nb_components, list_nb_parallel_transitions, sleep_time, nb_repeats, conf, working_directory,
                   force_deployment=True, destroy=False):
    with G5kReservation(conf, force_deployment, destroy) as g5k:
        remote_machines = g5k.get_hosts_info(role='remote')
        concerto_machine = g5k.get_hosts_info(role='concerto')[0]
        print("Remote: %s" % str(remote_machines))
        print("Concerto: %s" % str(concerto_machine))
        concerto_config = {
            "remote_hosts": remote_machines,
            "concerto_host": concerto_machine if concerto_machine else None,
            "list_nb_components": list_nb_components,
            "list_nb_parallel_transitions": list_nb_parallel_transitions,
            "sleep_time": sleep_time,
            "nb_repeats": nb_repeats,

        }

        with g5k.ansible_to("concerto") as ansible_to_concerto:
            ansible_to_concerto.apt(name=["python3", "python3-pip", "git"], state="present")
            ansible_to_concerto.pip(name=["enoslib"], executable="pip3")

        with RemoteHost(concerto_machine["address"], remote_user="root") as concerto_host:
            with ConcertoG5k(
                    remote_host=concerto_host,
                    remote_exp_dir=ConcertoG5k.DEFAULT_CONCERTO_DIR_IN_GIT + '/tests/parallel_test',
                    python_file='assembly.py',
                    concerto_config=concerto_config,
                    local_wd=working_directory,
                    send_ssh_keys=True
            ) as concerto_g5k:
                concerto_g5k.execute(timeout="45m")
                files_to_get = ['stdout', 'stderr', 'times.json']
                for nb_trans in list_nb_parallel_transitions:
                    files_to_get += ['results_%d_transitions.gpl' % nb_trans, 'results_%d_transitions.json' % nb_trans]
                concerto_g5k.get_files(files_to_get)


def perform_experiment(list_nb_components: List[int], list_nb_parallel_transitions: List[int], sleep_time: float, nb_repeats: int,
                       working_directory: str = 'exp', ssh_test=True):
    import yaml
    from os import makedirs

    with open("conf.yaml") as f:
        conf = yaml.load(f)

    conf['g5k']['resources']['machines'][0]['nodes'] = max(list_nb_components) if ssh_test else 0

    makedirs(working_directory, exist_ok=True)
    with open(working_directory + '/g5k_config.yaml', 'w') as g5k_config_file:
        yaml.dump(conf, g5k_config_file)

    run_experiment(list_nb_components, list_nb_parallel_transitions, sleep_time, nb_repeats, conf, working_directory)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    perform_experiment(
        list_nb_components=[1, 5, 10, 15, 20],
        list_nb_parallel_transitions=[1, 5, 10, 20],
        sleep_time=10,
        nb_repeats=5,
        working_directory="exp_ssh",
        ssh_test=True
    )
    perform_experiment(
        list_nb_components=[1, 5, 10, 15, 20, 50],
        list_nb_parallel_transitions=[1, 5, 10, 20],
        sleep_time=1,
        nb_repeats=5,
        working_directory="exp_no_ssh",
        ssh_test=False
    )
