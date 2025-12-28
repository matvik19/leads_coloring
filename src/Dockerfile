###########
# BUILDER #
###########
FROM python:3.12-slim as builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update
RUN apt -y install build-essential libpq-dev

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# FINAL #
#########

FROM python:3.12-slim

RUN apt update
RUN apt -y install netcat-traditional libpq-dev

RUN mkdir -p /home/app

RUN adduser app

ENV HOME=/home
WORKDIR $HOME

COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . $HOME

RUN chown -R app:app $HOME

ENV TZ=Europe/Moscow

USER app
ENTRYPOINT ["/home/entrypoint.app.sh"]
