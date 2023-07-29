#!/usr/bin/python3.11

from __future__ import annotations  # required for type hinting of classes in itself

from datetime import datetime, timedelta

from . import Config, db
from .helpers import log_info, log_warn


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
        if timediff > timedelta(seconds=Config.UI.timeout_crit):
            return "timeout_crit"
        if timediff > timedelta(seconds=Config.UI.timeout_warn):
            return "timeout_warn"
        return "timeout_ok"

    @property
    def completed_timestamp(self) -> str:
        if self.completed_at is None:
            log_warn(f"completed_at for order {self.id!s} called but order is not completed")
            return " "

        return self.completed_at.strftime("%Y-%m-%d %H:%M:%S")

    def complete(self) -> None:
        products = db.session.execute(db.select(Product).filter_by(order_id=self.id, completed=False)).scalars()
        for product in products:
            product.complete()

        self.completed_at = datetime.now()

        db.session.commit()

        log_info(f"Completed order {self.id!s}")


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
            log_info(f"Completed product {self.id!s}")
