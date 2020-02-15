
from copy import deepcopy
import logging
from pprint import pformat

from mesa import Agent
# from numpy.random import uniform

from complex_economies.utils import messages
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


class ConsumptionGoodFirm(Firm):

    inventory = d(0)
    unfilled_demand_rate = d(0)
    average_productivity = d(0)
    price = d(0)
    expected_demand = d(0)
    desired_production = d(0)
    desired_capital_stock = d(0)
    production_rationed = False
    planned_production = d(0)
    want_to_scrap = []
    desired_ei = d(0)
    desired_ri = d(0)
    expansion_investment = d(0)
    replacement_investment = d(0)
    labour_demand = d(0)
    profit = d(0)

    def __init__(self, unique_id, model, liquid_assets, capital_stock,
                 market_share, supplier=None):
        super().__init__(unique_id, model, liquid_assets, market_share)

        self.group = 'consumption_firm'
        self.supplier = supplier

        # initial values
        self.capital_stock = capital_stock

        # calculated
        capital_firms = self.model.get_group('capital_firm')
        self.machines = {
            (supplier.unique_id, supplier.machine.generation): {
                'machine': supplier.machine,
                'stock': 40
            } for supplier in capital_firms
        }
        self.demand = self.market_share * self.model.consumption  # / self.model.cpi
        self.production = self.demand
        self.output = self.production
        self.sales = self.output

        row = {
            'step': -1,
            'agent_id': self.unique_id,
            'market_share': self.market_share,
            'demand': self.demand,
            'production': self.production,
            'output': self.output,
            'inventory': self.inventory,
            'sales': self.sales,
            'liquid_assets': self.liquid_assets,
            'capital_stock': self.capital_stock,
            'debt_stock': self.debt_stock,
            'supplier': self.supplier
        }
        self.model.datacollector.add_table_row(
            'consumption_firm', row, ignore_missing=True
        )

    @property
    def investment(self):
        return self.expansion_investment + self.replacement_investment

    @property
    def available_financing(self):
        return self.residual_assets + self.available_debt

    def compute_max_quantity(self, unit_cost):
        return d(int(self.available_financing / unit_cost))

    def compute_unfilled_demand(self):
        if self.demand == 0:
            return 0
        return 1 - self.sales / self.demand

    def compute_average_productivity(self):
        productivities = []
        machine_set = list(self.machines.keys())
        for machine_type in machine_set:
            machine = self.machines[machine_type]['machine']
            stock = self.machines[machine_type]['stock']
            productivity = (
                machine.labour_productivity_coefficient * stock
            )
            productivities.append(productivity)
        avgp = sum(productivities) / self.capital_stock
        return d(float(avgp))

    def compute_unit_production_cost(self):
        return (
            self.model.market_wage / self.average_productivity
        )

    def adjust_competitiveness(self):
        w1, w2 = self.model.competitiveness_weights[0]
        adj = round(-w1 * self.price - w2 * self.unfilled_demand_rate, 2)
        self.competitiveness = max(0, self.competitiveness - adj)

    def compute_debt_availability(self):
        max_debt = self.model.max_debt_sales_ratio * self.sales
        return max(0, max_debt - self.debt_stock)

    def forecast_demand(self, myopic=True):
        if myopic:
            return self.demand
        firm_data = self.model.datacollector.get_table_dataframe(
            'consumption_firm'
        )
        # model_data = self.model.datacollector.get_model_vars_dataframe()
        past_demand = firm_data.loc[
            firm_data.agent_id == self.unique_id, 'demand'
        ].tolist()[-4:]
        return sum([
            b * d(t) for b, t in zip(self.model.betas, past_demand)
        ])

    def forecast_production(self):
        demand_net = self.expected_demand - self.inventory
        return max(0, demand_net)

    def forecast_capital_stock(self):
        return d(int(
            self.desired_production / self.model.desired_capital_utilization
        ))

    def plan_production(self):
        production_max = self.compute_max_quantity(
            self.unit_production_cost
        )
        production = min(self.desired_production, production_max)
        # check if production has to be rationed
        if production < self.desired_production:
            self.production_rationed = True
        else:
            self.production_rationed = False
        return production

    def plan_production_financing(self):
        return self.finance_operations(
            self.planned_production, self.unit_production_cost
        )

    def compute_labour_demand(self):
        return self.planned_production / self.average_productivity

    def forecast_expansion_investment(self):
        trigger_level = d(int(self.capital_stock * (1 + self.model.trigger_rule)))
        planned_ei = 0
        if self.desired_capital_stock >= trigger_level:
            # NOTE: in paper this is trigger_level
            planned_ei = trigger_level - self.capital_stock
        return planned_ei

    def choose_supplier(self, subset=10):
        # NOTE: in the paper, supplier is chosen based on market share
        current_supplier = self.model.schedule.get_agent(self.supplier, _raise=False)
        capital_firms = self.model.get_group('capital_firm')
        sample = self.random.sample(capital_firms, subset)
        ratios = [s.machine.lpc_price_ratio for s in sample]
        new_supplier_id = sample[ratios.index(max(ratios))].unique_id
        if not current_supplier or current_supplier.bankrupt:
            return new_supplier_id
        return (
            new_supplier_id
            if max(ratios) > current_supplier.machine.lpc_price_ratio
            else self.supplier  # NOTE: causes consolidation in cap market?
        )

    def plan_replacement(self):
        supplier = self.model.schedule.get_agent(self.supplier)
        machine_set = [k for k, v in self.machines.items() if v['stock'] > 0]
        want_to_scrap = []
        for machine_type in machine_set:
            machine = self.machines[machine_type]['machine']
            unit_labour_cost = machine.compute_unit_labour_cost(self.model)
            if unit_labour_cost == supplier.unit_production_cost:
                continue
            x = (
                supplier.price
                / (unit_labour_cost - supplier.unit_production_cost)
            )
            if x <= self.model.payback_period_parameter:
                want_to_scrap.append(machine_type)
        return want_to_scrap

    def forecast_replacement_investment(self):
        return sum([self.machines[m]['stock'] for m in self.want_to_scrap])

    def fix_investment(self):
        """Allocate between expanding capital stock and replacement
        """
        if self.production_rationed:
            return 0, 0
        machine_cost = self.model.schedule.get_agent(self.supplier).machine.price
        ce_q, de_q = self.plan_production_financing()
        self.residual_assets -= ce_q
        self.available_debt -= de_q
        investment_max = self.compute_max_quantity(machine_cost)

        expansion_i = min(self.desired_ei, investment_max)
        ce_ei, de_ei = self.finance_operations(expansion_i, machine_cost)
        self.residual_assets -= ce_ei
        self.available_debt -= de_ei

        replacement_i = min(self.desired_ri, investment_max - expansion_i)
        ce_ri, de_ri = self.finance_operations(replacement_i, machine_cost)
        self.residual_assets = self.residual_assets - ce_ri + ce_q
        self.available_debt = self.available_debt - de_ri + de_q

        self.capital_employed = ce_ei + ce_ri
        self.debt_employed = de_ei + de_ri

        return expansion_i, replacement_i

    def compute_market_share(self):
        sector_avg_comp = self.model.avg_comp_competitiveness
        if self.unique_id == 50:
            self.log.info('computing market share')
            self.log.info(f'own competitiveness: {self.competitiveness}')
            self.log.info(f'sector average competitiveness: {sector_avg_comp}')
        ms = (
            self.market_share
            * (1 + self.model.replicator_dynamics_coeff[0]
               * (self.competitiveness - sector_avg_comp)
               / sector_avg_comp)
        )
        return d(max(0, ms))

    def compute_demand(self):  # TODO: should be dependant on price?
        return self.model.consumption * self.market_share  # / self.price

    def compute_labour_availability(self):
        return self.market_share * (
            self.model.labour_supply - self.model.capital_labour_demand
        )

    def fix_production(self):
        labour_res = self.compute_labour_availability()
        max_q = labour_res * self.average_productivity
        production = min(max_q, self.planned_production)
        ce_q, de_q = self.finance_operations(production, self.unit_production_cost)
        self.residual_assets -= ce_q
        self.available_debt -= de_q
        self.debt_stock += self.debt_employed + de_q
        return production

    def compute_sales(self):
        return min(self.demand, self.output)

    def compute_inventory(self):
        inventory = self.output - self.sales
        # deprecate inventory
        if inventory > 0:
            inventory = (
                int(inventory * (1 - self.model.inventory_deprecation))
            )
        return inventory

    def compute_profit(self):
        revenue = self.price * self.sales
        production_cost = self.unit_production_cost * self.production
        debt_payments = self.model.interest_rate * self.debt_stock
        return revenue - production_cost - debt_payments

    def compute_liquid_assets(self):
        return self.liquid_assets + self.profit - self.capital_employed

    def reimburse_investment(self, received_orders):
        self.liquid_assets += (
            received_orders * self.model.schedule.get_agent(self.supplier).price
        )
        if received_orders < self.expansion_investment:
            self.expansion_investment = received_orders
            self.replacement_investment = 0
        else:
            self.replacement_investment = received_orders - self.expansion_investment

    def replace_and_add_machines(self):  # TODO: add logging
        supplier = self.model.schedule.get_agent(self.supplier)
        if supplier.output < supplier.demand:
            # assign residual orders to firms
            received_orders = (
                int(d(self.investment / supplier.orders) * supplier.output)
            )
            self.reimburse_investment(received_orders)
        new_machines = self.expansion_investment
        for machine_type in self.want_to_scrap:
            stock = self.machines[machine_type]['stock']
            if stock <= self.replacement_investment:
                self.machines.pop(machine_type)
                new_machines += stock
            else:
                self.machines[machine_type]['stock'] -= self.replacement_investment
                new_machines += self.replacement_investment
                break
        new_type = (supplier.unique_id, supplier.machine.generation)
        if new_type in self.machines:
            self.machines[new_type]['stock'] += new_machines
            return None
        self.machines[new_type] = {
            'machine': deepcopy(supplier.machine),
            'stock': new_machines
        }

    def compute_capital_stock(self):
        return sum([mtype['stock'] for mtype in self.machines.values()])

    # stage methods
    def stage_one(self):
        if self.bankrupt:
            return None

        self.residual_assets = self.liquid_assets
        self.available_debt = self.compute_debt_availability()

        self.unfilled_demand_rate = self.compute_unfilled_demand()
        self.average_productivity = self.compute_average_productivity()
        self.unit_production_cost = self.compute_unit_production_cost()
        self.price = self.fix_price()
        # if demand was underestimated, competitiveness decreases
        if self.output < self.demand:
            self.adjust_competitiveness()
        # self.debt_availability = self.compute_debt_availability()

        if self.unique_id == 50:
            self.log.info(messages.comp_stage_one.format(
                step=self.model.schedule.steps,
                stage=self.model.schedule.stage,
                group=self.group,
                agent_id=self.unique_id,
                res_assets=self.residual_assets,
                res_debt=self.available_debt,
                unfilled_demand=self.unfilled_demand_rate,
                avg_prod=self.average_productivity,
                upc=self.unit_production_cost,
                price=self.price,
                compet=self.competitiveness
            ))

    def stage_two(self):
        if self.bankrupt:
            return None

        self.expected_demand = self.forecast_demand()
        self.desired_production = self.forecast_production()
        self.desired_capital_stock = self.forecast_capital_stock()
        self.planned_production = self.plan_production()
        self.labour_demand = self.compute_labour_demand()
        self.supplier = self.choose_supplier()
        self.want_to_scrap = self.plan_replacement()
        self.desired_ei = self.forecast_expansion_investment()
        self.desired_ri = self.forecast_replacement_investment()
        self.expansion_investment, self.replacement_investment = self.fix_investment()
        # register order with supplier
        self.model.schedule.get_agent(self.supplier).orders += self.investment

        if self.unique_id == 50:
            self.log.info(messages.comp_stage_two.format(
                step=self.model.schedule.steps,
                stage=self.model.schedule.stage,
                group=self.group,
                agent_id=self.unique_id,
                demand_e=self.expected_demand,
                production_d=self.desired_production,
                cap_stock_d=self.desired_capital_stock,
                production_p=self.planned_production,
                labour_demand=self.labour_demand,
                supplier=self.supplier,
                scrap=pformat(self.want_to_scrap),
                expansion_i=self.expansion_investment,
                replacement_i=self.replacement_investment
            ))

    def stage_three(self):
        if self.bankrupt:
            return None

        pass

    def stage_four(self):
        if self.bankrupt:
            return None

        self.market_share = self.compute_market_share()
        self.demand = self.compute_demand()
        self.production = self.fix_production()  # need to adjust labour demand here
        self.output = self.production + self.inventory
        self.sales = self.compute_sales()
        self.inventory = self.compute_inventory()
        self.profit = self.compute_profit()
        self.liquid_assets = self.compute_liquid_assets()

        if self.unique_id == 50:
            self.log.info(messages.comp_stage_four.format(
                step=self.model.schedule.steps,
                stage=self.model.schedule.stage,
                group=self.group,
                agent_id=self.unique_id,
                market_share=self.market_share,
                demand=self.demand,
                production=self.production,
                output=self.output,
                sales=self.sales,
                inventory=self.inventory,
                profit=self.profit,
                assets=self.liquid_assets
            ))

    def stage_five(self):

        row = {
            'step': self.model.schedule.steps,
            'agent_id': self.unique_id,
            'competitiveness': self.competitiveness,
            'expected_demand': self.expected_demand,
            'market_share': self.market_share,
            'demand': self.demand,
            'desired_production': self.desired_production,
            'desired_capital_stock': self.desired_capital_stock,
            'labour_demand': self.labour_demand,
            'desired_ei': self.desired_ei,
            'desired_ri': self.desired_ri,
            'supplier': self.supplier,
            'expansion_investment': self.expansion_investment,
            'replacement_investment': self.replacement_investment,
            'production': self.production,
            'output': self.output,
            'inventory': self.inventory,
            'sales': self.sales,
            'profit': self.profit,
            'liquid_assets': self.liquid_assets,
            'capital_stock': self.capital_stock,
            'debt_stock': self.debt_stock,
            'price': self.price,
            'upc': self.unit_production_cost,
            'average_productivity': self.average_productivity,
            'available_debt': self.available_debt,
            'bankrupt': self.bankrupt
        }
        self.model.datacollector.add_table_row('consumption_firm', row)

        if self.bankrupt:
            return None

        self.replace_and_add_machines()
        self.capital_stock = self.compute_capital_stock()


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
