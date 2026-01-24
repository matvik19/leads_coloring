###########
# BUILDER #
###########
FROM python:3.12-slim AS builder

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Объединяем apt update и install для избежания кэширования устаревших индексов
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

#########
# FINAL #
#########

FROM python:3.12-slim

# Объединяем apt update и install + очистка кэша
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        netcat-traditional \
        libpq-dev \
        libpq5 && \
    rm -rf /var/lib/apt/lists/*

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
