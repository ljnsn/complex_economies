
benchmark_parameters = {
    'sample_size': 600,
    'n_consumption_firms': 200,
    'n_capital_firms': 50,
    'replicator_dynamics_coeff': (-.5, -.5),
    'competitiveness_weights': ((1, 1), (1, 1)),
    'distribution_bounds': (-.05, .05),  # labour prod seems to increase way too fast
    'labour_supply_growth': 0,  # .01
    'wage_setting': {
        'cpi_weight': 0.75,  # .75
        'avg_lp_weight': 1,
        'unemployment_weight': .1  # .1
    },
    'desired_capital_utilization': .75,
    'trigger_rule': .1,
    'payback_period_parameter': 4,
    'mark_up': .3,
    'interest_rate': .01,
    'wage_share': 0.1,  # .1 in first paper, .33 in second
    'betas': [.7, .3, 0, 0, .25, 1, .05, .25],
    'max_debt_sales_ratio': 1,  # this is not provided in the paper
    # added by me
    'innovation': False,
    'social_policy': 'base',  # at the moment, 'base' and 'welfare' are possible
    'inventory_deprecation': 0,
    'fix_supplier': True,
    # TODO: add supplier subset as param
}
