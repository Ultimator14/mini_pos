#!/usr/bin/python3.10

import app

app.log_info("----------------------------------------")
app.log_info("Starting analysis")
app.log_info("----------------------------------------")
app.log_info(f"Active orders: {str(len(app.orders))}")
app.log_info(f"Completed orders: {str(len(app.completed_orders))}")
app.log_info("----------------------------------------")


products = dict()

for order in app.completed_orders:
    for product in order.products:
        if product.name in products.keys():
            products[product.name] += product.amount
        else:
            products[product.name] = product.amount


app.log_info("Sold units")
app.log_info("----------")
for product in sorted(products, key=products.get, reverse=True):
    app.log_info(f"{product}: {str(products[product])}")
app.log_info("----------------------------------------")
