# MiniPOS [WIP]

### Internals

- Don't submit order and product in bar


# MiniPOS 0.1.6

### Features

- Add pytest
- Add testing config and basic tests
- Use different exit codes

### Bugfixes

- Fix crash if table is placed outside the grid
- Fix inconsistent redirect behavior


# MiniPOS 0.1.5

### Features

- Detect all syntax/type errors or missing values in config file

### Internals

- Shrink config classes
- Update dependencies
- Use logging handler to count critical logs


# MiniPOS 0.1.4

### Features

- Add pylint for static code analysis

### Internals

- Use flask blueprints
- Improve code structure in package


# MiniPOS 0.1.3

### Internals

- Split logic in package into separate files
- Use application factory to create flask app
- Use flask for logging


# MiniPOS 0.1.2

### Features

- Use separate package
- Use poetry for dependency management
- Add ruff (linter), black (formatter), mypy (type checker)


# MiniPOS 0.1.1

### Features

- Add debug logging
- Catch wrong syntax in config file
- Don't crash if config file is missing entries

### Bugfixes

- Fix crash if table is placed outside the grid


# MiniPOS v0.1.0

### Features

- Use sqlite for data storage (breaking change, old data.pkl file is no longer supported)

### Removals

- admin page
- persistence config


# MiniPOS v0.0.2

### Features

- Add indication in bar if service is down
- Adjust grid size if table is placed outside the grid
- Catch duplicate table names
- Filter duplicate orders
- Use javascript fetch instead of php page reload

### UI

- Align columns in bar
- Improve popup window in service
- Use sans-serif font
- Use two lines for date in bar


# MiniPOS v0.0.1

Initial version
