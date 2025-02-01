#!/usr/bin/python3.10

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from mini_pos import create_app
from mini_pos.models import Order, db

app = create_app()

PDF_FILENAME = "analysis.pdf"
FIGSIZE = (20, 15)

app.logger.info("Starting analysis...")


def extract_data():
    """Create dataframes from databases. Note: only completed orders are handled"""
    app.logger.info("Extracting data...")
    with app.app_context():

        def get_completed_orders() -> list[Order]:
            return list(db.session.execute(db.select(Order).filter(Order.completed_at.isnot(None))).scalars())

        orders = get_completed_orders()

        if not orders:
            app.logger.error("No orders found. Terminating.")
            exit()


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
            for order in orders
        ]

        datalist_products = [
            [
                product.name,
                product.price,
                product.amount,
                order.date,
                order.completed_at - order.date,
                order.waiter,
                order.table,
                order.id,
            ]
            for order in orders
            for product in order.products
        ]

        ocolumns = ["date", "ordertime", "waiter", "table", "price", "numproducts"]
        pcolumns = ["name", "price", "amount", "date", "ordertime", "waiter", "table", "orderid"]

        df_orders = pd.DataFrame(datalist_orders, columns=ocolumns)
        df_products = pd.DataFrame(datalist_products, columns=pcolumns)

        df_orders["ordertime"] = df_orders["ordertime"].dt.round("1s").dt.seconds  # datetime to seconds

        return df_orders, df_products


def newplot():
    return plt.subplots(figsize=FIGSIZE)


def fig_general(dfo, dfp):
    orders_len = len(dfo)
    total_product_count = dfp["amount"].sum()
    total_revenue = (dfp["price"] * dfp["amount"]).sum()
    average_ordertime = round(dfo["ordertime"].mean())

    fig = plt.figure(figsize=FIGSIZE)
    fig.clf()

    general_info = f"""
    Abgeschlossene Bestellungen: {orders_len!s}
    Verkaufte Produkte: {total_product_count}
    Umsatz: {total_revenue}€
    Durchschnittliche Bearbeitungsdauer: {average_ordertime}s
    """
    # print(general_info)  # print some general info to console

    fig.text(0.5, 0.5, general_info, transform=fig.transFigure, size=24, ha="center")

    return fig


def fig_sold_products(_, dfp):
    """Create sold products figure"""
    fig, ax = newplot()

    df = dfp[["name", "amount"]].groupby("name").sum().sort_values("amount")

    df.plot.barh(title="Verkaufte Produkte", xlabel="Produkte", ylabel="Anzahl", legend=False, ax=ax)

    return fig


def fig_ordertime_hist(dfo, _):
    """Create ordertime histogram"""
    fig, ax = newplot()

    df = dfo[["ordertime"]]

    df.plot.hist(
        bins=20,
        title="Bearbeitungsdauer",
        xlabel="Bearbeitungsdauer",
        ylabel="#Bestellungen",
        legend=False,
        grid=False,
        ax=ax,
    )

    return fig


def fig_ordertime_by_time(dfo, _):
    """Create ordertime by time figure"""
    fig, ax = newplot()

    df = dfo.resample("5min", on="date").ordertime.agg(["mean", "max", "min"]).dropna()
    df.plot(title="Bearbeitungsdauer (5min)", xlabel="Zeit", ylabel="Bearbeitungsdauer (s)", ax=ax)
    ax.legend(["Average", "Max", "Min"])

    return fig


def fig_ordertime_by_product(_, dfp):
    """Create ordertime by product figure"""
    fig, ax = newplot()

    df = dfp[["name", "ordertime"]].groupby("name").mean().sort_values("ordertime").astype("timedelta64[s]")
    df.plot.barh(
        title="Bearbeitungsdauer pro Produkt", xlabel="Bearbeitungsdauer (s)", ylabel="Produkte", legend=False, ax=ax
    )

    return fig


def fig_table_by_waiter(dfo, _):
    """Create table by waiter figure"""
    fig, ax = newplot()

    df = (
        dfo[["waiter", "table"]]
        .groupby(["table", "waiter"])
        .value_counts()
        .reset_index()
        .set_index("table")
        .pivot_table(columns="waiter", index="table", fill_value=0)
        .astype(int)
    )
    df.plot.bar(y="count", title="Tisch/Bedienung", xlabel="Tisch", ylabel="Bestellungen", ax=ax)
    ax.legend(title="Bedienung")

    return fig


def fig_products_orders_by_table(_, dfp):
    """Create products/orders by table figure"""
    fig, ax = newplot()

    df = dfp[["table", "amount"]].groupby("table").sum().sort_values("amount", ascending=False)
    dfa = dfp[["table", "orderid"]].groupby("table").nunique()
    df = df.merge(dfa, on="table")

    df.plot.bar(title="Bestellungen pro Tisch", xlabel="Tisch", ylabel="Anzahl", ax=ax)
    ax.legend(["Produkte", "Bestellungen"])

    return fig


def fig_revenue_by_table(_, dfp):
    """Create revenue by table figure"""
    fig, ax = newplot()

    df = dfp[["price", "amount", "table"]].copy()
    df["fullprice"] = df.amount * df.price
    df = df[["table", "fullprice"]].groupby("table").sum().sort_values("fullprice", ascending=False)

    df.plot.bar(title="Umsatz pro Tisch", xlabel="Tisch", ylabel="Umsatz in €", legend=False, ax=ax)

    return fig


def fig_orders_by_waiter_by_time(dfo, _):
    """Create orders by waiter by time figure"""
    fig, ax = newplot()

    df = (
        dfo[["waiter", "date"]]
        .resample("5min", on="date")
        .waiter.value_counts()
        .reset_index()
        .set_index("date")
        .pivot_table(columns="waiter", index="date", fill_value=0)
        .astype(int)
    )["count"].cumsum()

    df.plot(title="Bedienungsbestellungen nach Zeit", xlabel="Zeit", ylabel="Bestellungen (5min)", ax=ax)
    ax.legend(title="Bedienung")

    return fig


def fig_products_orders_by_waiter(_, dfp):
    """Create products/orders by waiter figure"""
    fig, ax = newplot()

    df = dfp[["waiter", "amount"]].groupby("waiter").sum().sort_values("amount", ascending=False)
    dfa = dfp[["waiter", "orderid"]].groupby("waiter").nunique()
    df = df.merge(dfa, on="waiter")

    df.plot.bar(title="Bestellungen pro Bedienung", xlabel="Bedienung", ylabel="Anzahl", ax=ax)
    ax.legend(["Produkte", "Bestellungen"])

    return fig


def fig_revenue_by_waiter(_, dfp):
    """Create revenue by waiter figure"""
    fig, ax = newplot()

    df = dfp[["price", "amount", "waiter"]].copy()
    df["fullprice"] = df.amount * df.price
    df = df[["waiter", "fullprice"]].groupby("waiter").sum().sort_values("fullprice", ascending=False)
    df.plot.bar(title="Umsatz pro Bedienung", xlabel="Bedienung", ylabel="Umsatz in €", legend=False, ax=ax)

    return fig


def fig_products_by_time(_, dfp):
    """Create products by time figure"""
    fig, ax = newplot()

    df = (
        dfp[["name", "date", "amount"]]
        .groupby("name")
        .resample("10min", on="date", include_groups=False)
        .sum()
        .reset_index()
        .set_index("date")
        .pivot_table(columns="name", index="date", fill_value=0)
        .astype(int)
    )["amount"].cumsum()

    df.plot(title="Verkaufte Produkte nach Zeit (10min)", xlabel="Zeit", ylabel="Anzahl", ax=ax)

    last_point_order = df.iloc[-1].to_numpy().argsort()
    legend_handles, legend_labels = ax.get_legend_handles_labels()

    handles_ordered = list(np.array(legend_handles)[last_point_order][::-1])
    labels_ordered = list(np.array(legend_labels)[last_point_order][::-1])

    ax.legend(title="Produkt", handles=handles_ordered, labels=labels_ordered)

    return fig


def fig_revenue_by_time(dfo, _):
    """Create revenue by time figure"""
    fig, ax = newplot()

    df = dfo.resample("5min", on="date").price.sum().dropna().cumsum()
    df.plot(title="Umsatz nach Zeit", xlabel="Zeit", ylabel="Einnahmen (€)", ax=ax)

    return fig


def create_figs(dfo, dfp):
    app.logger.info("Creating figures...")
    dfs = (dfo, dfp)
    return [
        x(*dfs)
        for x in [
            fig_general,
            fig_sold_products,
            fig_ordertime_hist,
            fig_ordertime_by_time,
            fig_ordertime_by_product,
            fig_table_by_waiter,
            fig_products_orders_by_table,
            fig_revenue_by_table,
            #fig_orders_by_waiter_by_time,
            #fig_products_orders_by_waiter,
            #fig_revenue_by_waiter,
            fig_products_by_time,
            fig_revenue_by_time,
        ]
    ]


def save_figs(figs):
    """Save figures as pdf"""
    app.logger.info("Saving figures...")

    with PdfPages(PDF_FILENAME) as pp:
        for fig in figs:
            fig.savefig(pp, format="pdf", dpi=300)
    print(f"Analysis written to '{PDF_FILENAME}'")


# Do analysis and save figures as pdf
figs = create_figs(*extract_data())
save_figs(figs)

# Show figures in window (uncomment if pyqt5 is available)
# plt.show()
