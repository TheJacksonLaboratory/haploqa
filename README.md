# HaploQA

## Overview

The HaploQA web application was developed at the [Jackson Laboratory](http://www.jax.org) with support from the Mutant
Mouse Regional Resource Centers (NIH OD010921) and the Jackson Laboratory Genetic Resource Science group.  The purpose
of the tool is to facilitate genetic quality assurance of mice using genotype data derived from genotyping platforms
such as GigaMUGA and MegaMUGA. The application was originally developed by [Keith Sheppard](https://github.com/keithshep)
as part of the Jackson Laboratory's [Computational Sciences]
(https://www.jax.org/research-and-faculty/tools/scientific-research-services/computational-sciences) group.  A public
instance of the HaploQA web application is available at [https://haploqa.jax.org](https://haploqa.jax.org/) and the
source code is made available under an [MIT license](LICENSE.txt).

Major Contributions:
* Laura Reinholdt
* [Keith Sheppard](https://github.com/keithshep)
* [Gary Churchill](https://github.com/churchill-lab)
* [Dan Gatti](https://github.com/dmgatti)
* [Anna Lamoureux](https://github.com/anna-lamoureux)
* [Ben Robinson](https://www.linkedin.com/in/gnotek/)
* [Vinita Sinha]( https://www.linkedin.com/in/vinita-sinha-219a60b2/)
* [Dave Walton](https://github.com/obwalton)

## Installation

HaploQA requires Python 3.  Begin by installing that. In order to install HaploQA you must first install and configure
MongoDB, RabbitMQ, Celery and apache with mod_wsgi. Assuming for a development installation you are working on a mac you
can use the following instructions.  For CENTOS there will be similar commands using yum.

I prefer to work from a VirtualEnv.  If you don't already have virtualenv you'll want to install it:

    pip install virtualenv

once that's installed create your virtual environment.  Note: That if python3 is not in your path, you'll need to give
the explicit path to it's location.

    virtualenv -p python3 HaploQA

then activate it

    . haploqa/bin/activate

then install all of your python project dependencies

    pip install -r requirements.txt

### To install MongoDB first update brew

    brew update

then install MongoDB with

    brew install mongodb

You'll need to create a folder for your database

    mkdir db

Instructions for starting Mongo are below.

### To install RabbitMQ

    brew install rabbitmq

Instructions for starting are below.

### To install Celery

    pip install Celery


## Running a local (development) instance
Start Mongo like:

    mongod --dbpath db --storageEngine mmapv1

Stop mongo with `crtl+c`

Start/Stop RabbitMQ like (note on the mac rabbitmq scripts will be located in /usr/local/sbin/) :

    rabbitmq-server
    rabbitmqctl stop

Start Celery worker like:

    PYTHONPATH=src python -m celery worker -A haploqa.haploqaapp.celery --logfile <abs_path>/logs/celery.log

Stop Celery with `ctrl+c`

On OSX we can start the local postfix server like:

    sudo postfix start

On OSX to run the app from the command-line (for development purposes only):

For the first time running:

    $ export FLASK_ENV=development
    $ export FLASK_APP=src/haploqa/haploqaapp.py
    $ flask run

After the first time, all it should take to run is:
    $ flask run

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

For a new installation you are going to need an administrative account to work through the system.  Once you have that
first account created, you can create other user accounts through the UI.

From the project root directory (where src is a subdirectory), run the following command:

    PYTHONPATH=src python src/haploqa/usermanagement.py
    
You will be prompted for an email address and a password.

## External Library Credits

saveSvgAsPng.js: script to save a D3 plot (svg) as a png. MIT license - author Eric Shull (github.com/exupero/saveSvgAsPng)

d3.tip.v0.6.3.js: script to create tooltips. - author Justin Palmer (http://labratrevenge.com/d3-tip/)
