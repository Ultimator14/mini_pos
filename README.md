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

## Requirements

- `>=python3.9`
- A desktop computer or tablet with large screen for the kitchen
- A smartphone for each cashier
- A device where the server can run on (can be the same as for the kitchen)
- Some kind of network to connect everything

## Configuration

Configuration is done in the `config.json` file. The file is mandatory. The software does not start without it.  
Some configuration options are

| Config option         | Description                                                               | Format                                             |
|-----------------------|:-------------------------------------------------------------------------:|---------------------------------------------------:|
| product/available     | List of available products (name, price, category)                        | `List[str Name, float price, int category]`        |
| product/categories    | Category names                                                            | `List[int category, str name]`                     |
| table/size            | Size for the table grid in service                                        | `int x, int y`                                     |
| table/names           | Table positions, sizes and names                                          | `List[int x, int y, int xlen, int ylen, str name]` |
| ui/auto_close         | Automatically complete an order when all products are marked as completed | `bool true/false`                                  |
| ui/show_completed     | Show the last n completed orders in /bar                                  | `int n`                                            |
| ui/show_category_names|Show category names between products of different category in service      | `bool true/false`                                  |
| ui/split_categories   | Make a space between different categories in service (always true if `show_category_names` is set) | `bool true/false`         |
| ui/timeout            | Timeout in seconds to mark orders yellow/red                              | `int timeout_warn, int timeout_crit`               |
| persistence           | Persist data between invocations (stored in `data.pkl` file)              | `bool true/false`                                  |

### Categories

Categories only have an effect if either `show_category_names` or `split_categories` are enabled. An additional space is then added between adjacent products with different category in service.

Categories 0-14 have a distinct color scheme

- Products in category 1-7 have a light colored background per default and become heavily colored upon selection. The category separators are not colored
- Products in category 8-14 have a white background per default and become light colored upon selection. The category separators are colored heavily
- All other products have a white background per default and are colored green upon selection. The category separators are not colored

Colors can be added or edited directly in [service_table.css](static/css/service_table.css)

### Tables

Table positions can be customized. Tables must have a start position `x,y`, a horizontal and vertical length `xlen, ylen` and a name.  
Overlapping tables are not supported and will produce a warning.  
Tables outside the grid are not supported and will produce an error.

## Images

### Bar

![Bar](https://user-images.githubusercontent.com/30043959/216357579-82770021-f14c-482a-803e-2a987cd3657c.png)

### Service

![Service 1](https://user-images.githubusercontent.com/30043959/216357655-df288558-f601-43fe-b45d-9dd3e7e85db5.png)
![Service 2](https://user-images.githubusercontent.com/30043959/216357709-668a4354-eb63-42cb-9b32-4790a8375497.png)
![Service 3](https://user-images.githubusercontent.com/30043959/216357756-f21db042-17cc-40e4-bbd3-5419ee8bebaa.png)
![Service 4](https://user-images.githubusercontent.com/30043959/216357819-45f2a6fc-65fb-46f2-88f0-a92e139871ac.png)
