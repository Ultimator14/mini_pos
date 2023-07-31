#!/usr/bin/python3.11

from __future__ import annotations  # required for type hinting of classes in itself

from datetime import datetime, timedelta

from flask import current_app as app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    nonce = db.Column(db.Integer)
    table = db.Column(db.String)
    date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    @classmethod
    def create(cls, table: str, nonce: int) -> Order:
        return cls(table=table, nonce=nonce, date=datetime.now(), completed_at=None)

    @property
    def products(self) -> list[Product]:
        return list(db.session.execute(db.select(Product).filter_by(order_id=self.id)).scalars())

    @property
    def active_since(self) -> str:
        timediff = datetime.now() - self.date
        if timediff > timedelta(minutes=60):
            return ">60min"

        seconds_aligned = timediff.seconds // 5 * 5  # align by 5 seconds (easy way to circumvent javascript timers)
        seconds = str(seconds_aligned % 60).rjust(2, "0")
        minutes = str(seconds_aligned // 60).rjust(2, "0")

        return f"{minutes}:{seconds}"

    @property
    def active_since_timeout_class(self) -> str:
        timediff = datetime.now() - self.date
        if timediff > timedelta(seconds=app.config["minipos"].ui.timeout_crit):
            return "timeout_crit"
        if timediff > timedelta(seconds=app.config["minipos"].ui.timeout_warn):
            return "timeout_warn"
        return "timeout_ok"

    @property
    def completed_timestamp(self) -> str:
        if self.completed_at is None:
            app.logger.warning("completed_at for order %s called but order is not completed", self.id)
            return " "

        return self.completed_at.strftime("%Y-%m-%d %H:%M:%S")

    def complete(self) -> None:
        products = db.session.execute(db.select(Product).filter_by(order_id=self.id, completed=False)).scalars()
        for product in products:
            product.complete()

        self.completed_at = datetime.now()

        db.session.commit()

        app.logger.info("Completed order %s", self.id)

    @staticmethod
    def get_open_orders() -> list[Order]:
        return list(db.session.execute(db.select(Order).filter_by(completed_at=None)).scalars())

    @staticmethod
    def get_order_by_id(order_id: int) -> Order | None:
        return db.session.execute(db.select(Order).filter_by(id=order_id)).scalar_one_or_none()

    @staticmethod
    def get_open_orders_by_table(table: str) -> list[Order]:
        return list(db.session.execute(db.select(Order).filter_by(table=table, completed_at=None)).scalars())

    @staticmethod
    def get_open_order_nonces() -> list[int]:
        return list(db.session.execute(db.select(Order.nonce).filter_by(completed_at=None)).scalars())

    @staticmethod
    def get_active_tables() -> list[str]:
        return list(db.session.execute(db.select(Order.table).filter_by(completed_at=None).distinct()).scalars())

    @staticmethod
    def get_last_completed_orders() -> list[Order]:
        return list(
            db.session.execute(
                db.select(Order)
                .filter(Order.completed_at.isnot(None))
                .order_by(Order.completed_at.desc())
                .limit(app.config["minipos"].ui.show_completed)
            ).scalars()
        )


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(Order.id))
    name = db.Column(db.String)
    price = db.Column(db.Float)
    amount = db.Column(db.Integer)
    comment = db.Column(db.String)
    completed = db.Column(db.Boolean)

    @classmethod
    def create(cls, order_id: int, name: str, price: float, amount: int, comment="") -> Product:
        return cls(order_id=order_id, name=name, price=price, amount=amount, comment=comment, completed=False)

    def complete(self) -> None:
        if not self.completed:
            self.completed = True
            db.session.commit()
            app.logger.info("Completed product %s", self.id)

    @staticmethod
    def get_product_by_id(product_id: int) -> Product | None:
        return db.session.execute(db.select(Product).filter_by(id=product_id)).scalar_one_or_none()

    @staticmethod
    def get_open_products_by_order_id(order_id: int) -> list[Product]:
        return list(db.session.execute(db.select(Product).filter_by(completed=False, order_id=order_id)).scalars())

    @staticmethod
    def get_open_product_lists_by_table(table: str) -> list[list[str]]:
        return [
            [
                f"{p.amount}x {p.name}" + (f" ({p.comment})" if p.comment else "")
                for p in Product.get_open_products_by_order_id(o.id)
            ]
            for o in Order.get_open_orders_by_table(table)
        ]
