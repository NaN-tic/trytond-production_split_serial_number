# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Equal
from trytond.transaction import Transaction

__all__ = ['Production', 'SplitProductionStart', 'SplitProduction']


class Production(metaclass=PoolMeta):
    __name__ = 'production'

    def split(self, quantity, uom, count=None):
        productions = super(Production, self).split(quantity, uom, count=count)
        if Transaction().context.get('create_serial_numbers', True):
            for production in productions:
                production.add_serial_number_lot()
        return productions

    def add_serial_number_lot(self):
        pool = Pool()
        Lot = pool.get('stock.lot')
        for output in self.outputs:
            if output.quantity != 1.0 or output.lot:
                continue
            if not output.product.template.serial_number:
                continue
            if hasattr(output.__class__, 'get_production_output_lot'):
                lot = output.get_production_output_lot()
                lot.save()
            else:
                lot = Lot(product=output.product)
                lot.save()
            if lot:
                output.lot = lot
                output.save()


class SplitProductionStart(metaclass=PoolMeta):
    __name__ = 'production.split.start'

    create_serial_numbers = fields.Boolean('Create Serial Numbers?',
        states={
            'invisible': ~Equal(Eval('quantity', 0), 1),
            },
        depends=['quantity'])

    @staticmethod
    def default_create_serial_numbers():
        return False


class SplitProduction(metaclass=PoolMeta):
    __name__ = 'production.split'

    def default_start(self, fields):
        pool = Pool()
        Production = pool.get('production')
        default = super(SplitProduction, self).default_start(fields)
        production = Production(Transaction().context['active_id'])
        if production.product and production.product.template.serial_number:
            default['quantity'] = 1.0
            default['create_serial_numbers'] = True
        return default

    def transition_split(self):
        if self.start.quantity == 1:
            create_serial_numbers = self.start.create_serial_numbers
        else:
            create_serial_numbers = False
        with Transaction().set_context(
                create_serial_numbers=create_serial_numbers):
            return super(SplitProduction, self).transition_split()
