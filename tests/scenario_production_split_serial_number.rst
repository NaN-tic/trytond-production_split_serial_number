=======================================
Production Split Serial Number Scenario
=======================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.tests.tools import activate_modules, set_user
    >>> from trytond.modules.party_company.tests.test_party_company import (
    ...     set_company)
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()
    >>> yesterday = today - relativedelta(days=1)


Install production_split_serial_number Module::

    >>> config = activate_modules('production_split_serial_number')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Get default sequence::

    >>> Configuration = Model.get('product.configuration')
    >>> configuration = Configuration(1)
    >>> sequence = configuration.default_lot_sequence

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.producible = True
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal(30)
    >>> template.serial_number = True
    >>> template.save()
    >>> product.template = template
    >>> product.cost_price = Decimal(20)
    >>> product.save()

Create Components::

    >>> component1 = Product()
    >>> template1 = ProductTemplate()
    >>> template1.name = 'component 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal(5)
    >>> template1.save()
    >>> component1.template = template1
    >>> component1.cost_price = Decimal(1)
    >>> component1.save()

    >>> meter, = ProductUom.find([('name', '=', 'Meter')])
    >>> centimeter, = ProductUom.find([('name', '=', 'centimeter')])
    >>> component2 = Product()
    >>> template2 = ProductTemplate()
    >>> template2.name = 'component 2'
    >>> template2.default_uom = meter
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal(7)
    >>> template2.save()
    >>> component2.template = template2
    >>> component2.cost_price = Decimal(5)
    >>> component2.save()

Create Bill of Material::

    >>> BOM = Model.get('production.bom')
    >>> BOMInput = Model.get('production.bom.input')
    >>> BOMOutput = Model.get('production.bom.output')
    >>> bom = BOM(name='product')
    >>> input1 = BOMInput()
    >>> bom.inputs.append(input1)
    >>> input1.product = component1
    >>> input1.quantity = 5
    >>> input2 = BOMInput()
    >>> bom.inputs.append(input2)
    >>> input2.product = component2
    >>> input2.quantity = 150
    >>> input2.uom = centimeter
    >>> output = BOMOutput()
    >>> bom.outputs.append(output)
    >>> output.product = product
    >>> output.quantity = 1
    >>> bom.save()

    >>> ProductBom = Model.get('product.product-production.bom')
    >>> product.boms.append(ProductBom(bom=bom))
    >>> product.save()

Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([
    ...         ('code', '=', 'STO'),
    ...         ])
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory_line1 = InventoryLine()
    >>> inventory.lines.append(inventory_line1)
    >>> inventory_line1.product = component1
    >>> inventory_line1.quantity = 200
    >>> inventory_line2 = InventoryLine()
    >>> inventory.lines.append(inventory_line2)
    >>> inventory_line2.product = component2
    >>> inventory_line2.quantity = 60
    >>> inventory.save()
    >>> Inventory.confirm([inventory.id], config.context)
    >>> inventory.state
    'done'

Make a production::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.product = product
    >>> production.bom = bom
    >>> production.quantity = 4
    >>> production.save()
    >>> split_production = Wizard('production.split', [production])
    >>> split_production.form.quantity
    1.0
    >>> split_production.form.count = 2
    >>> split_production.execute('split')
    >>> productions = Production.find([])
    >>> len(productions)
    3
    >>> lots = [o.lot for p in productions for o in p.outputs if o.lot]
    >>> lot1, lot2  = sorted(lots, key=lambda a: int(a.number))
    >>> lot1.number
    '1'
    >>> lot2.number
    '2'
    >>> sequence.reload()
    >>> sequence.number_next == 3
    True

Split a production without creating serial numbers::

    >>> Production = Model.get('production')
    >>> production = Production()
    >>> production.product = product
    >>> production.bom = bom
    >>> production.quantity = 4
    >>> production.save()
    >>> split_production = Wizard('production.split', [production])
    >>> split_production.form.quantity
    1.0
    >>> split_production.form.count = 2
    >>> split_production.form.create_serial_numbers = False
    >>> split_production.execute('split')
    >>> productions = Production.find([('number', 'like', '2-%')])
    >>> len(productions)
    3
    >>> [o.lot for p in productions for o in p.outputs]
    [None, None, None]
