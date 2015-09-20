# HaploQA

TODO description of what this app does

## Installation

In order to install HaploQA you must first install and configure RabbitMQ, Celery and apache with mod_wsgi

Start Mongo like:

    mongod

Stop mongo with `crtl+c`

Start RabbitMQ like:

    ~/bin/rabbitmq_server-3.5.4/sbin/rabbitmq-server

Stop RabbitMQ like:

    ~/bin/rabbitmq_server-3.5.4/sbin/rabbitmqctl stop

Start Celery worker like:

    PYTHONPATH=src celery -A haploqa.haploqaapp.celery worker

Stop Celery with `ctrl+c`