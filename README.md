# Mini POS

## General

This is a simple POS system built to simplify the act of serving food/drinks.  

### Traditional service

The usual procedure for this would be that a waiter

- Walks around
- Takes an order
- Walks to the kitchen
- Passes the order
- Waits while it's prepared
- Takes the food/drinks
- Walks to the client
- Delivers the food/drinks
- Cashes up

### Improved service

Using this system, the ordering procedure would be

A waiter

- Walks around
- Takes an order with his smartphone
- Cashes up

The order is automatically received in the kitchen

Another waiter

- Takes food/drinks
- Walks to the client
- Delivers the food/drinks

In contrast to the traditional service, the delay between ordering and passing the order the the kitchen as well as unnecessary waiting has been eliminated completely.

## Setup

- The software does not require an internet connection an can be run on e.g. a raspberry pi
- Both kitchen and waiter need have access to the server via network (e.g. by using a hotspot or a connecting everything to a router)
- The server can be started with `gunicorn --bind 0.0.0.0:80 app:app`
- Waiters can connect to the server with their smartphones via `http://<ip>/service`
- The kitchen can connect to the server with a desktop computer via `http://<ip>/bar`

### Requirements

- `>=python3.10`
- A desktop computer or tablet with large screen for the kitchen
- A smartphone for each cashier
- A device where the server can run on (can be the same as for the kitchen)
- Some kind of network to connect everything

### Configuration

Configuration is done in the `config.json` file. The file is mandatory. The software does not start without it.  
Some configuration options are

| Config option         | Description                                                               | Format                                        |
|-----------------------|:-------------------------------------------------------------------------:|----------------------------------------------:|
| product/available     | List of available products                                                | `List[str Name, float price, int category]`   |
| product/categories    | Category names, no effect yet                                             | `List[int category, str name]`                |
| table                 | X/Y values for tables                                                     | `str x_values, str y_values`                  |
| ui/auto_close         | Automatically complete an order when all products are marked as completed | `bool true/false`                             |
| ui/show_completed     | Show the last n completed orders in /bar                                  | `int n`                                       |
| ui/timeout            | Timeout in seconds to mark orders yellow/red                              | `int timeout_warn, int timeout_crit`          |
| persistence           | Persist data between invocations (stored in `data.pkl` file)              | `bool true/false`                             |
