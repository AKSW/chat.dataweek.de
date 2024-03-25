FROM docker.io/library/python:3.11

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local/ python3 -

WORKDIR /usr/src/app
COPY . .
RUN poetry install

CMD poetry run gunicorn chat.fastbot:app --bind :3000 --worker-class aiohttp.GunicornWebWorker
