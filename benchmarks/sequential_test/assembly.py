import time
from typing import List
from concerto.all import DepType
from concerto.madeus.all import MadeusAssembly, MadeusComponent


class SingleTransitionsComponent(MadeusComponent):
    def __init__(self, sleep_time: float = 0, first: bool = False):
        self._sleep_time = sleep_time
        self._first = first
        super().__init__()

    def create(self):
        self.places = [
            'beginning',
            'end'
        ]

        self.initial_place = "beginning"

        self.transitions = {
            'run': ('beginning', 'end', self.run_function),
        }

        self.dependencies = {
            "finished": (DepType.PROVIDE, ['end'])
        }
        if not self._first:
            self.dependencies["previous"] = (DepType.USE, ['run'])

    def run_function(self):
        if self._sleep_time > 0:
            time.sleep(self._sleep_time)


class SequenceAssembly(MadeusAssembly):
    def __init__(self, chain_length: int, sleep_time: float):
        self._chain_length = chain_length
        self._sleep_time = sleep_time
        super().__init__()

    def create(self):
        self.components = {"comp%d" % i: SingleTransitionsComponent(sleep_time=self._sleep_time,
                                                                    first=(i == 0))
                           for i in range(self._chain_length)}

        self.dependencies = [("comp%d" % (i-1), "finished", "comp%d" % i, "previous")
                             for i in range(1, self._chain_length)]

    def run_test(self):
        beginning_time = time.perf_counter()
        self.run(auto_synchronize=False)
        self.synchronize()
        end_time = time.perf_counter()
        self.terminate()
        return end_time-beginning_time


def run_experiments(list_chain_length: List[int], nb_repeats: int,
                    sleep_time: float = 0,
                    gantt: bool = False,
                    verbosity: int = -1, printing: bool = False, print_time: bool = False, dryrun: bool = False):
    import json
    from statistics import mean, stdev
    from typing import Dict, Any
    from concerto.utility import Printer

    running_times: Dict[int, Dict[str, Any]] = dict()

    for chain_length in list_chain_length:
        if printing:
            Printer.st_tprint("Testing for a chain of length %d..." % chain_length)

        running_times[chain_length] = {
            "runs": []
        }
        for i in range(nb_repeats):
            assembly = SequenceAssembly(chain_length, sleep_time)
            assembly.set_verbosity(verbosity)
            assembly.set_print_time(print_time)
            if gantt:
                assembly.set_record_gantt(True)
            assembly.set_dryrun(dryrun)
            time.sleep(1)

            running_time = assembly.run_test()
            running_times[chain_length]["runs"].append(running_time)
            if printing:
                Printer.st_tprint("- attempt %d: %f" % (i+1, running_time))

            if gantt:
                gc = assembly.get_gantt_record()
                gc.get_gantt_chart().export_json("results_%d_%d.json" % (chain_length, i))
        running_times[chain_length]["average"] = mean(running_times[chain_length]["runs"])
        if printing:
            Printer.st_tprint("- average: %f" % running_times[chain_length]["average"])
        if nb_repeats >= 2:
            running_times[chain_length]["std"] = stdev(running_times[chain_length]["runs"])
            if printing:
                Printer.st_tprint("- std: %f" % running_times[chain_length]["std"])

    with open("times.json", "w") as f:
        json.dump(running_times, f, indent='\t')


def load_config(conf_file_location):
    from json import load
    with open(conf_file_location, "r") as file:
        conf = load(file)
    return conf


def main():
    config = load_config("concerto_config.json")
    list_chain_length = config['list_chain_length']
    nb_repeats = config['nb_repeats']
    sleep_time = config['sleep_time']

    run_experiments(
        list_chain_length, nb_repeats,
        sleep_time=sleep_time,
        gantt=False,
        verbosity=-1,
        printing=True,
        print_time=True,
    )


if __name__ == '__main__':
    main()
