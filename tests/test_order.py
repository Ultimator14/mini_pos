"""Test order flow"""

from mini_pos.models import Order

BAR_FOOD = "Küche"
BAR_DRINKS = "Getränke"
BAR_DEFAULT = "default"

def test_order_completion(app):
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
        open_orders = Order.get_open_orders_for_bar(BAR_DEFAULT)

        assert len(open_orders) == 2

        order1, order2 = open_orders

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
        assert len(Order.get_open_orders_for_bar(BAR_DEFAULT)) == 0


def test_bars(app):
    # Setup
    client = app.test_client()

    data1 = {"nonce": "123123123", "amount-5": "2", "comment-5": "", "amount-6": "2", "comment-6": ""}  # only drinks
    data2 = {
        "nonce": "456456456",
        "amount-31": "2",
        "comment-31": "Test",
        "amount-32": "4",
        "comment-32": "Mycomment",
    }  # only food
    data3 = {"nonce": "789789789", "amount-8": "2", "comment-8": "", "amount-31": "7", "comment-31": "Test"}  # both

    response = client.post("/service/A3", data=data1)
    assert response.status_code == 302

    response = client.post("/service/A4", data=data2)
    assert response.status_code == 302

    response = client.post("/service/A5", data=data3)
    assert response.status_code == 302

    # Get order ids of new orders
    with app.app_context():
        open_orders = Order.get_open_orders_for_bar(BAR_DEFAULT)
        assert len(open_orders) == 3
        order1, order2, order3 = open_orders

        open_orders_bar = Order.get_open_orders_for_bar(BAR_DRINKS)
        assert open_orders_bar == [order1, order3]

        open_orders_kitchen = Order.get_open_orders_for_bar(BAR_FOOD)
        assert open_orders_kitchen == [order2, order3]

        order3_product1, order3_product2 = order3.products

    # Check that both orders are completed and that each bar displays the correct order
    with app.app_context():
        assert len(Order.get_open_orders_for_bar(BAR_DRINKS)) == 2
        assert len(Order.get_partially_completed_order_for_bar(BAR_DRINKS)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DRINKS)) == 0

        assert len(Order.get_open_orders_for_bar(BAR_FOOD)) == 2
        assert len(Order.get_partially_completed_order_for_bar(BAR_FOOD)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_FOOD)) == 0

        assert len(Order.get_open_orders_for_bar(BAR_DEFAULT)) == 3
        assert len(Order.get_partially_completed_order_for_bar(BAR_DEFAULT)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DEFAULT)) == 0

    # Complete first order from bar Bar
    data = {"order-completed": str(order1.id)}
    response = client.post(f"/bar/{BAR_DRINKS}", data=data)

    # Check that order is completed correctly
    with app.app_context():
        assert len(Order.get_open_orders_for_bar(BAR_DRINKS)) == 1
        assert len(Order.get_partially_completed_order_for_bar(BAR_DRINKS)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DRINKS)) == 1

        assert len(Order.get_open_orders_for_bar(BAR_FOOD)) == 2
        assert len(Order.get_partially_completed_order_for_bar(BAR_FOOD)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_FOOD)) == 0

        assert len(Order.get_open_orders_for_bar(BAR_DEFAULT)) == 2
        assert len(Order.get_partially_completed_order_for_bar(BAR_DEFAULT)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DEFAULT)) == 1

    # Complete second order from bar Küche
    data = {"order-completed": str(order2.id)}
    response = client.post(f"/bar/{BAR_FOOD}", data=data)

    # Check that order is completed correctly
    with app.app_context():
        assert len(Order.get_open_orders_for_bar(BAR_DRINKS)) == 1
        assert len(Order.get_partially_completed_order_for_bar(BAR_DRINKS)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DRINKS)) == 1

        assert len(Order.get_open_orders_for_bar(BAR_FOOD)) == 1
        assert len(Order.get_partially_completed_order_for_bar(BAR_FOOD)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_FOOD)) == 1

        assert len(Order.get_open_orders_for_bar(BAR_DEFAULT)) == 1
        assert len(Order.get_partially_completed_order_for_bar(BAR_DEFAULT)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DEFAULT)) == 2

    # Partially complete third order from bar Bar
    data = {"product-completed": str(order3_product1.id), "order": str(order3.id)}
    response = client.post(f"/bar/{BAR_DRINKS}", data=data)

    # Check that order is partially completed correctly
    with app.app_context():
        assert len(Order.get_open_orders_for_bar(BAR_DRINKS)) == 0
        assert len(Order.get_partially_completed_order_for_bar(BAR_DRINKS)) == 1
        assert len(Order.get_last_completed_orders_for_bar(BAR_DRINKS)) == 1

        assert len(Order.get_open_orders_for_bar(BAR_FOOD)) == 1
        assert len(Order.get_partially_completed_order_for_bar(BAR_FOOD)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_FOOD)) == 1

        assert len(Order.get_open_orders_for_bar(BAR_DEFAULT)) == 1
        assert len(Order.get_partially_completed_order_for_bar(BAR_DEFAULT)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DEFAULT)) == 2

        print(order3.products)

    # Completely complete third order from bar Küche
    data = {"product-completed": str(order3_product2.id), "order": str(order3.id)}
    response = client.post(f"/bar/{BAR_FOOD}", data=data)

    # Check that order is completed correctly
    with app.app_context():
        assert len(Order.get_open_orders_for_bar(BAR_DRINKS)) == 0
        assert len(Order.get_partially_completed_order_for_bar(BAR_DRINKS)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DRINKS)) == 2

        assert len(Order.get_open_orders_for_bar(BAR_FOOD)) == 0
        assert len(Order.get_partially_completed_order_for_bar(BAR_FOOD)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_FOOD)) == 2

        assert len(Order.get_open_orders_for_bar(BAR_DEFAULT)) == 0
        assert len(Order.get_partially_completed_order_for_bar(BAR_DEFAULT)) == 0
        assert len(Order.get_last_completed_orders_for_bar(BAR_DEFAULT)) == 3


if __name__ == "__main__":
    # run with python tests/test_order.py
    from mini_pos import create_app
    from mini_pos.settings import TestConfig

    app = create_app(TestConfig)
    test_order_completion(app)
    test_bars(app)
