# HaploQA

TODO description of what this app does

## Installation

HaploQA requires Python 3.  Begin by installing that. In order to install HaploQA you must first install and configure MongoDB, RabbitMQ, Celery and apache with mod_wsgi. Assuming for a development installation you are working on a mac you can use the following instructions.  For CENTOS there will be simalar commands using yum.

I prefer to work from a VirtualEnv.  If you don't already have virtualenv you'll want to install it:

    pip install virtualenv
    
once that's installed create your virtual environment.  Note: That if python3 is not in your path, you'll need to give the explicit path to it's location.

    virtualenv -p python3 HaploQA
    
then activate it

    . haploqa/bin/activate
    
### To install MongoDB first update brew

    brew update
    
then install MongoDB with

    brew install mongodb
    
You'll need to create a folder for your database

    mkdir db
    
Instructions for starting Mongo are below.

### To install RabbitMQ

    brew install rabbitmq
    
Instructions fro starting are below.

### To install Celery

    pip install Celery



## Running a local (development) instance

Start Mongo like:

    mongod --dbpath db

Stop mongo with `crtl+c`

Start/Stop RabbitMQ like (not on the mac rabbitmq scripts will be located in /usr/local/sbin/) :

    rabbitmq-server
    rabbitmqctl stop

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

## Create an admin account

For a new installation you are going to need an administrative account to work through the system.  Once you have that first account created, you can create other user accounts through the UI.  

From the project root directory (where src is a subdirectory), run the following command:

    PYTHONPATH=src python src/haploqa/usermanagement.py
    
You will be prompted for an email address and a password.