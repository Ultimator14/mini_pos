# Roadmap

This file provides an overview about the planned (future) changes.

## Release 1.0.0

### Waiter login (breaking change for database)

- Waiter should be able to save a name
- The name should be displayed in the bar
- Orders should be attached to a waiter
- The name should be saved client side via webstorage or cookie

### Multiple bars (breaking change for config file)

- Support arbitrary many bars (e.g. food, drinks, cocktails, ...)
- Bars should be selectable on the main page
- Each bar can display multiple categories (as in config file)

### Sold out products

- Add admin UI to disable/enable products on the fly
- Products should be displayed ~~strikethrough~~ in service


## Release 1.1.0

### Order overview

- Add an additional step after finishing an order in service
- Waiters should be able to combine products from a completed order arbitrarily in case different people want to pay
- Products can be marked as payed
- After payment is complete, return to main service page
- This feature should be client side only
- The ordering process should already be fininshed and the order should already be displayed at the bar BEFORE waiters compute the subtotals
- Put this on a separate page, maybe controlled via config value

## Release 2.0.0

### Bons

- Add support for printing bons (python-escpos?)
- Make bar optional (in favor of bons)

## Unscheduled

- Add popup in service if server is down. Prevent clicks on any button
- Reimplement reloading config file on the fly via admin UI (workers have to poll changes, maybe with a database entry holding the time of the latest change and a global variable per worker - if the database time is newer than the worker time, reload config), client-side polling of potential config changes via javascript e.g. changed table order
- Add history tab (paginated or lazy load) to show all completed orders even if the number of shown completed orders is limited in bar, maybe include this in bar and add a unfold button
- Convert the client side to PWA
