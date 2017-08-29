===================
3D Model Repository
===================
This project is a repository for 3D models, and their metadata, for use by the OpenStreetMap community for improving the quality of 3D rendering of maps, developed as part of Google Summer of Code 2017 by Pedro Amaro, with Jan Marsch and Tobias Knerr as mentors.

Development Server Instructions
===============================
Firstly, install ``python3`` and ``pip3``. You also need the ``virtualenv`` python package, you can install it with ``sudo pip3 install virtualenv``.
Then, to get a development server running from this repository:

1. Clone the repository, ``git clone https://gitlab.com/n42k/3dmr.git``.
2. Move inside the directory that was created, ``cd 3dmr``.
3. Set up the virtualenv, ``virtualenv .env``.
4. Activate the virtualenv, ``source .env/bin/activate``.
5. Install the required packages, ``pip3 install -r requirements.txt``.
6. Set up the PostgreSQL database, configure it in ``modelrepository/settings.py``, and run ``./manage.py makemigrations`` and ``./manage.py migrate``.
7. Run the server! ``./manage.py runserver 8080``.

Your development server should now be running on port 8080.

Deployment Instructions
=======================
1. These are a set of simple step-by-step deployment instructions for 3dmr, to get the repository running on a server quickly. These steps have been tested in a fresh Debian 9 installation.

 1. Starting off, make sure to update your current packages: ``# apt-get update`` and ``# apt-get upgrade``.

 2. Download the required packages, in one go: ``# apt-get install postgresql postgresql-client git python3 python3-pip apache2 libapache2-mod-wsgi-py3 python-virtualenv``.
    Note: do not install python3-virtualenv, it won't work, python-virtualenv will work for both major versions of Python.

2. Let's now set up PostgreSQL.

 1. Edit the file ``/etc/postgresql/9.6/main/pg_hba.conf``, adding ``local all 3dmr password``, after ``local all postgres peer``, and then restart its service: ``service postgresql restart``.

 2. Switch to the postgres user: ``su - postgres``. The next few steps will be done in this user.

 3. Create an user to use with the repository: ``createuser -d -P 3dmr``. Remember the password you enter here.

 4. Create a new database for the repository, as the 3dmr user: ``createdb -O 3dmr 3dmr``.

 5. Run ``psql -d 3dmr -c "create extension hstore;"`` to activate the hstore extension on the database.

 6. The database setup is now finished! Make sure to get back to the root user with ``exit``.

3. We will now acquire the project from the git repository. This should be done with a separate user.

 1. Let's create it now: ``# adduser tdmr`` (t stands for the t in three, as there can be no names starting with a digit).

 2. Switch to the newly created user: ``su - tdmr``. The next commands will be run as this user.

 3. In the home directory of this user, run ``git clone https://gitlab.com/n42k/3dmr.git``, then move inside it: ``cd 3dmr``.

 4. Setup the virtualenv: ``virtualenv -p python3 .env``, and activate it: ``source .env/bin/activate``, and install the required Python packages: ``pip3 install -r requirements.txt``.

 5. We must now configure the model repository.

  1. With your favourite text editor, begin editing ``modelrepository/settings.py``. Then, in order, edit the folllowing variables:

  2. Generate a new random ``SECRET_KEY``. This should be generated randomly, by a computer. One quick way to do this is running
     ``import binascii;import os;binascii.hexlify(os.urandom(50))`` in a Python shell.

  3. Set ``DEBUG`` to ``False``, as we're now in production.

  4. Set ``ALLOWED_HOSTS`` to ``['*']``. *IMPORTANT*: You should replace this with ``['www.yourdomain.com']`` when you host it on a domain, or your public IP,
     according to https://docs.djangoproject.com/en/1.11/ref/settings/#allowed-hosts .

  5. You should also use your own OpenStreetMap OAuth key and secret, replacing ``SOCIAL_AUTH_OPENSTREETMAP_KEY`` and ``SOCIAL_AUTH_OPENSTREETMAP_SECRET``.

  6. Configure the ``DATABASES`` entry: change ``n42k`` to ``3dmr``, and the password ``carrots``, to the one set in 2.3.

  7. Finally, add the directory where we'll hold the static files, by appending at the end of this file ``STATIC_ROOT = 'home/tdmr/static/'``.

  8. You can now save and close this file.

 6. Run ``./manage.py migrate`` to create the tables for our database. Note: run ``./manage.py makemigrations`` first for now.

 7. Create a directory to hold the model zips: ``mkdir ~/models``.
    Configure the repository to use this directory in ``mainapp/utils.py``, at the end of the file: ``MODEL_DIR = '/home/tdmr/models'``.

 8. Create a directory to hold the static files: ``mkdir ~/static`` and run ``./manage.py collectstatic`` to place the static files there.

 9. Set up the nightlies task, by placing the following script in ``/home/3dmr/nightly.sh``:

    | #!/bin/bash
    | cd /home/tdmr/3dmr/
    | source .env/bin/activate
    | ./manage.py nightly
    | mv 3dmr-nightly.zip /home/tdmr/static/mainapp

    and give it executable permissions: ``chmod +x nightly.sh``, and run it once, to set up an initial, empty, nightly zip: ``./nightly.sh``.

 10. You should now be able to connect on port 8080 to the development server after running ``./manage.py runserver 0.0.0.0:8080``.
     Note that this will not yet work fully: static files will 404 (explaining the big avatar in the navbar if you login, or the missing model previews).
     Do not use this in production.

4. Now, let's set up Apache.

 1. Edit, as the root user, ``/etc/apache2/sites-available/000-default.conf``, adding at the end of the VirtualHost section:

    | <VirtualHost \*:80>
    |         Alias /static/ /home/tdmr/static/
    |         <Directory /home/tdmr/static>
    |                 Require all granted
    |         </Directory>
    |         <Directory /home/tdmr/3dmr/modelrepository>
    |                 <Files wsgi.py>
    |                         Require all granted
    |                 </Files>
    |         </Directory>
    |
    |         WSGIDaemonProcess 3dmr python-path=/home/tdmr/3dmr:/home/tdmr/3dmr/.env/lib/python3.5/site-packages
    |         WSGIProcessGroup 3dmr
    |         WSGIScriptAlias / /home/tdmr/3dmr/modelrepository/wsgi.py
    | </VirtualHost>

 2. Give Apache write permission to the model directory, by running ``# chmod -R 0775 /home/tdmr/models`` and ``# chown -R :www-data /home/tdmr/models``.

 3. Finally, restart Apache to update its settings: ``# service apache2 restart``

5. The last remaining step is to set up the nightly script to run as a cronjob.

 1. Open the crontab, as the user ``tdmr``: ``# crontab -u tdmr -e``.

 2. Create an entry in the crontab for the nightly script, to run every day, at 4 AM: ``0 4 * * * /home/tdmr/nightly.sh``.

 3. The 3D model repository has been successfully deployed!
