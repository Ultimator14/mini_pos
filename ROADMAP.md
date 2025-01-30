# Roadmap

This file provides an overview about the planned (future) changes.

## Release 0.3.x

### History Access

- Make order history of table available in service

### Misc

- Underscore category names should be hidden (same as no category)

## Release 0.4.x

### Order overview

- Add an additional step after finishing an order in service
- Waiters should be able to combine products from a completed order arbitrarily in case different people want to pay
- Products can be marked as payed
- After payment is complete, return to main service page
- This feature should be client side only
- The ordering process should already be fininshed and the order should already be displayed at the bar BEFORE waiters compute the subtotals
- Put this on a separate page, maybe controlled via config value

## Release 0.5.x

### Sold out products

- Add admin UI to disable/enable products on the fly
- Products should be displayed ~~strikethrough~~ in service
- Implement Quota management. Set a limit of products. Once the limit is reached, the product is automatically marked as sold out. Quota should be controlled via admin ui

## Release 0.6.0

### Bons

- Add support for printing bons (python-escpos?)
- Make bar optional (in favor of bons)

## Unscheduled

- Add popup in service if server is down. Prevent clicks on any button
- Reimplement reloading config file on the fly via admin UI (workers have to poll changes, maybe with a database entry holding the time of the latest change and a global variable per worker - if the database time is newer than the worker time, reload config), client-side polling of potential config changes via javascript e.g. changed table order
- Convert the client side to PWA
- Rework fetching logic, change so that fetching does always only fetch data and not the whole html page -> layouting should happen on the client
