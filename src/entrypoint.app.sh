#!/bin/sh

echo "Waiting for db..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.5
done

echo "DB started"

while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 0.5
done

echo "Reddis started"

while ! nc -z $RABBITMQ_HOST $RABBITMQ_PORT; do
  sleep 0.5
done

echo "RabbitMQ started"

echo "Apply migrations"
alembic upgrade head

exec "$@"
