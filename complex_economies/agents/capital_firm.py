
from complex_economies.agents.base_firm import Firm
from complex_economies.utils.misc import d


class Machine:
    def __init__(self, producer, generation, lpc, price):
        self.producer = producer
        self.generation = generation
        self.labour_productivity_coefficient = lpc
        self.price = price

    @property
    def lpc_price_ratio(self):
        return self.labour_productivity_coefficient / self.price

    def compute_unit_labour_cost(self, model):
        return model.market_wage / self.labour_productivity_coefficient


class CapitalGoodFirm(Firm):

    # debt_stock = 0
    # unit_production_cost = 1
    demand = d(0)
    output = d(0)
    sales = d(0)
    labour_demand = d(0)
    profit = d(0)
    orders = d(0)

    def __init__(self, unique_id, model, liquid_assets, market_share, **kwargs):
        super().__init__(unique_id, model, liquid_assets, market_share)

        self.group = 'capital_firm'

        self.machine = Machine(
            producer=unique_id,
            generation=1,
            lpc=d(100),
            price=d(1)
        )

    @property
    def price(self):
        return self.machine.price

    @property
    def available_financing(self):
        return self.residual_assets + self.available_debt

    def compute_max_quantity(self, unit_cost):
        return self.available_financing // unit_cost

    @property
    def max_production(self):
        max_labour = self.market_share * self.model.max_capital_labour
        max_quantity = self.compute_max_quantity(self.unit_production_cost)
        return min(
            max_quantity,
            max_labour * self.machine.labour_productivity_coefficient
        )

    def compute_unit_production_cost(self):
        return (
            self.model.market_wage
            / self.machine.labour_productivity_coefficient
        )

    def compute_competitiveness(self):
        w3, w4 = self.model.competitiveness_weights[1]
        return (
            -w3 * self.machine.price + w4 * self.machine.labour_productivity_coefficient
        )

    def compute_debt_availability(self):
        max_debt = self.model.max_debt_sales_ratio * self.sales
        return max(0, max_debt - self.debt_stock)

    def compute_demand(self):
        # consumption_firms = self.model.get_group('consumption_firm')
        # return sum([
        #     a.investment for a in consumption_firms
        #     if a.supplier == self.unique_id
        # ])
        return self.orders

    def fix_production(self):
        production = min(self.demand, self.max_production)
        ce, de = self.finance_operations(production, self.unit_production_cost)
        self.debt_stock += de
        return production

    def compute_labour_demand(self):
        return (
            self.output / self.machine.labour_productivity_coefficient
        )

    def compute_profit(self):
        return (
            (self.price - self.unit_production_cost) * self.sales
            - self.model.interest_rate * self.debt_stock
        )

    def compute_liquid_assets(self):
        return self.liquid_assets + self.profit

    def compute_market_share(self):
        investment = self.model.investment
        market_share = (
            d(self.demand / investment) if investment > 0 else self.market_share
        )
        return market_share

    def innovate(self):
        if not self.model.innovation:
            return None
        epsilon = d(self.random.uniform(*self.model.distribution_bounds))
        new_lpc = (
            self.machine.labour_productivity_coefficient
            * (1 + epsilon)
        )
        if new_lpc > self.machine.labour_productivity_coefficient:
            self.machine = Machine(
                producer=self.unique_id,
                generation=self.machine.generation + 1,
                lpc=new_lpc,
                price=self.machine.price
            )

    # stage methods
    def stage_one(self):
        if self.bankrupt:
            return None

        self.residual_assets = self.liquid_assets
        self.available_debt = self.compute_debt_availability()

        self.unit_production_cost = self.compute_unit_production_cost()
        self.machine.price = self.fix_price()
        self.competitiveness = self.compute_competitiveness()

    def stage_two(self):
        if self.bankrupt:
            return None

    def stage_three(self):
        if self.bankrupt:
            return None

        self.demand = self.compute_demand()
        self.output = self.sales = self.fix_production()
        self.labour_demand = self.compute_labour_demand()
        self.profit = self.compute_profit()
        self.liquid_assets = self.compute_liquid_assets()
        self.market_share = self.compute_market_share()

    def stage_four(self):
        if self.bankrupt:
            return None

    def stage_five(self):

        row = {
            'step': self.model.schedule.steps,
            'agent_id': self.unique_id,
            'competitiveness': self.competitiveness,
            'demand': self.demand,
            'production': self.output,
            'labour_demand': self.labour_demand,
            'output': self.output,
            'sales': self.sales,
            'profit': self.profit,
            'liquid_assets': self.liquid_assets,
            'debt_stock': self.debt_stock,
            'market_share': self.market_share,
            'machine_generation': self.machine.generation,
            'price': self.price,
            'upc': self.unit_production_cost,
            'labour_productivity': self.machine.labour_productivity_coefficient,
            'available_debt': self.available_debt,
            'bankrupt': self.bankrupt
        }

        self.model.datacollector.add_table_row('capital_firm', row)

        if self.bankrupt:
            return None

        self.innovate()
        self.orders = 0
