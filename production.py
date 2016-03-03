# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['Production', 'SplitProduction']
__metaclass__ = PoolMeta


class Production:
    __name__ = 'production'

    def _split_inputs_outputs(self, factor):
        pool = Pool()
        Lot = pool.get('stock.lot')
        super(Production, self)._split_inputs_outputs(factor)
        for output in self.outputs:
            if not output.product.serial_number:
                continue
            if output.quantity != 1.0 or output.lot:
                continue
            if hasattr(output, 'get_production_output_lot'):
                lot = output.get_production_output_lot()
                lot.save()
            else:
                lot = Lot(product=output.product)
                lot.save()
            if lot:
                output.lot = lot
                output.save()


class SplitProduction:
    'Split Production'
    __name__ = 'production.split'

    def default_start(self, fields):
        pool = Pool()
        Production = pool.get('production')
        default = super(SplitProduction, self).default_start(fields)
        production = Production(Transaction().context['active_id'])
        if production.product and production.product.serial_number:
            default['quantity'] = 1.0
        return default
