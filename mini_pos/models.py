from __future__ import annotations  # required for type hinting of classes in itself

import os.path
from datetime import datetime, timedelta

from flask import current_app as app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    nonce = db.Column(db.Integer)
    waiter = db.Column(db.String)
    table = db.Column(db.String)
    date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    products = db.relationship("Product", back_populates="order")

    @classmethod
    def create(cls, waiter: str, table: str, nonce: int) -> Order:
        return cls(waiter=waiter, table=table, nonce=nonce, date=datetime.now(), completed_at=None)

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
        if timediff > timedelta(seconds=app.config["minipos"].ui.bar.timeout_crit):
            return "timeout_crit"
        if timediff > timedelta(seconds=app.config["minipos"].ui.bar.timeout_warn):
            return "timeout_warn"
        return "timeout_ok"

    @property
    def completed_timestamp(self) -> str:
        if self.completed_at is None:
            app.logger.warning("completed_at for order %s called but order is not completed", self.id)
            return " "

        return self.completed_at.strftime("%Y-%m-%d %H:%M:%S")

    def complete(self) -> None:
        for product in self.products:
            product.complete()

        self.completed_at = datetime.now()

        db.session.commit()

        app.logger.info("Completed order %s", self.id)

    def products_for_bar(self, bar: str) -> list[Product]:
        return [p for p in self.products if p.category in app.config["minipos"].bars.get(bar, [])]

    def complete_for_bar(self, bar: str) -> None:
        for product in self.products_for_bar(bar):
            product.complete()

        if not all(product.completed for product in self.products):
            db.session.commit()

            app.logger.info("Partially completed order %s for bar %s", self.id, bar)
        else:
            self.completed_at = datetime.now()
            db.session.commit()

            app.logger.info("Completed order %s", self.id)

    @staticmethod
    def get_open_orders_for_bar(bar: str) -> list[Order]:
        categories = app.config["minipos"].bars[bar]
        return list(
            db.session.execute(
                db.select(Order)
                .filter_by(completed_at=None)
                .join(Order.products)
                .filter(
                    Product.category.in_(categories),
                    Product.completed.is_(False)
                )
                .group_by(Order)
            ).scalars()
        )

    @staticmethod
    def get_partially_completed_order_for_bar(bar: str) -> list[Order]:
        categories = app.config["minipos"].bars[bar]
        return list(
            db.session.execute(
                db.select(Order)
                .join(Order.products)
                .filter(
                    Product.category.in_(categories),
                    Product.completed.isnot(False)
                )
                .group_by(Order)
            ).scalars()
        )

    @staticmethod
    def get_last_completed_orders_for_bar(bar: str) -> list[Order]:
        categories = app.config["minipos"].bars[bar]
        return list(
            db.session.execute(
                db.select(Order)
                .filter(Order.completed_at.isnot(None))
                .join(Order.products)
                .filter(Product.category.in_(categories))
                .group_by(Order)
                .order_by(Order.completed_at.desc())
                .limit(app.config["minipos"].ui.bar.show_completed)
            ).scalars()
        )

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


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey(Order.id))
    name = db.Column(db.String)
    price = db.Column(db.Float)
    category = db.Column(db.String)
    amount = db.Column(db.Integer)
    comment = db.Column(db.String)
    completed = db.Column(db.Boolean)

    order = db.relationship("Order", back_populates="products")

    @classmethod
    def create(cls, order_id: int, name: str, price: float, category: str, amount: int, comment="") -> Product:
        return cls(
            order_id=order_id,
            name=name,
            price=price,
            category=category,
            amount=amount,
            comment=comment,
            completed=False,
        )

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


def init_db(app):
    db.init_app(app)

    if not os.path.isfile(f"instance/{app.config['DATABASE_FILE']}"):
        app.logger.info("No database file found. Creating database.")
        db.create_all()
