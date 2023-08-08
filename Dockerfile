FROM python:3.11-alpine

RUN apk --no-cache add poetry

WORKDIR /app

COPY . /app

RUN poetry install --without dev

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:80", "--workers=4", "run:app"]
