# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import production

def register():
    Pool.register(
        production.Production,
        production.SplitProductionStart,
        module='production_split_serial_number', type_='model')
    Pool.register(
        production.SplitProduction,
        module='production_split_serial_number', type_='wizard')
