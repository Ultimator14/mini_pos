#!/usr/bin/python3.10

import app
from app import db

with app.app.app_context():
    def get_completed_orders() -> list[app.Order]:
        return list(db.session.execute(
            db.select(app.Order)
            .filter(app.Order.completed_at != None)  # this must be != and not 'is not'
        ).scalars())

    orders = app.get_open_orders()
    completed_orders = get_completed_orders()

    app.log_info("----------------------------------------")
    app.log_info("Starting analysis")
    app.log_info("----------------------------------------")
    app.log_info(f"Active orders: {str(len(orders))}")
    app.log_info(f"Completed orders: {str(len(completed_orders))}")
    app.log_info("----------------------------------------")


    products: dict[str, int] = {}

    for order in completed_orders:
        for product in order.products:
            if product.name in products:
                products[product.name] += product.amount
            else:
                products[product.name] = product.amount

    app.log_info("Sold units")
    app.log_info("----------")
    for product in sorted(products, key=products.get, reverse=True):
        app.log_info(f"{product}: {str(products[product])}")
    app.log_info("----------------------------------------")
