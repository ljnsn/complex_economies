
from decimal import Decimal, FloatOperation, getcontext


c = getcontext()
c.prec = 8
c.traps[FloatOperation] = True


def d(v):
    return Decimal(str(v)) # round(float(v), 4)
