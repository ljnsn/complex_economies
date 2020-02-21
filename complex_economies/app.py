# -*- coding: utf-8 -*-
# from complex_economies.agents import CapitalGoodFirm, ConsumptionGoodFirm
from complex_economies.visualization import ChartModule, ModularApp, UserParam
from complex_economies.model import ComplexEconomy
from complex_economies.benchmark import benchmark_parameters


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

# dictionary of user settable parameters - these map to the model __init__ parameters
init_conditions = {
    "market_wage": UserParam(
        "slider", name="Market Wage", value=100, min_value=1, max_value=200,
        description="Initial market wage"
    ),
    "cpi": UserParam(
        "number", "Consumer Price Index", 1.3, 1, 2,
        description="Initial cpi level"
    ),
    "avg_labour_productivity": UserParam(
        "slider", "Average Labour Productivity", 100, 1, 200,
        description="Initial average labour productivity"
    ),
    "liquid_assets": UserParam(
        "slider", "Liquid Assets", 3000, 100, 10000,
        description="Initial liquid assets of each firm"
    ),
    "capital_stock": UserParam(
        "slider", "Capital Stock", 2000, 100, 10000,
        description="Initial capital stock of consumption firms"
    ),
    "labour_supply": UserParam(
        "slider", "Labour Supply", 3000, 100, 10000,
        description="Initial labour supply in the economy"
    ),
    # 'innovation': UserParam(
    #     "checkbox", name="Innovation", value=True,
    #     description="Whether there is innovation or not"
    # ),
}

model_params = {
    "parameters": benchmark_parameters,
    **init_conditions,
    "seed": 123456
}

# map data to chart in the ChartModule
chart_1 = ChartModule(title='Chart1', series=[
    {"Label": "gdp", "Color": gdp_colour},
    {"Label": "consumption", "Color": consumption_colour},
    {"Label": "production", "Color": production_colour},
    {"Label": "investment", "Color": investment_colour},
    {"Label": "inventories", "Color": inventories_colour}
])

chart_2 = ChartModule(title='Chart2', series=[
    {"Label": "labour_supply", "Color": gdp_colour},
    {"Label": "labour_demand", "Color": consumption_colour},
    {"Label": "employment", "Color": production_colour},
    {"Label": "unemployment", "Color": investment_colour}
])

chart_3 = ChartModule(title='Chart3', series=[
    {"Label": "avg_comp_competitiveness", "Color": gdp_colour},
    {"Label": "avg_cap_competitiveness", "Color": consumption_colour},
    {"Label": "market_wage", "Color": production_colour}
])
# TODO: plot prices and debt_stock / liquidity


# create instance of Mesa ModularServer
def makeserver(app):
    mod_app = ModularApp(
        app,
        ComplexEconomy, [chart_1, chart_2, chart_3],
        "Complex Economy Model",
        model_params=model_params
    )
    return mod_app.server
