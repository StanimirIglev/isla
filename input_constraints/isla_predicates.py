import copy
from typing import Union, Optional

from fuzzingbook.Parser import canonical, EarleyParser
from grammar_graph.gg import GrammarGraph

from input_constraints.existential_helpers import insert_tree
from input_constraints.helpers import is_before, delete_unreachable
from input_constraints.isla import DerivationTree, Constant, SemPredEvalResult, StructuralPredicate, SemanticPredicate
from input_constraints.type_defs import Grammar

BEFORE_PREDICATE = StructuralPredicate("before", 2, is_before)


def count(grammar: Grammar,
          in_tree: DerivationTree,
          needle: str,
          num: Union[Constant, DerivationTree]) -> SemPredEvalResult:
    num_needle_occurrences = len(in_tree.filter(lambda t: t.value == needle))

    graph = GrammarGraph.from_grammar(grammar)
    leaf_nonterminals = [node.value for _, node in in_tree.open_leaves()]

    more_needles_possible = any(graph.get_node(leaf_nonterminal).reachable(graph.get_node(needle))
                                for leaf_nonterminal in leaf_nonterminals)

    if isinstance(num, Constant):
        # Return the number of needle occurrences in in_tree, or "not ready" if in_tree is not
        # closed and more needle occurrences can yet occur in in_tree
        if more_needles_possible:
            return SemPredEvalResult(None)

        return SemPredEvalResult({num: DerivationTree(str(num_needle_occurrences), None)})

    assert not num.children
    assert num.value.isnumeric()
    target_num_needle_occurrences = int(num.value)

    if num_needle_occurrences > target_num_needle_occurrences:
        return SemPredEvalResult(False)

    if not more_needles_possible:
        # TODO: We could also try to insert needle into already closed parts of the tree,
        #       similar to treatment of existential quantifiers...
        if num_needle_occurrences == target_num_needle_occurrences:
            return SemPredEvalResult(True)
        else:
            return SemPredEvalResult(False)

    if more_needles_possible and num_needle_occurrences == target_num_needle_occurrences:
        return SemPredEvalResult(None)

    assert num_needle_occurrences < target_num_needle_occurrences

    # Try to add more needles to in_tree, such that no more needles can be obtained
    # in the resulting tree from expanding leaf nonterminals.

    num_needles = lambda candidate: len(candidate.filter(lambda t: t.value == needle))

    canonical_grammar = canonical(grammar)
    candidates = [candidate for candidate in insert_tree(canonical_grammar, DerivationTree(needle, None), in_tree)
                  if num_needles(candidate) <= target_num_needle_occurrences]
    already_seen = {candidate.structural_hash() for candidate in candidates}
    while candidates:
        candidate = candidates.pop(0)
        candidate_needle_occurrences = num_needles(candidate)

        candidate_more_needles_possible = \
            any(graph.get_node(leaf_nonterminal).reachable(graph.get_node(needle))
                for leaf_nonterminal in [node.value for _, node in candidate.open_leaves()])

        if not candidate_more_needles_possible and candidate_needle_occurrences == target_num_needle_occurrences:
            return SemPredEvalResult({in_tree: candidate})

        if candidate_needle_occurrences < target_num_needle_occurrences:
            new_candidates = [
                new_candidate
                for new_candidate in insert_tree(canonical_grammar, DerivationTree(needle, None), candidate)
                if (num_needles(new_candidate) <= target_num_needle_occurrences
                    and not new_candidate.structural_hash() in already_seen)]

            candidates.extend(new_candidates)
            already_seen.update({new_candidate.structural_hash() for new_candidate in new_candidates})

    # TODO: Check if None would not be more appropriate. Could we have missed a better insertion opportunity?
    return SemPredEvalResult(False)


COUNT_PREDICATE = lambda grammar: SemanticPredicate(
    "count", 3, lambda in_tree, needle, num: count(grammar, in_tree, needle, num))


def ljust(grammar: Grammar,
          tree: DerivationTree,
          width: int,
          fillchar: str) -> SemPredEvalResult:
    if len(fillchar) != 1:
        raise TypeError("The fill character must be exactly one character long")

    if not tree.is_complete():
        return SemPredEvalResult(None)

    unparsed = str(tree)

    if len(unparsed) == width:
        return SemPredEvalResult(True)

    if len(unparsed) > width:
        return SemPredEvalResult(False)

    specialized_grammar = copy.deepcopy(grammar)
    specialized_grammar["<start>"] = [tree.value]
    delete_unreachable(specialized_grammar)
    parser = EarleyParser(specialized_grammar)

    unparsed_output = unparsed.ljust(width, fillchar)
    result = DerivationTree.from_parse_tree(list(parser.parse(unparsed_output))[0])
    return SemPredEvalResult({tree: result})


LJUST_PREDICATE = lambda grammar: SemanticPredicate(
    "ljust", 3, lambda tree, width, fillchar: ljust(grammar, tree, width, fillchar))
