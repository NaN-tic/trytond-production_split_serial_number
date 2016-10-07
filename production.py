# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, Equal
from trytond.transaction import Transaction

__all__ = ['Production', 'SplitProductionStart', 'SplitProduction']


class Production:
    __metaclass__ = PoolMeta
    __name__ = 'production'

    def _split_moves(self, current_moves, new_production, product2qty,
            relation_field):
        pool = Pool()
        Lot = pool.get('stock.lot')
        super(Production, self)._split_moves(current_moves, new_production,
            product2qty, relation_field)
        if relation_field != 'production_output':
            return
        for output in new_production.outputs:
            if not output.product.serial_number:
                continue
            if not Transaction().context.get('create_serial_numbers', True):
                continue
            if output.quantity != 1.0 or output.lot:
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


class SplitProductionStart:
    __metaclass__ = PoolMeta
    __name__ = 'production.split.start'

    create_serial_numbers = fields.Boolean('Create Serial Numbers?',
        states={
            'invisible': ~Equal(Eval('quantity', 0), 1),
            },
        depends=['quantity'])

    @staticmethod
    def default_create_serial_numbers():
        return False


class SplitProduction:
    __metaclass__ = PoolMeta
    __name__ = 'production.split'

    def default_start(self, fields):
        pool = Pool()
        Production = pool.get('production')
        default = super(SplitProduction, self).default_start(fields)
        production = Production(Transaction().context['active_id'])
        if production.product and production.product.serial_number:
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
