import json
import logging
import multiprocessing
import multiprocessing as mp
import os
import os.path
import sqlite3
import sys
import time
from datetime import datetime
from multiprocessing import Process
from typing import List, Generator, Dict, Callable, Set, Tuple, Optional, Union

import math
import matplotlib
import matplotlib.pyplot as plt
import pathos.multiprocessing as pmp
from fuzzingbook.GrammarCoverageFuzzer import GrammarCoverageFuzzer
from fuzzingbook.Parser import EarleyParser
from grammar_graph import gg
from matplotlib import pyplot as plt, ticker as mtick

from isla import isla, solver
from isla.helpers import weighted_geometric_mean
from isla.solver import ISLaSolver
from isla.type_defs import Grammar, ParseTree

logger = logging.getLogger("evaluator")


def strtime() -> str:
    return datetime.now().strftime("%H:%M:%S")


def std_db_file() -> str:
    return os.path.join(
        *os.path.split(os.path.dirname(os.path.realpath(__file__)))[:-1],
        "isla_evaluation.sqlite")


class PerformanceEvaluationResult:
    def __init__(
            self,
            accumulated_valid_inputs: Dict[float, int],
            accumulated_invalid_inputs: Dict[float, int],
            accumulated_k_path_coverage: Dict[float, int],
            accumulated_non_vacuous_index: Dict[float, float]):
        self.accumulated_valid_inputs = accumulated_valid_inputs
        self.accumulated_invalid_inputs = accumulated_invalid_inputs
        self.accumulated_k_path_coverage = accumulated_k_path_coverage
        self.accumulated_non_vacuous_index = accumulated_non_vacuous_index

        self.max_time = max([
            (.0 if not accumulated_valid_inputs else list(accumulated_valid_inputs.keys())[-1]),
            (.0 if not accumulated_invalid_inputs else list(accumulated_invalid_inputs.keys())[-1]),
        ])

        if accumulated_valid_inputs and accumulated_k_path_coverage and accumulated_non_vacuous_index:
            self.final_product_value: float = self.single_product_value(max(accumulated_valid_inputs.keys()))
        else:
            self.final_product_value = -1

    def save_to_csv_file(self, dir: str, base_file_name: str):
        valid_input_file = os.path.join(dir, base_file_name + "_valid_inputs.csv")
        with open(valid_input_file, 'w') as f:
            f.write("\n".join(f"{t};{r}" for t, r in self.accumulated_valid_inputs.items()))
            print(f"Written valid input data to {valid_input_file}")

        invalid_input_file = os.path.join(dir, base_file_name + "_invalid_inputs.csv")
        with open(invalid_input_file, 'w') as f:
            f.write("\n".join(f"{t};{r}" for t, r in self.accumulated_invalid_inputs.items()))
            print(f"Written invalid input data to {invalid_input_file}")

        k_path_file = os.path.join(dir, base_file_name + "_k_paths.csv")
        with open(k_path_file, 'w') as f:
            f.write("\n".join(f"{t};{r}" for t, r in self.accumulated_k_path_coverage.items()))
            print(f"Written accumulated k-path data {k_path_file}")

        non_vacuous_file = os.path.join(dir, base_file_name + "_non_vacuous_index.csv")
        with open(non_vacuous_file, 'w') as f:
            f.write("\n".join(f"{t};{r}" for t, r in self.accumulated_valid_inputs.items()))
            print(f"Written non-vacuous index data to {k_path_file}")

    @staticmethod
    def load_from_csv_file(dir: str, base_file_name: str) -> 'PerformanceEvaluationResult':
        valid_input_file = os.path.join(dir, base_file_name + "_valid_inputs.csv")
        with open(valid_input_file, 'r') as f:
            accumulated_valid_inputs = dict([
                (float(line.split(";")[0]), int(line.split(";")[1]))
                for line in f.read().split("\n") if line])

        invalid_input_file = os.path.join(dir, base_file_name + "_invalid_inputs.csv")
        with open(invalid_input_file, 'r') as f:
            accumulated_invalid_inputs = dict([
                (float(line.split(";")[0]), int(line.split(";")[1]))
                for line in f.read().split("\n") if line
            ])

        k_path_file = os.path.join(dir, base_file_name + "_k_paths.csv")
        with open(k_path_file, 'r') as f:
            accumulated_k_path_coverage = dict([
                (float(line.split(";")[0]), int(line.split(";")[1]))
                for line in f.read().split("\n") if line])

        non_vacuous_file = os.path.join(dir, base_file_name + "_non_vacuous_index.csv")
        with open(non_vacuous_file, 'r') as f:
            accumulated_non_vacuous_index = dict([
                (float(line.split(";")[0]), float(line.split(";")[1]))
                for line in f.read().split("\n") if line])

        return PerformanceEvaluationResult(
            accumulated_valid_inputs,
            accumulated_invalid_inputs,
            accumulated_k_path_coverage,
            accumulated_non_vacuous_index)

    def valid_inputs_proportion_data(self) -> Dict[float, float]:
        result: Dict[float, float] = {}
        valid_inputs = 0
        invalid_inputs = 0

        for seconds in sorted(list(set(self.accumulated_valid_inputs.keys()) |
                                   set(self.accumulated_invalid_inputs.keys()))):
            if seconds in self.accumulated_valid_inputs:
                valid_inputs += 1
            if seconds in self.accumulated_invalid_inputs:
                invalid_inputs += 1

            result[seconds] = valid_inputs / (valid_inputs + invalid_inputs)

        return result

    def mean_data(self) -> Dict[float, float]:
        if not (self.accumulated_valid_inputs
                and self.accumulated_k_path_coverage
                and self.accumulated_non_vacuous_index):
            return {}

        return {
            seconds: self.single_product_value(seconds)
            for seconds in self.accumulated_valid_inputs}

    def single_product_value(self, seconds: float, weights: tuple[float, ...] = (1, 1, 1)) -> float:
        return weighted_geometric_mean(
            [self.accumulated_valid_inputs[seconds],
             self.accumulated_k_path_coverage[seconds],
             self.accumulated_non_vacuous_index[seconds]],
            weights)

    def plot(self, outfile_pdf: str, title: str = "Performance Data"):
        assert outfile_pdf.endswith(".pdf")
        matplotlib.use("PDF")

        fig, ax = plt.subplots()
        ax.plot(
            list(self.accumulated_valid_inputs.keys()),
            list(self.accumulated_valid_inputs.values()),
            label="Valid Inputs")
        ax.plot(
            list(self.accumulated_invalid_inputs.keys()),
            list(self.accumulated_invalid_inputs.values()),
            label="Invalid Inputs")
        ax.plot(
            list(self.accumulated_k_path_coverage.keys()),
            list(self.accumulated_k_path_coverage.values()),
            label="k-Path Coverage (%)")
        ax.plot(
            list(self.accumulated_non_vacuous_index.keys()),
            list(self.accumulated_non_vacuous_index.values()),
            label="Non-Vacuity Index")

        mean = self.mean_data()
        ax.plot(
            list(mean.keys()),
            list(mean.values()),
            label="Geometric Mean")

        for values in [
            self.accumulated_valid_inputs.values(),
            self.accumulated_invalid_inputs.values(),
            self.accumulated_k_path_coverage.values(),
            self.accumulated_non_vacuous_index.values(),
            mean.values()
        ]:
            plt.annotate(
                max(values),
                xy=(1, max(values)),
                xytext=(8, 0),
                xycoords=('axes fraction', 'data'),
                textcoords='offset points')

        ax.set_xlabel("Seconds")
        ax.set_title(title)
        ax.legend()
        fig.tight_layout()
        plt.plot()

        print("Saving performance analysis plot to %s", outfile_pdf)
        matplotlib.pyplot.savefig(outfile_pdf)

    def __repr__(self):
        return (f"PerformanceEvaluationResult("
                f"accumulated_valid_inputs={self.accumulated_valid_inputs}, "
                f"accumulated_invalid_inputs={self.accumulated_invalid_inputs}, "
                f"accumulated_k_path_coverage={self.accumulated_k_path_coverage}, "
                f"accumulated_non_vacuous_index={self.accumulated_non_vacuous_index})")

    def __str__(self):
        return f"Performance: {self.final_product_value} (" \
               f"valid inputs: {(list(self.accumulated_valid_inputs.values()) or [0])[-1]}, " \
               f"invalid inputs: {(list(self.accumulated_invalid_inputs.values()) or [0])[-1]}, " \
               f"k-Path Coverage: {(list(self.accumulated_k_path_coverage.values()) or [0])[-1]}, " \
               f"Non-Vacuity Index: {(list(self.accumulated_non_vacuous_index.values()) or [0])[-1]})"


def generate_inputs(
        generator: Generator[isla.DerivationTree, None, None] | ISLaSolver | Grammar,
        timeout_seconds: int = 60,
        jobname: Optional[str] = None) -> Dict[float, isla.DerivationTree]:
    start_time = time.time()
    result: Dict[float, isla.DerivationTree] = {}
    jobname = "" if not jobname else f" ({jobname})"
    print(f"[{strtime()}] Collecting data for {timeout_seconds} seconds{jobname}")

    if isinstance(generator, ISLaSolver):
        generator = generator.solve()
    elif isinstance(generator, dict):
        grammar = generator

        def gen():
            fuzzer = GrammarCoverageFuzzer(grammar)
            while True:
                yield isla.DerivationTree.from_parse_tree(
                    list(EarleyParser(grammar).parse(fuzzer.fuzz()))[0])

        generator = gen()

    while int(time.time()) - int(start_time) <= timeout_seconds:
        try:
            inp = next(generator)
        except StopIteration:
            break
        except Exception as exp:
            print("Exception occurred while executing solver; I'll stop here:\n" + str(exp), file=sys.stderr)
            return result

        logger.debug("Input: %s", str(inp))
        curr_relative_time = time.time() - start_time
        assert curr_relative_time not in result
        result[curr_relative_time] = inp

    print(f"[{strtime()}] Collected {len(result)} inputs in {timeout_seconds} seconds{jobname}")
    return result


def create_db_tables(db_file: str = std_db_file()) -> None:
    con = sqlite3.connect(db_file)

    with con:
        con.execute("""
CREATE TABLE IF NOT EXISTS inputs (
  inpId INTEGER PRIMARY KEY ASC, 
  testId TEXT,
  sid INT,
  reltime REAL,
  inp TEXT
)
""")

        con.execute("CREATE TABLE IF NOT EXISTS valid(inpId INTEGER PRIMARY KEY ASC)")

        con.execute("CREATE TABLE IF NOT EXISTS kpaths(inpId INTEGER PRIMARY KEY ASC, k INT, paths TEXT)")

    con.close()


def get_max_sid(test_id: str, db_file: str = std_db_file()) -> Optional[int]:
    create_db_tables(db_file)
    con = sqlite3.connect(db_file)

    with con:
        sid = None
        for row in con.execute("SELECT MAX(sid) FROM inputs WHERE testId = ?", (test_id,)):
            if row[0]:
                sid = row[0]
            break

    con.close()
    return sid


def store_inputs(test_id: str, inputs: Dict[float, isla.DerivationTree], db_file: str = std_db_file()) -> None:
    sid = (get_max_sid(test_id, db_file) or 0) + 1

    create_db_tables(db_file)
    con = sqlite3.connect(db_file)

    with con:
        reltime: float
        inp: isla.DerivationTree
        for reltime, inp in inputs.items():
            con.execute(
                "INSERT INTO inputs(testId, sid, reltime, inp) VALUES (?, ?, ?, ?)",
                (test_id, sid, reltime, json.dumps(inp.to_parse_tree())))

    con.close()


def get_inputs_from_db(
        test_id: str,
        sid: Optional[int] = None,
        db_file: str = std_db_file(),
        only_valid: bool = False
) -> Dict[int, isla.DerivationTree]:
    all_inputs_query = \
        """
        SELECT inpId, inp FROM inputs
        WHERE testId = ? AND sid = ?
        """

    valid_inputs_query = \
        """
        SELECT inpId, inp FROM inputs
        NATURAL JOIN valid
        WHERE testId = ? AND sid = ?
        """

    inputs: Dict[int, isla.DerivationTree] = {}

    # Get newest session ID if not present
    if sid is None:
        sid = get_max_sid(test_id, db_file)
        assert sid

    query = valid_inputs_query if only_valid else all_inputs_query
    con = sqlite3.connect(db_file)
    with con:
        for row in con.execute(query, (test_id, sid)):
            inputs[row[0]] = isla.DerivationTree.from_parse_tree(json.loads(row[1]))
    con.close()

    return inputs


def evaluate_validity(
        test_id: str,
        validator: Callable[[isla.DerivationTree], bool],
        db_file: str = std_db_file(),
        sid: Optional[int] = None) -> None:
    create_db_tables(db_file)

    # Get newest session ID if not present
    if sid is None:
        sid = get_max_sid(test_id, db_file)
        assert sid

    print(f"[{strtime()}] Evaluating validity for session {sid} of {test_id}")

    # Obtain inputs from session
    inputs = get_inputs_from_db(test_id, sid, db_file)

    # Evaluate (in parallel)
    def evaluate(inp_id: int, inp: isla.DerivationTree, queue: multiprocessing.Queue):
        try:
            if validator(inp) is True:
                queue.put(inp_id)
        except Exception as err:
            print(f"Exception {err} raise when validating input {inp}, tree: {repr(inp)}")

    manager = multiprocessing.Manager()
    queue = manager.Queue()
    with pmp.Pool(processes=pmp.cpu_count()) as pool:
        pool.starmap(evaluate, [(inp_id, inp, queue) for inp_id, inp in inputs.items()])

    # Insert into DB
    con = sqlite3.connect(db_file)
    with con:
        while not queue.empty():
            con.execute("INSERT INTO valid(inpId) VALUES (?)", (queue.get(),))
    con.close()

    print(f"[{strtime()}] DONE Evaluating validity for session {sid} of {test_id}")


def evaluate_kpaths(
        test_id: str,
        graph: gg.GrammarGraph,
        k: int = 3,
        db_file: str = std_db_file(),
        sid: Optional[int] = None) -> None:
    if os.environ.get("PYTHONHASHSEED") is None:
        print("WARNING: Environment variable PYTHONHASHSEED not set, "
              "should be set to 0 for deterministic hashing of k-paths", file=sys.stderr)
    if os.environ.get("PYTHONHASHSEED") is not None and os.environ["PYTHONHASHSEED"] != "0":
        print("WARNING: Environment variable PYTHONHASHSEED not set, "
              "should be set to 0 for deterministic hashing of k-paths", file=sys.stderr)

    create_db_tables(db_file)

    # Get newest session ID if not present
    if sid is None:
        sid = get_max_sid(test_id, db_file)
        assert sid

    print(f"[{strtime()}] Evaluating k-paths for session {sid} of {test_id}")

    # Obtain inputs from session
    inputs = get_inputs_from_db(test_id, sid, db_file, only_valid=True)

    # Evaluate (in parallel)
    def compute_k_paths(inp_id: int, inp: isla.DerivationTree, queue: multiprocessing.Queue):
        queue.put((inp_id, [hash(path) for path in graph.k_paths_in_tree(inp.to_parse_tree(), k)]))

    manager = multiprocessing.Manager()
    queue = manager.Queue()
    with pmp.Pool(processes=pmp.cpu_count()) as pool:
        pool.starmap(compute_k_paths, [(inp_id, inp, queue) for inp_id, inp in inputs.items()])

    # Insert into DB
    con = sqlite3.connect(db_file)
    with con:
        while not queue.empty():
            inp_id, path_hashes = queue.get()
            con.execute("INSERT INTO kpaths(inpId, k, paths) VALUES (?, ?, ?)", (inp_id, k, json.dumps(path_hashes)))
    con.close()

    print(f"[{strtime()}] DONE Evaluating k-paths for session {sid} of {test_id}")


def evaluate_data(
        data: Dict[float, isla.DerivationTree],
        formula: Optional[isla.Formula],
        graph: gg.GrammarGraph,
        validator: Callable[[isla.DerivationTree], bool],
        k: int = 3,
        jobname: str = "Unnamed",
        compute_kpath_coverage: bool = True,
        compute_vacuity: bool = True) -> PerformanceEvaluationResult:
    accumulated_valid_inputs: Dict[float, int] = {}
    accumulated_invalid_inputs: Dict[float, int] = {}
    accumulated_k_path_coverage: Dict[float, int] = {}
    accumulated_non_vacuous_index: Dict[float, float] = {}

    quantifier_chains: List[Tuple[isla.ForallFormula, ...]] = (
        [] if (not compute_vacuity or formula is None)
        else [tuple([f for f in c if isinstance(f, isla.ForallFormula)])
              for c in solver.get_quantifier_chains(formula)])

    valid_inputs: int = 0
    invalid_inputs: int = 0
    covered_kpaths: Set[Tuple[gg.Node, ...]] = set()
    chains_satisfied: Dict[Tuple[isla.ForallFormula, ...], int] = {c: 0 for c in quantifier_chains}

    for seconds, inp in data.items():
        try:
            validation_result = validator(inp)
        except Exception as err:
            validation_result = False
            print(f"Exception {err} raise when validating input {inp}, tree: {repr(inp)}")

        if validation_result is True:
            valid_inputs += 1
        else:
            invalid_inputs += 1
            accumulated_invalid_inputs[seconds] = invalid_inputs
            logger.debug("Input %s invalid", str(inp))
            continue

        if quantifier_chains:
            vacuously_matched_quantifiers = set()
            isla.eliminate_quantifiers(
                isla.instantiate_top_constant(formula, inp),
                vacuously_matched_quantifiers, graph.to_grammar())

            non_vacuous_chains = {
                c for c in quantifier_chains if
                all(of.id != f.id
                    for of in vacuously_matched_quantifiers
                    for f in c)}

            for c in non_vacuous_chains:
                assert c in chains_satisfied
                chains_satisfied[c] += 1

        accumulated_valid_inputs[seconds] = valid_inputs

        if compute_kpath_coverage:
            covered_kpaths.update(graph.k_paths_in_tree(inp.to_parse_tree(), k))
            accumulated_k_path_coverage[seconds] = int(len(covered_kpaths) * 100 / len(graph.k_paths(k)))

        if quantifier_chains and compute_vacuity:
            # Values in chains_satisfied range between 0 and `valid_inputs`, and thus the mean, too.
            chains_satisfied_mean = (
                    math.prod([v + 1 for v in chains_satisfied.values()]) ** (1 / len(chains_satisfied)) - 1)
            assert 0 <= chains_satisfied_mean <= valid_inputs
            # We normalize to a percentage-like value between 0 and 100
            accumulated_non_vacuous_index[seconds] = 100 * chains_satisfied_mean / valid_inputs
            assert 0 <= accumulated_non_vacuous_index[seconds] <= 100
        else:
            accumulated_non_vacuous_index[seconds] = 0

    result = PerformanceEvaluationResult(
        accumulated_valid_inputs,
        accumulated_invalid_inputs,
        accumulated_k_path_coverage,
        accumulated_non_vacuous_index)

    print(f"Final evaluation values: "
          f"{valid_inputs} valid inputs, "
          f"{invalid_inputs} invalid inputs, "
          f"{int(len(covered_kpaths) * 100 / len(graph.k_paths(k)))}% coverage, "
          f"{(list(accumulated_non_vacuous_index.values()) or [0])[-1]} non-vacuous index, "
          f"final mean: {(list(result.mean_data().values()) or [0])[-1]}, job: {jobname}")

    return result


def grammar_coverage_generator(grammar: Grammar) -> Generator[isla.DerivationTree, None, None]:
    fuzzer = GrammarCoverageFuzzer(grammar)
    while True:
        yield fuzzer.fuzz()


def evaluate_producer(
        producer: Union[Generator[isla.DerivationTree, None, None], ISLaSolver, Grammar],
        formula: Optional[isla.Formula],
        graph: gg.GrammarGraph,
        validator: Callable[[isla.DerivationTree], bool],
        outfile_pdf: Optional[str] = None,
        timeout_seconds: int = 60,
        diagram_title: str = "Performance Data",
        k=3,
        jobname: str = "Unnamed",
        compute_kpath_coverage: bool = True,
        compute_vacuity: bool = True) -> PerformanceEvaluationResult:
    print(f"Collecting performance data, job: {jobname}")
    data = generate_inputs(producer, timeout_seconds=timeout_seconds)
    print(f"Evaluating Data, job: {jobname}")

    evaluation_result = evaluate_data(
        data, formula, graph, validator, k,
        jobname=jobname,
        compute_kpath_coverage=compute_kpath_coverage,
        compute_vacuity=compute_vacuity)

    if outfile_pdf:
        print(f"Plotting result to {outfile_pdf}, job: {jobname}")
        evaluation_result.plot(outfile_pdf, title=diagram_title)

    return evaluation_result


def evaluate_generators(
        producers: List[Union[Grammar, ISLaSolver]],
        formula: Optional[isla.Formula],
        graph: gg.GrammarGraph,
        validator: Callable[[isla.DerivationTree], bool],
        timeout_seconds: int = 60,
        k=3,
        cpu_count: int = -1,
        jobnames: Optional[List[str]] = None,
        compute_kpath_coverage: bool = True,
        compute_vacuity: bool = True) -> List[PerformanceEvaluationResult]:
    assert jobnames is None or len(jobnames) == len(producers)
    if jobnames is None:
        jobnames = ["Unnamed" for _ in range(len(producers))]

    if cpu_count < 0:
        cpu_count = mp.cpu_count()

    if cpu_count < 2:
        return [
            evaluate_producer(
                producer,
                formula,
                graph,
                validator,
                timeout_seconds=timeout_seconds,
                k=k,
                jobname=jobname,
                compute_kpath_coverage=compute_kpath_coverage,
                compute_vacuity=compute_vacuity
            )
            for jobname, producer in zip(jobnames, producers)]

    with pmp.Pool(processes=cpu_count) as pool:
        return pool.starmap(evaluate_producer, [
            (producer, formula, graph, validator, None, timeout_seconds, "", k,
             jobname, compute_kpath_coverage, compute_vacuity)
            for jobname, producer in zip(jobnames, producers)])


def load_results(out_dir: str, base_name: str, jobnames: List[str]) -> List[PerformanceEvaluationResult]:
    return [PerformanceEvaluationResult.load_from_csv_file(
        out_dir, base_name + jobname) for jobname in jobnames]


def print_statistics(out_dir: str, base_name: str, jobnames: List[str]):
    results = load_results(out_dir, base_name, jobnames)
    for jobname, result in zip(jobnames, results):
        print(jobname + "\n" + "".join(["=" for _ in range(len(jobname))]) + "\n")

        valid_inputs = list(result.accumulated_valid_inputs.values() or [0])[-1]
        invalid_inputs = list(result.accumulated_invalid_inputs.values() or [0])[-1]
        max_kpath_cov = list(result.accumulated_k_path_coverage.values() or [0])[-1]

        # print("Seconds / input: " + "{:.1f}".format(result.max_time / (valid_inputs + invalid_inputs)))
        print("Inputs / second:       " + "{:.1f}".format((valid_inputs + invalid_inputs) / result.max_time))
        # print("Seconds / valid input: " + ("N/A" if not valid_inputs
        #                                    else "{:.1f}".format(result.max_time / valid_inputs)))
        print("Precision:             " + "{:.0f}".format(100 * valid_inputs / (valid_inputs + invalid_inputs)) + " %")
        print("k-path Coverage:       " + str(max_kpath_cov) + " %")

        print("\n")


def plot_proportion_valid_inputs_graph(
        out_dir: str, base_name: str, jobnames: List[str], outfile_pdf: str, show_final_values=False):
    assert outfile_pdf.endswith(".pdf")
    matplotlib.use("PDF")
    results = load_results(out_dir, base_name, jobnames)

    highest_seconds = max([result.max_time for result in results])

    fig, ax = plt.subplots()
    for jobname, result in zip(jobnames, results):
        data = result.valid_inputs_proportion_data()
        ax.plot(
            [.0] + list(data.keys()) + [highest_seconds],
            [list(data.values())[0]] + list(data.values()) + [list(data.values())[-1]],
            label=jobname)

        if show_final_values:
            label_val = "{:.2f}".format(100 * max(data.values())) + " %"

            plt.annotate(
                label_val,
                xy=(1, list(data.values())[-1]),
                xytext=(8, 0),
                xycoords=('axes fraction', 'data'),
                textcoords='offset points')

    ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    ax.set_xlabel("Seconds")
    ax.set_ylabel("% Valid Inputs")
    ax.legend()
    fig.tight_layout()
    plt.plot()

    matplotlib.pyplot.savefig(outfile_pdf)
