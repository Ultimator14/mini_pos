#!/usr/bin/python3.11

from . import db, Config
from .models import Product, Order

def get_open_orders() -> list[Order]:
    return list(db.session.execute(db.select(Order).filter_by(completed_at=None)).scalars())


def get_order_by_id(order_id: int) -> Order | None:
    return db.session.execute(db.select(Order).filter_by(id=order_id)).scalar_one_or_none()


def _get_open_orders_by_table(table: str) -> list[Order]:
    return list(db.session.execute(db.select(Order).filter_by(table=table, completed_at=None)).scalars())


def get_open_order_nonces() -> list[int]:
    return list(db.session.execute(db.select(Order.nonce).filter_by(completed_at=None)).scalars())


def get_active_tables() -> list[str]:
    return list(db.session.execute(db.select(Order.table).filter_by(completed_at=None).distinct()).scalars())


def get_last_completed_orders() -> list[Order]:
    return list(
        db.session.execute(
            db.select(Order)
            .filter(Order.completed_at != None)  # this must be != and not 'is not'
            .order_by(Order.completed_at.desc())
            .limit(Config.UI.show_completed)
        ).scalars()
    )


def get_product_by_id(product_id: int) -> Product | None:
    return db.session.execute(db.select(Product).filter_by(id=product_id)).scalar_one_or_none()


def get_open_products_by_order_id(order_id: int) -> list[Product]:
    return list(db.session.execute(db.select(Product).filter_by(completed=False, order_id=order_id)).scalars())


def get_open_product_lists_by_table(table: str) -> list[list[str]]:
    return [
        [
            f"{p.amount}x {p.name}" + (f" ({p.comment})" if p.comment else "")
            for p in get_open_products_by_order_id(o.id)
        ]
        for o in _get_open_orders_by_table(table)
    ]


