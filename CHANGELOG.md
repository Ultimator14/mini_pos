# MiniPOS Unreleased


# MiniPOS 0.3.5

### Features

- Add order overview in service for waiters to compute subtotals
- Display per-product price in service overview

### Internals

- Adapt tests to new feature


# MiniPOS 0.3.4

### Bugfixes

- Disallow negative values as product amount
- Fix crash in analysis if no orders are found
- Fix category folding

### Internals

- Conform to HTML standard


# MiniPOS 0.3.3

### Internals

- Deduplicate css
- Use template inheritance
- Rename variables to better fit their purpose


# MiniPOS 0.3.2

### Bugfixes

- Fix status bar buttons looking different

### Internals

- Reformat css
- Always use `url_for` instead of hardcoded paths


# MiniPOS 0.3.1

### Features

- Add option to show full history in bar
- Improve tests


# MiniPOS 0.3.0

### Features

- Support multiple bars (breaking change, database now contains category)
- New config structure (breaking change for config file)
- Improve tests

## Internals

- Create database relationship between Order and Product


# MiniPOS 0.2.4

### Features

- Improve config checking


# MiniPOS 0.2.3

### Features

- Improve analysis script

### Internals

- Update dependencies


# MiniPOS 0.2.2

### Features

- Improve analysis script


# MiniPOS 0.2.1

### Bugfixes

- Fix arrow orientation on window resize in service
- Fix display errors on window resize in service


# MiniPOS 0.2.0

### Features

- Add waiter names (breaking change, database now contains column for waiter name)
- Make categories foldable in service

### Removals

- `split_categories` config option

### Bugfixes

- Use correct path for `service_table_submit` form

### Internals

- Update dependencies


# MiniPOS 0.1.7

### Features

- Add Dockerfile

### Bugfixes

- Fix poetry lockfile not being up to date with pyproject.toml

### Internals

- Don't submit order and product in bar
- Don't lookup form values twice


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
