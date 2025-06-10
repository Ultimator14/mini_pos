# Roadmap

This file provides an overview about the planned (future) changes.

## Release 0.4.x

### Bons

- Add support for bon printers
- Add support for printing bons (python-escpos?)

Configuration:

- Bons should be added to the config the same way bars are, using a config option `bons` additionally to `bars`
- Bons should only give the bar name they are assigned so that there is always a bar but not necessarily a bon printer
- Add a config option for timeout how long in the past prints should attempt to print orders
- This option should be server side only, servers should stop offering orders that passed the timeout
- Add an option to change the desired print status i.e. if all new orders should be printed automatically without interaction in bar (status 1) or not (status 0)

Infrastructure:

- The main server should also host an API
- Printer clients (separate single-core python processes e.g. on Raspberry Pis) poll new orders from the API
- Each client must be assigned a bar with bon support (client config), so that they can naturally integrate with bars

Database:

- Printers can use a separate database field `printed` to mark orders as printed
- The field should be an integer indicating how often the product was printed

UI:

- Add a field to the bar indicating the last poll of the printer
- Add a button to each order in bar to trigger a print (or add the initial amount/10 seconds to the timeout field)
- Also add the option to cancel a print
- This field should also display how often something was printed already

Important:

This is prone to race conditions if multiple bars display the same products and trigger a print at the same time.
However that situation was also prone to race conditions before regarding marking orders as completed.
Add a warning if such a configuration is found.

## Release 0.5.x

### Sold out products

- Add admin UI to disable/enable products on the fly
- Products should be displayed ~~strikethrough~~ in service
- Implement Quota management. Set a limit of products. Once the limit is reached, the product is automatically marked as sold out. Quota should be controlled via admin ui

## Release 0.6.x

### PWA support

- Convert the client side to PWA
- Rework bar and service logic
- Rework fetching logic, change so that fetching does always only fetch data and not the whole html page -> layouting should happen on the client
- Fetch ALL data using javascript
- Implement an API on the server side handling all request with a json output
- Add popup in service if server is down. Prevent clicks on any button

## Release 0.7.x

### Statistics

- Add live statistics endpoint accessible via website
- Different statistics should be accessible via e.g. /statistics/by-table
- Statistics should be live updated for users to have a competitive experience

## Unscheduled

- Reimplement reloading config file on the fly via admin UI (workers have to poll changes, maybe with a database entry holding the time of the latest change and a global variable per worker - if the database time is newer than the worker time, reload config), client-side polling of potential config changes via javascript e.g. changed table order
- Reccommend products to order (same as last time button) in service, maybe also display in bar to optimize speed
- Add a "offline" feature i.e. a minified version of the software with less functionality that basically only hosts a webserver with the product list and the ability for waiters to compute prices.
  It should be enough to use only one table and  disable ordering but instead use a js rewrite to the same page in service
  However it might be a good idea to use a completely separate server for this which only uses the config, route and static files to avoid installing unneeded dependencies and running unneeded endpoints.
