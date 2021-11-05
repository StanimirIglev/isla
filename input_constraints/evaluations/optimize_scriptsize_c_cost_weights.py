import logging
import random

from input_constraints import isla
from input_constraints.evaluator import auto_tune_weight_vector
from input_constraints.tests.subject_languages.scriptsizec import SCRIPTSIZE_C_GRAMMAR, compile_scriptsizec_clang, \
    SCRIPTSIZE_C_DEF_USE_CONSTR, SCRIPTSIZE_C_NO_REDEF_CONSTR


def validator(t: isla.DerivationTree) -> bool:
    return compile_scriptsizec_clang(t) is True


if __name__ == '__main__':
    logger = logging.getLogger("optim_scriptsize_c")
    logging.basicConfig(level=logging.ERROR)
    logging.getLogger("evaluator").setLevel(logging.INFO)
    logger.setLevel(logging.INFO)

    # seed = random.randint(-1000, 1000)
    # seed = random.randint(-1000, 1000)
    # seed = random.randint(-1000, 1000)
    # seed = random.randint(-1000, 1000)
    # logger.info("Seed: %d", seed)
    # random.seed(seed)

    random.seed(1245498451)

    tune_result = auto_tune_weight_vector(
        SCRIPTSIZE_C_GRAMMAR,
        SCRIPTSIZE_C_DEF_USE_CONSTR,  # & SCRIPTSIZE_C_NO_REDEF_CONSTR,
        validator,
        timeout=120,
        population_size=20,
        generations=4,
    )

    tune_result[0].plot("/tmp/scriptsize_c_autotune_result_state.pdf", "Scriptsize-C Auto-Tune Result Config Stats")
