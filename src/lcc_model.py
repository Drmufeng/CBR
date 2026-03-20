"""LCC 成本分解与计算模块。

当前文件先提供一个简化、可扩展的生命周期成本计算框架，
用于承接后续“购置-使用-回收”分项计算需求。
"""


class LCCCostModel:
    """新能源汽车 LCC 简化计算模型。"""

    def __init__(self, config=None):
        self.config = config or {
            'years': 10,
            'annual_mileage': 15000,
            'electricity_price': 0.7,
            'maintenance_per_year': 2000,
            'insurance_per_year': 4500,
            'residual_rate': 0.2,
        }

    def calculate(self, purchase_price, energy_consumption=None, maintenance_cost=None, insurance_cost=None, residual_rate=None):
        """计算总 LCC 及成本构成。

        参数说明：
        - purchase_price: 购置价格
        - energy_consumption: 百公里电耗，可为空，后续可由 CBR 估算补全
        - maintenance_cost: 年保养维修费用，可为空
        - insurance_cost: 年保险费用，可为空
        - residual_rate: 残值率，可为空
        """
        years = self.config['years']
        annual_mileage = self.config['annual_mileage']
        electricity_price = self.config['electricity_price']

        maintenance = maintenance_cost if maintenance_cost is not None else self.config['maintenance_per_year']
        insurance = insurance_cost if insurance_cost is not None else self.config['insurance_per_year']
        residual = residual_rate if residual_rate is not None else self.config['residual_rate']

        # 当前是简化版框架：若电耗未知，则使用 0 占位，后续由 CBR 或人工输入补全。
        if energy_consumption is None:
            energy_cost = 0.0
        else:
            energy_cost = annual_mileage / 100 * energy_consumption * electricity_price * years

        use_cost = energy_cost + maintenance * years + insurance * years
        recycle_income = purchase_price * residual
        total_lcc = purchase_price + use_cost - recycle_income

        return {
            '购置成本': float(purchase_price),
            '使用成本': float(use_cost),
            '回收收益': float(recycle_income),
            '总LCC': float(total_lcc),
            '明细': {
                '电费': float(energy_cost),
                '保养维修': float(maintenance * years),
                '保险': float(insurance * years),
                '残值回收': float(recycle_income),
            },
        }
