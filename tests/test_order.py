"""Test order flow"""

from mini_pos.models import Order


def test_service_post(app):
    # Setup
    client = app.test_client()

    data1 = {"nonce": "123456789"}

    for i in range(1, len(app.config["minipos"].products) + 1):
        data1[f"amount-{i}"] = "1"  # one for every product
        data1[f"comment-{i}"] = "Test"  # comment for every product

    data2 = {"nonce": "987654321", "amount-1": "1", "comment-1": ""}

    # Order products
    response = client.post("/service/A1", data=data1)
    assert response.status_code == 302  # assert redirect to service page

    response = client.post("/service/A2", data=data2)
    assert response.status_code == 302

    # Get order ids of new orders
    with app.app_context():
        open_orders = Order.get_open_orders_for_bar("default")

        assert len(open_orders) == 2

        order1 = open_orders[0]

        order2 = open_orders[1]
        order2_product = order2.products[0]

    # Complete order1 in bar
    data = {"order-completed": str(order1.id)}
    response = client.post("/bar/default", data=data)

    assert response.status_code == 302

    # Complete second order by completing product
    data = {"product-completed": str(order2_product.id), "order": str(order2.id)}
    response = client.post("/bar/default", data=data)

    assert response.status_code == 302

    # Check that both orders are completed
    with app.app_context():
        open_orders = Order.get_open_orders_for_bar("default")

    assert len(open_orders) == 0


if __name__ == "__main__":
    # run with python tests/test_order.py
    from mini_pos import create_app
    from mini_pos.settings import TestConfig

    app = create_app(TestConfig)
    test_service_post(app)
