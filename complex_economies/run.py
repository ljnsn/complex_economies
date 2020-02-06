
import logging

from complex_economies.model import ComplexEconomy


def run(steps, params, init_conditions, seed=None):

    log = logging.getLogger(__name__)

    m = ComplexEconomy(
        parameters=params,
        market_wage=init_conditions['market_wage'],
        cpi=init_conditions['cpi'],
        avg_labour_productivity=init_conditions['avg_labour_productivity'],
        liquid_assets=init_conditions['liquid_assets'],
        capital_stock=init_conditions['capital_stock'],
        labour_supply=init_conditions['labour_supply'],
        seed=seed
    )

    for n in range(steps):
        try:
            m.step()
        except Exception:
            log.exception(f'The run stopped early at step {n}')
            print(f'The run stopped early at step {n}')
            return m
    return m
