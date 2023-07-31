#!/usr/bin/python3.10

from mini_pos import create_app, db
from mini_pos.models import Order

app = create_app()

with app.app_context():
    def get_completed_orders() -> list[Order]:
        return list(db.session.execute(
            db.select(Order)
            .filter(Order.completed_at.isnot(None))
        ).scalars())

    orders = Order.get_open_orders()
    completed_orders = get_completed_orders()

    app.logger.info("----------------------------------------")
    app.logger.info("Starting analysis")
    app.logger.info("----------------------------------------")
    app.logger.info("Active orders: %s", str(len(orders)))
    app.logger.info("Completed orders: %s", str(len(completed_orders)))
    app.logger.info("----------------------------------------")


    products: dict[str, int] = {}

    for order in completed_orders:
        for product in order.products:
            if product.name in products:
                products[product.name] += product.amount
            else:
                products[product.name] = product.amount

    app.logger.info("Sold units")
    app.logger.info("----------")
    for product in sorted(products, key=products.get, reverse=True):
        app.logger.info("%s: %s", product, str(products[product]))
    app.logger.info("----------------------------------------")
