#!/usr/bin/python3.10

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from mini_pos import create_app
from mini_pos.models import Order, db

app = create_app()

PDF_FILENAME = "analysis.pdf"

app.logger.info("Starting analysis...")


def extract_data():
    """Create dataframes from databases. Note: only completed orders are handled"""
    app.logger.info("Extracting data...")
    with app.app_context():

        def get_completed_orders() -> list[Order]:
            return list(db.session.execute(db.select(Order).filter(Order.completed_at.isnot(None))).scalars())

        orders = Order.get_open_orders()
        completed_orders = get_completed_orders()

        # General information
        orders_len = len(orders)
        completed_orders_len = len(completed_orders)
        total_product_count = sum(product.amount for order in completed_orders for product in order.products)
        total_revenue = round(
            sum(product.price * product.amount for order in completed_orders for product in order.products), 2
        )
        info = (orders_len, completed_orders_len, total_product_count, total_revenue)

        # Dataframes
        datalist_orders = [
            [
                order.date,
                order.completed_at - order.date,
                order.waiter,
                order.table,
                sum(p.price * p.amount for p in order.products),
                len(order.products),
            ]
            for order in completed_orders
        ]

        datalist_products = [
            [product.name, product.price, product.amount, order.date, order.waiter, order.table, order.id]
            for order in completed_orders
            for product in order.products
        ]

        ocolumns = ["date", "ordertime", "waiter", "table", "price", "numproducts"]
        pcolumns = ["name", "price", "amount", "date", "waiter", "table", "orderid"]

        df_orders = pd.DataFrame(datalist_orders, columns=ocolumns)
        df_products = pd.DataFrame(datalist_products, columns=pcolumns)

        df_orders["ordertime"] = df_orders["ordertime"].dt.round("1s").dt.seconds  # datetime to seconds

        return info, df_orders, df_products


def create_general_figs(general):
    app.logger.info("Creating general figures...")
    orders_len, completed_orders_len, total_product_count, total_revenue = general

    fig = plt.figure()
    fig.clf()

    general_info = f"""
    Offene Bestellungen: {orders_len!s}
    Abgeschlossene Bestellungen: {completed_orders_len!s}
    Verkaufte Produkte: {total_product_count}
    Umsatz: {total_revenue}€
    """
    # print(general_info)  # print some general info to console

    fig.text(0.5, 0.5, general_info, transform=fig.transFigure, size=24, ha="center")

    return [fig]


def create_order_figs(dfo):
    app.logger.info("Creating order figures...")

    # Revenue by 5min time interval
    df1 = dfo.resample("5min", on="date").price.sum().dropna()

    # Order duration by time
    df2_ot = dfo.resample("5min", on="date").ordertime
    df2 = df2_ot.mean().dropna()
    df2a = df2_ot.max().dropna()
    df2b = df2_ot.min().dropna()

    # Table by waiter
    df3 = (
        dfo[["waiter", "table"]]
        .groupby(["table", "waiter"])
        .value_counts()
        .reset_index()
        .set_index("table")
        .pivot_table(columns="waiter", index="table", fill_value=0)
        .astype(int)
    )

    # Prepare figures and axes
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig3, ax3 = plt.subplots()

    # Plot data
    df1.plot(title="Umsatz", xlabel="Zeit", ylabel="Einnahmen (€)", ax=ax1)

    df2.plot(title="Bearbeitungsdauer (5min)", xlabel="Zeit", ylabel="Bearbeitungsdauer (s)", ax=ax2)
    df2a.plot(ax=ax2)
    df2b.plot(ax=ax2)

    df3.plot.bar(y="count", title="Tisch/Bedienung", xlabel="Tisch", ylabel="Bestellungen", ax=ax3)
    ax3.legend(title="Bedienung")

    return [fig1, fig2, fig3]


def create_product_figs(dfp):
    app.logger.info("Creating product figures...")

    # Sold units
    df1 = dfp[["name", "amount"]].groupby("name").sum().sort_values("amount", ascending=False)

    # Products by table, orders by table
    df2 = dfp[["table", "amount"]].groupby("table").sum().sort_values("amount", ascending=False)
    df2a = dfp[["table", "orderid"]].groupby("table").nunique()
    df2 = df2.merge(df2a, on="table")

    # Revenue by table
    df3 = dfp[["price", "amount", "table"]].copy()
    df3["fullprice"] = df3.amount * df3.price
    df3 = df3[["table", "fullprice"]].groupby("table").sum().sort_values("fullprice", ascending=False)

    # Products by waiter, orders by waiter
    df4 = dfp[["waiter", "amount"]].groupby("waiter").sum().sort_values("amount", ascending=False)
    df4a = dfp[["waiter", "orderid"]].groupby("waiter").nunique()
    df4 = df4.merge(df4a, on="waiter")

    # Revenue by waiter
    df5 = dfp[["price", "amount", "waiter"]].copy()
    df5["fullprice"] = df5.amount * df5.price
    df5 = df5[["waiter", "fullprice"]].groupby("waiter").sum().sort_values("fullprice", ascending=False)

    # Prepare figures and axes
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    fig3, ax3 = plt.subplots()
    fig4, ax4 = plt.subplots()
    fig5, ax5 = plt.subplots()

    # Plot data
    df1.plot.bar(title="Verkaufte Produkte", xlabel="Produkte", ylabel="Anzahl", legend=False, ax=ax1)

    df2.plot.bar(title="Bestellungen pro Tisch", xlabel="Tisch", ylabel="Anzahl", ax=ax2)
    ax2.legend(["Produkte", "Bestellungen"])

    df3.plot.bar(title="Umsatz pro Tisch", xlabel="Tisch", ylabel="Umsatz in €", legend=False, ax=ax3)

    df4.plot.bar(title="Bestellungen pro Bedienung", xlabel="Bedienung", ylabel="Anzahl", ax=ax4)
    ax4.legend(["Produkte", "Bestellungen"])

    df5.plot.bar(title="Umsatz pro Bedienung", xlabel="Bedienung", ylabel="Umsatz in €", legend=False, ax=ax5)

    return [fig1, fig2, fig3, fig4, fig5]


def save_figs(figs):
    """Save figures as pdf"""
    app.logger.info("Saving figures...")

    with PdfPages(PDF_FILENAME) as pp:
        for fig in figs:
            fig.savefig(pp, format="pdf", dpi=300)
    print(f"Analysis written to '{PDF_FILENAME}'")


# Do analysis and save figures as pdf
info, dfo, dfp = extract_data()
figs = create_general_figs(info) + create_order_figs(dfo) + create_product_figs(dfp)
save_figs(figs)

# Show figures in window (uncomment if pyqt5 is available)
# plt.show()
