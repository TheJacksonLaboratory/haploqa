# HaploQA

TODO description of what this app does

## Installation

In order to install HaploQA you must first install and configure RabbitMQ, Celery and apache with mod_wsgi

## Running a local (development) instance

Start Mongo like:

    mongod

Stop mongo with `crtl+c`

Start/Stop RabbitMQ like:

    ~/bin/rabbitmq_server-3.5.4/sbin/rabbitmq-server
    ~/bin/rabbitmq_server-3.5.4/sbin/rabbitmqctl stop

Start Celery worker like:

    PYTHONPATH=src celery -A haploqa.haploqaapp.celery worker

Stop Celery with `ctrl+c`

On OSX we can start the local postfix server like:

    sudo postfix start

## Running on Linux (tested on CentOS)

Start/Stop the Web Service Like:

    sudo service httpd24-httpd start
    sudo service httpd24-httpd stop

Start/Stop Mongo Like:

    sudo service mongod start
    sudo service mongod stop

Start/Stop celery Like:

    sudo service haploqa-celeryd start
    sudo service haploqa-celeryd stop
