# Roadmap

This file provides an overview about the planned (future) changes.

## Release 0.3.x

### History Access

- Make order history of table available in service

## Release 0.4.x

### Sold out products

- Add admin UI to disable/enable products on the fly
- Products should be displayed ~~strikethrough~~ in service
- Implement Quota management. Set a limit of products. Once the limit is reached, the product is automatically marked as sold out. Quota should be controlled via admin ui

## Release 0.5.x

### Bons

- Add support for printing bons (python-escpos?)
- Make bar optional (in favor of bons)

## Unscheduled

- Add popup in service if server is down. Prevent clicks on any button
- Reimplement reloading config file on the fly via admin UI (workers have to poll changes, maybe with a database entry holding the time of the latest change and a global variable per worker - if the database time is newer than the worker time, reload config), client-side polling of potential config changes via javascript e.g. changed table order
- Convert the client side to PWA
- Rework fetching logic, change so that fetching does always only fetch data and not the whole html page -> layouting should happen on the client
- Restrict url access via param instead of many if-s in functions
