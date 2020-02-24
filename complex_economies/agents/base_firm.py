
import logging

from mesa import Agent

from complex_economies.utils.misc import d


class Firm(Agent):

    log = logging.getLogger(__name__)

    debt_stock = d(0)
    unit_production_cost = d(0)
    competitiveness = d(100)
    capital_employed = d(0)
    debt_employed = d(0)
    residual_assets = None
    available_debt = None

    bankrupt = False

    def __init__(self, unique_id, model, liquid_assets, market_share):
        super().__init__(unique_id, model)

        self.group = None

        self.liquid_assets = d(liquid_assets)
        self.market_share = d(market_share)

    def fix_price(self):
        return (1 + self.model.mark_up) * self.unit_production_cost

    def finance_operations(self, quantity, unit_cost):
        cost = unit_cost * quantity
        capital_employed = min(cost, self.residual_assets)
        debt_employed = min(cost - capital_employed, self.available_debt)
        return capital_employed, debt_employed
