
model_init_message = """\
Initialising complex economy model with initial values
    Market wage: {wage},
    CPI: {cpi},
    Average labour productivity: {avg_labour_prod},
    Labour supply: {labour_supply},
    Initial market share:
        Consumption: {comp_market_share},
        Capital: {cap_market_share}
    Employment: {employment},
    Consumption: {consumption}
    Unemployment rate: {unemployment_rate}

Parameters are:
    {parameters}
"""

stage_message = """\
Step: {step} - Stage: {stage} - Group: {group} - Agent: {agent_id}
"""

comp_stage_one = stage_message + """
    Residual assets: {res_assets},
    Available debt: {res_debt},
    Unfilled demand rate: {unfilled_demand},
    Average productivity: {avg_prod},
    Unit production cost: {upc},
    Price: {price},
    Competitiveness: {compet}
"""

comp_stage_two = stage_message + """
    Expected demand: {demand_e},
    Desired production: {production_d},
    Desired capital stock: {cap_stock_d},
    Planned production: {production_p},
    Labour demand: {labour_demand},
    Supplier: {supplier},
    Scrap stock: {scrap},
    Expansion investment: {expansion_i},
    Replacement investment: {replacement_i}
"""

comp_stage_three = stage_message + """
    _pass_
"""

comp_stage_four = stage_message + """
    Market share: {market_share},
    Demand: {demand},
    Production: {production},
    Output: {output},
    Sales: {sales},
    Inventory: {inventory},
    Profit: {profit},
    Liquid assets: {assets}
"""

cap_stage_one = stage_message + """

"""
