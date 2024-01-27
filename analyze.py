#!/usr/bin/python3.10

from mini_pos import create_app
from mini_pos.models import Order, db

app = create_app()

app.logger.info("Starting analysis...")
app.logger.info("")

with app.app_context():

    def get_completed_orders() -> list[Order]:
        return list(db.session.execute(db.select(Order).filter(Order.completed_at.isnot(None))).scalars())

    # Note: Only completed orders are handled in the following
    # because only they have a completed date

    # General information
    orders = Order.get_open_orders()
    completed_orders = get_completed_orders()
    total_product_count = sum(product.amount for order in completed_orders for product in order.products)
    total_revenue = round(
        sum(product.price * product.amount for order in completed_orders for product in order.products), 2
    )

    app.logger.info("General")
    app.logger.info("-------")
    app.logger.info("Active orders: %s", str(len(orders)))
    app.logger.info("Completed orders: %s", str(len(completed_orders)))
    app.logger.info("Sold units total: %s", total_product_count)
    app.logger.info("Total revenue: %s€", total_revenue)
    app.logger.info("")
    app.logger.info("")

    # Orders/Products sold, Orders by table, Orders by waiter
    products: dict[str, int] = {}
    tabledict: dict[str, list] = {}
    waiterdict: dict = {}

    for order in completed_orders:
        if order.table not in tabledict:
            tabledict[order.table] = [0, 0, 0]

        if order.waiter not in waiterdict:
            waiterdict[order.waiter] = [0, 0, 0]

        # Orders/Products sold
        for product in order.products:
            if product.name in products:
                products[product.name] += product.amount
            else:
                products[product.name] = product.amount

        product_count = sum(product.amount for product in order.products)
        product_price = sum(product.amount * product.price for product in order.products)

        # Orders by table
        tabledict[order.table][0] += 1  # order count
        tabledict[order.table][1] += product_count  # product count
        tabledict[order.table][2] += product_price  # product price

        # Orders by waiter
        waiterdict[order.waiter][0] += 1  # order count
        waiterdict[order.waiter][1] += product_count  # product count
        waiterdict[order.waiter][2] += product_price  # product price

    app.logger.info("Sold units")
    app.logger.info("----------")
    for product in sorted(products, key=products.get, reverse=True):
        app.logger.info("%s: %s", product, str(products[product]))
    app.logger.info("")
    app.logger.info("")

    app.logger.info("Products by table")
    app.logger.info("---------------")
    for table in sorted(tabledict, key=lambda x: tabledict[x][1], reverse=True):
        app.logger.info(
            "%s: %s (%s orders, %s€)", table, tabledict[table][1], tabledict[table][0], round(tabledict[table][2], 2)
        )
    app.logger.info("")
    app.logger.info("")

    app.logger.info("Products by waiter")
    app.logger.info("---------------")
    for waiter in sorted(waiterdict, key=lambda x: waiterdict[x][1], reverse=True):
        app.logger.info(
            "%s: %s (%s orders, %s€)",
            waiter,
            waiterdict[waiter][1],
            waiterdict[waiter][0],
            round(waiterdict[waiter][2], 2),
        )
    app.logger.info("")
    app.logger.info("")
