# -*- coding: utf-8 -*-
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter
# from complex_economies.agents import CapitalGoodFirm, ConsumptionGoodFirm
from complex_economies.model import ComplexEconomy


# Green
gdp_colour = "#46FF33"
# Red
consumption_colour = "#FF3C33"
# Blue
production_colour = "#3349FF"
# Turqoise
investment_colour = "#00FFFF"
# Pink
inventories_colour = "#FF00D3"

benchmark_parameters = {
    'sample_size': 600,
    'n_consumption_firms': 200,
    'n_capital_firms': 50,
    'replicator_dynamics_coeff': (-.5, -.5),
    'competitiveness_weights': ((1, 1), (1, 1)),
    'distribution_bounds': (-.5, .5),  # labour prod seems to increase way too fast
    'labour_supply_growth': .01,  # .01
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
    # 'innovation': False,
    'social_policy': 'base',  # at the moment, 'base' and 'welfare' are possible
    'inventory_deprecation': 0,
    'fix_supplier': True,
}

# dictionary of user settable parameters - these map to the model __init__ parameters
init_conditions = {
    "market_wage": UserSettableParameter(
        "slider", name="Market Wage", value=100, min_value=1, max_value=200,
        description="Initial market wage"
    ),
    "cpi": UserSettableParameter(
        "number", "Consumer Price Index", 1.3, 1, 2,
        description="Initial cpi level"
    ),
    "avg_labour_productivity": UserSettableParameter(
        "slider", "Average Labour Productivity", 100, 1, 200,
        description="Initial average labour productivity"
    ),
    "liquid_assets": UserSettableParameter(
        "slider", "Liquid Assets", 3000, 100, 10000,
        description="Initial liquid assets of each firm"
    ),
    "capital_stock": UserSettableParameter(
        "slider", "Capital Stock", 2000, 100, 10000,
        description="Initial capital stock of consumption firms"
    ),
    "labour_supply": UserSettableParameter(
        "slider", "Labour Supply", 3000, 100, 10000,
        description="Initial labour supply in the economy"
    ),
    'innovation': UserSettableParameter(
        "checkbox", name="Innovation", value=True,
        description="Whether there is innovation or not"
    ),
}

model_params = {
    "parameters": benchmark_parameters,
    **init_conditions,
    "seed": 123456
}

# map data to chart in the ChartModule
chart_1 = ChartModule([
    {"Label": "gdp", "Color": gdp_colour},
    {"Label": "consumption", "Color": consumption_colour},
    {"Label": "production", "Color": production_colour},
    {"Label": "investment", "Color": investment_colour},
    {"Label": "inventories", "Color": inventories_colour}
])

chart_2 = ChartModule([
    {"Label": "labour_supply", "Color": gdp_colour},
    {"Label": "labour_demand", "Color": consumption_colour},
    {"Label": "employment", "Color": production_colour},
    {"Label": "unemployment", "Color": investment_colour}
])

chart_3 = ChartModule([
    {"Label": "avg_comp_competitiveness", "Color": gdp_colour},
    {"Label": "avg_cap_competitiveness", "Color": consumption_colour},
    {"Label": "market_wage", "Color": production_colour}
])

# create instance of Mesa ModularServer
server = ModularServer(
    ComplexEconomy, [chart_1, chart_2, chart_3],
    "Complex Economy Model",
    model_params=model_params
)
