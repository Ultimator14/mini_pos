"""Check for broken routes"""


def test_index(client):
    response = client.get("/")
    assert b"<title>Index</title>" in response.data


def test_bar(client):
    response = client.get("/bar")
    assert b"<title>Bar Selection</title>" in response.data


def test_service_login(client):
    response = client.get("/service/login")
    assert b"<title>Service Login</title>" in response.data


def test_service_trylogin(client):
    response = client.get("/service/trylogin")
    assert response.status_code == 302
    assert b"/service/login" in response.data


def test_service_trylogin2(client):
    client.set_cookie("waiter", "")
    response = client.get("/service/trylogin")
    assert response.status_code == 302
    assert b"/service" in response.data
    assert b"/service/login" not in response.data


def test_service(client):
    response = client.get("/service")
    assert b"<title>Service</title>" in response.data


def test_service2(client):
    response = client.get("/service/A1")
    assert b"<title>Service Table A1</title>" in response.data


def test_fetch_bar(client):
    response = client.get("/fetch/bar/default")
    assert b"server-status-up" in response.data


def test_fetch_service(client):
    response = client.get("/fetch/service")
    assert b"[]" in response.data
