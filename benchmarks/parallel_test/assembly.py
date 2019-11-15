import time
from typing import List, Optional
from concerto.all import DepType
from concerto.madeus.all import MadeusAssembly, MadeusComponent
from concerto.utility import empty_transition


class ParallelTransitionsComponent(MadeusComponent):
    def __init__(self,  nb_parallel_transitions: int,
                 sleep_time: float = 0, remote_address: Optional[str] = None):
        self._nb_parallel_transitions = nb_parallel_transitions
        assert(nb_parallel_transitions >= 1)
        self._sleep_time = sleep_time
        self._remote_host = None
        if remote_address:
            from experiment_utilities.remote_host import RemoteHost
            self._remote_host = RemoteHost(remote_address)
        super().__init__()

    def create(self):
        self.places = [
            'beginning',
            'ready',
            'end'
        ]

        self.initial_place = "beginning"

        self.transitions = {
            'wait_dep': ('beginning', 'ready', empty_transition)
        }
        for i in range(self._nb_parallel_transitions):
            self.transitions["trans%d" % i] = 'ready', 'end', self.run_function,

        self.dependencies = {
            "service": (DepType.PROVIDE, ['end']),
            "use_service": (DepType.USE, ['wait_dep'])
        }

    def run_function(self):
        if self._remote_host:
            self._remote_host.run("sleep %f" % self._sleep_time)
        elif self._sleep_time > 0:
            time.sleep(self._sleep_time)


class ProviderComponent(MadeusComponent):
    def create(self):
        self.places = [
            'beginning',
            'end'
        ]

        self.initial_place = "beginning"

        self.transitions = {
            'provide': ('beginning', 'end', empty_transition)
        }

        self.dependencies = {
            "service": (DepType.PROVIDE, ['end'])
        }


class ParallelAssembly(MadeusAssembly):
    def __init__(self, nb_components: int, nb_parallel_transitions: int,
                 remote_addresses: Optional[List[str]] = None, sleep_time: float = 0):
        if remote_addresses:
            assert(len(remote_addresses) >= nb_components)
        self._nb_components = nb_components
        self._nb_parallel_transitions = nb_parallel_transitions
        self._remote_addresses = remote_addresses
        self._sleep_time = sleep_time
        super().__init__()

    def create(self):
        self.components = {
            "provider": ProviderComponent()
        }
        for i in range(self._nb_components):
            remote_address = self._remote_addresses[i] if self._remote_addresses else None
            self.components["user%d" % i] = ParallelTransitionsComponent(self._nb_parallel_transitions,
                                                                         self._sleep_time,
                                                                         remote_address)
        self.dependencies = [("provider", "service", "user%d" % i, "use_service") for i in range(self._nb_components)]

    def run_test(self):
        beginning_time = time.perf_counter()
        self.run(auto_synchronize=False)
        self.synchronize()
        end_time = time.perf_counter()
        self.terminate()
        return end_time-beginning_time


def run_experiments(list_nb_components: List[int], list_nb_parallel_transitions: List[int], nb_repeats: int,
                    remote_hosts: List[str] = (), sleep_time: float = 0, gantt: bool = False,
                    verbosity: int = -1, printing: bool = False, print_time: bool = False, dryrun: bool = False):
    import json
    from statistics import mean, stdev
    from typing import Dict, Any
    from concerto.utility import Printer

    running_times: Dict[int, Dict[int, Dict[str, Any]]] = dict()

    for nb_trans in list_nb_parallel_transitions:
        running_times[nb_trans] = dict()
        if printing:
            Printer.st_tprint("Preparing the assembly with %d parallel transitions per component" % nb_trans)

        for nb_components in list_nb_components:
            if printing:
                Printer.st_tprint("Testing for %d components..." % nb_components)
            running_times[nb_trans][nb_components] = {
                "runs": []
            }
            for i in range(nb_repeats):
                assembly = ParallelAssembly(nb_components, nb_trans, remote_hosts, sleep_time)
                assembly.set_verbosity(verbosity)
                assembly.set_print_time(print_time)
                if gantt:
                    assembly.set_record_gantt(True)
                assembly.set_dryrun(dryrun)
                time.sleep(1)
                running_time = assembly.run_test()
                running_times[nb_trans][nb_components]["runs"].append(running_time)

                if printing:
                    Printer.st_tprint("- attempt %d: %f" % (i+1, running_time))

                if gantt:
                    gc = assembly.get_gantt_record()
                    gc.get_gantt_chart().export_json("results_%d_transitions_%d_components_%d.gpl"
                                                     % (nb_trans, nb_components, i))
            running_times[nb_trans][nb_components]["average"] = mean(running_times[nb_trans][nb_components]["runs"])
            if printing:
                Printer.st_tprint("- average: %f" % running_times[nb_trans][nb_components]["average"])
            if nb_repeats >= 2:
                running_times[nb_trans][nb_components]["std"] = stdev(running_times[nb_trans][nb_components]["runs"])
                if printing:
                    Printer.st_tprint("- std: %f" % running_times[nb_trans][nb_components]["std"])

    with open("times.json", "w") as f:
        json.dump(running_times, f, indent='\t')


def load_config(conf_file_location):
    from json import load
    with open(conf_file_location, "r") as file:
        conf = load(file)
    return conf


def main():
    config = load_config("concerto_config.json")
    list_nb_components = config['list_nb_components']
    list_nb_parallel_transitions = config['list_nb_parallel_transitions']
    nb_repeats = config['nb_repeats']
    remote_hosts = [h["ip"] for h in config['remote_hosts']]
    sleep_time = config['sleep_time']

    run_experiments(
        list_nb_components,
        list_nb_parallel_transitions,
        nb_repeats,
        remote_hosts,
        sleep_time=sleep_time,
        gantt=False,
        verbosity=-1,
        printing=True,
        print_time=True,
    )


if __name__ == '__main__':
    main()
