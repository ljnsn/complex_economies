
import logging

from complex_economies.model import ComplexEconomy
from complex_economies.utils.misc import d


open('model.log', 'w').close()

log = logging.getLogger()
log.setLevel('DEBUG')
fh = logging.FileHandler('model.log')
fh.setLevel('DEBUG')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
log.addHandler(fh)

benchmark_parameters = {
    'sample_size': d(600),
    'n_consumption_firms': d(200),
    'n_capital_firms': d(50),
    'replicator_dynamics_coeff': (d(-.5), d(-.5)),
    'competitiveness_weights': ((1, 1), (1, 1)),
    # 'distribution_lower_bound': -.5,
    # 'distribution_upper_bound': .5,
    'distribution_bounds': (d(-.5), d(.5)),
    'labour_supply_growth': d(.01),  # .01
    'wage_setting': {
        'cpi_weight': d(.75),
        'avg_lp_weight': d(1),
        'unemployment_weight': d(.1)
    },
    'desired_capital_utilization': d(.75),
    'trigger_rule': d(.1),
    'payback_period_parameter': d(4),
    'mark_up': d(.3),
    'interest_rate': d(.01),
    'wage_share': d(0.1),  # .1 in first paper, .33 in second
    'betas': [d(.7), d(.3), d(0), d(0), d(.25), d(1), d(.05), d(.25)],
    'max_debt_sales_ratio': d(1)  # this is not provided in the paper
}

initial_conditions = {
    'market_wage': d(100),
    'cpi': d(1.3),
    'avg_labour_productivity': d(100),
    'liquid_assets': d(3000),
    'capital_stock': d(2000),
    'labour_supply': d(3000)
}

seed = 123456
m = ComplexEconomy(
    parameters=benchmark_parameters,
    market_wage=initial_conditions['market_wage'],
    cpi=initial_conditions['cpi'],
    avg_labour_productivity=initial_conditions['avg_labour_productivity'],
    liquid_assets=initial_conditions['liquid_assets'],
    capital_stock=initial_conditions['capital_stock'],
    labour_supply=initial_conditions['labour_supply'],
    innovation=False,
    social_policy='base',
    inventory_deprecation=0,
    fix_supplier=True,
    seed=seed
)


def run(steps):
    for n in range(steps):
        m.step()
    return m
