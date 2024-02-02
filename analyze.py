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


def create_general_figs(dfo, dfp):
    app.logger.info("Creating general figures...")

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

    return [fig]


def create_order_figs(dfo):
    app.logger.info("Creating order figures...")

    # Revenue by 5min time interval
    df1 = dfo.resample("5min", on="date").price.sum().dropna().cumsum()

    # Order duration by time
    df2 = dfo.resample("5min", on="date").ordertime.agg(["mean", "max", "min"]).dropna()

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

    # Orders by waiter by time
    df4 = (
        dfo[["waiter", "date"]]
        .resample("5min", on="date")
        .waiter.value_counts()
        .reset_index()
        .set_index("date")
        .pivot_table(columns="waiter", index="date", fill_value=0)
        .astype(int)
    )["count"].cumsum()

    # Ordertime histogram
    df5 = dfo[["ordertime"]]

    # Prepare figures and axes
    fig1, ax1 = newplot()
    fig2, ax2 = newplot()
    fig3, ax3 = newplot()
    fig4, ax4 = newplot()
    fig5, ax5 = newplot()

    # Plot data
    df1.plot(title="Umsatz", xlabel="Zeit", ylabel="Einnahmen (€)", ax=ax1)

    df2.plot(title="Bearbeitungsdauer (5min)", xlabel="Zeit", ylabel="Bearbeitungsdauer (s)", ax=ax2)
    ax2.legend(["Average", "Max", "Min"])

    df3.plot.bar(y="count", title="Tisch/Bedienung", xlabel="Tisch", ylabel="Bestellungen", ax=ax3)
    ax3.legend(title="Bedienung")

    df4.plot(title="Bedienungsbestellungen nach Zeit", xlabel="Zeit", ylabel="Bestellungen (5min)", ax=ax4)
    ax4.legend(title="Bedienung")

    df5.plot.hist(
        bins=20,
        title="Bearbeitungsdauer",
        xlabel="Bearbeitungsdauer",
        ylabel="#Bestellungen",
        legend=False,
        grid=False,
        ax=ax5,
    )

    return [fig1, fig2, fig3, fig4, fig5]


def create_product_figs(dfp):
    app.logger.info("Creating product figures...")

    # Sold units
    df1 = dfp[["name", "amount"]].groupby("name").sum().sort_values("amount")

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

    # Products by time
    df6 = (
        dfp[["name", "date", "amount"]]
        .groupby("name")
        .resample("10min", on="date", include_groups=False)
        .sum()
        .reset_index()
        .set_index("date")
        .pivot_table(columns="name", index="date", fill_value=0)
        .astype(int)
    )["amount"].cumsum()

    # Product by time
    df7 = dfp[["name", "ordertime"]].groupby("name").mean().sort_values("ordertime").astype("timedelta64[s]")

    # Prepare figures and axes
    fig1, ax1 = newplot()
    fig2, ax2 = newplot()
    fig3, ax3 = newplot()
    fig4, ax4 = newplot()
    fig5, ax5 = newplot()
    fig6, ax6 = newplot()
    fig7, ax7 = newplot()

    # Plot data
    df1.plot.barh(title="Verkaufte Produkte", xlabel="Produkte", ylabel="Anzahl", legend=False, ax=ax1)

    df2.plot.bar(title="Bestellungen pro Tisch", xlabel="Tisch", ylabel="Anzahl", ax=ax2)
    ax2.legend(["Produkte", "Bestellungen"])

    df3.plot.bar(title="Umsatz pro Tisch", xlabel="Tisch", ylabel="Umsatz in €", legend=False, ax=ax3)

    df4.plot.bar(title="Bestellungen pro Bedienung", xlabel="Bedienung", ylabel="Anzahl", ax=ax4)
    ax4.legend(["Produkte", "Bestellungen"])

    df5.plot.bar(title="Umsatz pro Bedienung", xlabel="Bedienung", ylabel="Umsatz in €", legend=False, ax=ax5)

    df6.plot(title="Verkaufte Produkte nach Zeit (10min)", xlabel="Zeit", ylabel="Anzahl", ax=ax6)

    last_point_order = df6.iloc[-1].to_numpy().argsort()
    legend_handles, legend_labels = ax6.get_legend_handles_labels()

    handles_ordered = list(np.array(legend_handles)[last_point_order][::-1])
    labels_ordered = list(np.array(legend_labels)[last_point_order][::-1])

    ax6.legend(title="Produkt", handles=handles_ordered, labels=labels_ordered)

    df7.plot.barh(
        title="Bearbeitungsdauer pro Produkt", xlabel="Bearbeitungsdauer (s)", ylabel="Produkte", legend=False, ax=ax7
    )

    return [fig1, fig2, fig3, fig4, fig5, fig6, fig7]


def save_figs(figs):
    """Save figures as pdf"""
    app.logger.info("Saving figures...")

    with PdfPages(PDF_FILENAME) as pp:
        for fig in figs:
            fig.savefig(pp, format="pdf", dpi=300)
    print(f"Analysis written to '{PDF_FILENAME}'")


# Do analysis and save figures as pdf
dfo, dfp = extract_data()
figs = create_general_figs(dfo, dfp) + create_order_figs(dfo) + create_product_figs(dfp)
save_figs(figs)

# Show figures in window (uncomment if pyqt5 is available)
# plt.show()
