
from decimal import Decimal, FloatOperation, getcontext


c = getcontext()
c.prec = 8
c.traps[FloatOperation] = True


def d(v):
    return round(float(v), 4)  # Decimal(str(v))
