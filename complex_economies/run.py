
from datetime import datetime
import logging

from complex_economies.model import ComplexEconomy


log = logging.getLogger()
log.setLevel('DEBUG')
fh = logging.FileHandler(f'model_{int(datetime.now().timestamp())}.log')
fh.setLevel('DEBUG')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)


def run(steps, params, init_conditions, seed=None):

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
            print(f'The run stopped early at step {n}')
            return m
    return m
