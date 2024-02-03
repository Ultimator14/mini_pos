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
- The server can be started with `gunicorn --bind 0.0.0.0:80 run:app`
- Waiters can connect to the server with their smartphones via `http://<ip>/service`
- The kitchen can connect to the server with a desktop computer via `http://<ip>/bar`

## Requirements

- A desktop computer or tablet with large screen for the kitchen
- A smartphone for each cashier with a browser installed
- A device where the server can run on (can be the same as for the kitchen) with `>=python3.10` installed
- Some kind of network to connect everything

## Usage

### Install

Clone the repository:

```bash
git clone https://github.com/Ultimator14/mini_pos.git
cd mini_pos
```

Install dependencies:

```bash
poetry install
```

Enter the poetry virtual environment:

```bash
poetry shell
```

### Run

Development (Werkzeug server):

```bash
python run.py
```

Production (Gunicorn server):

```bash
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80    # allow binding to port 80 without root
gunicorn --bind 0.0.0.0:80 --workers=4 run:app      # run the app
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=1024  # reset sysctl config change
```

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
| ui/show_category_names| Show category names between products of different category in service     | `bool true/false`                                  |
| ui/fold_categories    | Fold categories by default in service                                     | `bool true/false`                                  |
| ui/timeout            | Timeout in seconds to mark orders yellow/red                              | `int timeout_warn, int timeout_crit`               |

### Categories

An additional space is added between adjacent products with different category in service. If `show_category_names` is enabled, the space is filled with the corresponding category name.

Categories 0-14 have a distinct color scheme

- Products in category 1-7 have a light colored background per default and become heavily colored upon selection. The category separators are not colored
- Products in category 8-14 have a white background per default and become light colored upon selection. The category separators are colored heavily
- All other products have a white background per default and are colored green upon selection. The category separators are not colored

Colors can be added or edited directly in [service_table.css](mini_pos/static/css/service_table.css)

### Tables

Table positions can be customized. Tables must have a start position `x,y`, a horizontal and vertical length `xlen, ylen` and a name.  
Overlapping tables are not supported and will produce a warning.  
Tables outside the grid are not supported and will produce an error.


## Pitfalls

It's not safe to alter configuration options and restarting the server without reloading the pages on the client side.  
Make sure, that waiters reload the page after a config change and server restart happened.

Example:

Removing, adding or swapping products in the configuration could cause a wrong product to be ordered when the server is restarted.  
Products are numbered by their position in the configuration file.
When a table is opened in service, the product numbers are fetched from the server.
When the server is restarted and the product numbers changed somehow, frontend and backend are not synced anymore.
This could cause wrong products in the next order.

Scenario:

- Waiter opens `/service/A1`, products are `Prod1` (1), `Prod2` (2), `Prod3` (3)
- Product `Prod1` is removed from server config
- Server is restarted
- Products in server are now `Prod2` (1), `Prod3` (2)
- Waiter orders `Prod2` identified by number 2
- Server receives number 2 and maps it to product `Prod3`


## Images

### Bar

![Bar](https://user-images.githubusercontent.com/30043959/216357579-82770021-f14c-482a-803e-2a987cd3657c.png)

### Service

![Service 1](https://user-images.githubusercontent.com/30043959/216357655-df288558-f601-43fe-b45d-9dd3e7e85db5.png)
![Service 2](https://user-images.githubusercontent.com/30043959/216357709-668a4354-eb63-42cb-9b32-4790a8375497.png)
![Service 3](https://user-images.githubusercontent.com/30043959/216357756-f21db042-17cc-40e4-bbd3-5419ee8bebaa.png)
![Service 4](https://user-images.githubusercontent.com/30043959/216357819-45f2a6fc-65fb-46f2-88f0-a92e139871ac.png)

## Analysis

The analysis script provides an overview about sold products, revenue as well as some more statistics.  
For the script to work, the dependencies from the analysis group must be installed. Afterwards the analysis can be started with the `analyze.py` script.
The results are saved as `analysis.pdf`.

Install analysis dependencies:

```bash
poetry install --with analysis
```

Enter the poetry virtual environment:
```bash
poetry shell
```

Start analysis:
```bash
python analyze.py
```

Note: When it's desired to show the plots in a window, uncomment the last line `plt.show()` in the `analyze.py` script.  
However the command `plot.show()` will probably not work. This is because PyQt5 is not included in the dependency list. Which again is because poetry is cross-platform but PyQt5 only supports some specific architectures. To still be able to show plots inside the poetry virtualenv, use `pip install pyqt5` (if there exists a wheel for your arch). Alternatively install PyQt5 on your system and use the `virtualenvs.options.system-site-packages` config option for poetry to allow the virtualenv to access it.

## Alternatives

Some (probably more mature) alternatives to this project are

- [Ordersprinter](https://www.ordersprinter.de/)
- [MoKaSys](https://www.mokasys.de/)
- [Orderjutsu](https://orderjutsu.org/)
