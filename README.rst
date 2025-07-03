===================
3D Model Repository
===================
This is a repository for 3D models and their metadata, for use by the community for improving the quality of 3D rendering of maps. The deployed version of the project can be experienced at `3dmr <https://3dmr.eu/>`_.

Project History
======================
This project was `originally developed <https://gitlab.com/n42k/3dmr>`_ as part of Google Summer of Code 2017 by `Pedro Amaro <https://github.com/n42k>`_, under the mentorship of the OpenStreetMap community with `Jan Marsch <https://github.com/kekscom>`_ and `Tobias Knerr <https://github.com/tordanik>`_ as mentors. The project was aimed at creating a repository for 3D models and their metadata, for use by the community for improving the quality of 3D rendering of maps.

Development Server Instructions
===============================

This project requires **PostgreSQL**, the `KhronosGroup glTF-Validator <https://github.com/KhronosGroup/glTF-Validator/>`_, **Python 3**, and **pip** to be installed on your system. It uses **Django** as the web framework, and it is recommended to use a Python virtual environment for development.

Prerequisites
-------------

1. Install Python 3 (version 3.13 recommended) and `pip3`.

2. Install PostgreSQL and ensure the server is running. You’ll also need to create a database and user for local development.

3. Install the glTF Validator:

   Download the appropriate binary release from the `KhronosGroup glTF-Validator releases <https://github.com/KhronosGroup/glTF-Validator/releases/>`_ page and extract the .tar.xz release into a dedicated folder.

   Then either:

   Add the directory containing the binary release to your `PATH`, or

   .. code-block:: bash

      mkdir /path/to/gltf_validator
      cd /path/to/gltf_validator
      wget https://github.com/KhronosGroup/glTF-Validator/releases/download/2.0.0-dev.3.10/gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
      tar -xf gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
   
   The binary should now be at /path/to/gltf_validator/gltf_validator
   Set the path in the `.env` file:

   .. code-block:: bash

      GLTF_VALIDATOR_PATH=/path/to/gltf_validator/gltf_validator

   Replace `/path/to/` with the actual path where you want to store the gltf_validator. This is required for model validation to work.

Setting Up the Development Server
---------------------------------

Follow these steps to get the project running locally:

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/fossgis/3dmr.git

2. Navigate into the project directory:

   .. code-block:: bash

      cd 3dmr

3. Set up a virtual environment:

   .. code-block:: bash

      python3 -m venv .venv

4. Activate the virtual environment:

   .. code-block:: bash

      source .venv/bin/activate

5. Install Python dependencies:

   .. code-block:: bash

      pip3 install -r requirements.txt

6. Copy the example environment file:

   .. code-block:: bash

      cp .env.example .env

7. Open the `.env` file and populate the environment variables as needed:

   .. list-table::
      :header-rows: 1

      * - Variable
        - Description
      * - ``POSTGRES_DB``
        - Name of your PostgreSQL database (e.g., ``3dmr_dev``).
      * - ``POSTGRES_USER``
        - PostgreSQL user with access to the database. It's highly recommended to create a separate unprivileged user with access restricted to only required database(s).
      * - ``POSTGRES_PASSWORD``
        - Password for the POSTGRES_USER user.
      * - ``POSTGRES_HOST``
        - Host where PostgreSQL is running (default is ``localhost``).
      * - ``POSTGRES_PORT``
        - Port for PostgreSQL (default is ``5432``).
      * - ``OSM_CLIENT_ID``
        - Your OpenStreetMap OAuth Application client ID.
      * - ``OSM_CLIENT_SECRET``
        - Your OSM OAuth Application client secret.
      * - ``DEBUG``
        - Set to ``True`` for development, ``False`` for production (default is ``True``). 
      * - ``DJANGO_SECRET_KEY``
        - A secret key for Django. Generate one using:
          ``python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'``
      * - ``MODEL_DIR``
        - Path to the directory where 3D models will be stored.
      * - ``STATIC_ROOT``
        - Path to the directory where static files will be collected.
      * - ``GLTF_VALIDATOR_PATH``
        - Path to the directory containing the `gltf_validator` binary.
      * - ``ALLOWED_HOSTS``
        - A comma-separated list of allowed hostnames for the Django application (e.g., ``localhost,127.0.0.1``).

8. Apply database migrations:

   .. code-block:: bash

      ./manage.py migrate

9. Run the development server:

   .. code-block:: bash

      ./manage.py runserver

Access your development server at: http://127.0.0.1:8000/

Deployment Instructions
=======================

These are step-by-step instructions to deploy the 3DMR repository using **Gunicorn** as the WSGI server and **Nginx** as the reverse proxy. These steps have been tested on a fresh Debian 13 installation.


1. System Setup
---------------

1. Update packages:

   .. code-block:: bash

      sudo apt update && sudo apt upgrade -y

2. Install required packages:

   .. code-block:: bash

      sudo apt install postgresql postgresql-client git python3 python3-pip nginx python3-venv


2. PostgreSQL Setup
-------------------

1. Switch to the `postgres` user:

   .. code-block:: bash

      sudo -u postgres -i

2. Create a PostgreSQL user and database:

   .. code-block:: bash

      createuser -d -P 3dmr
      createdb -O 3dmr 3dmr

3. Exit back to your original user:

   .. code-block:: bash

      exit


3. Application Setup
--------------------

1. Create a system user to run the app:

   .. code-block:: bash

      sudo adduser tdmr
      sudo usermod -aG www-data tdmr

2. Switch to that user:

   .. code-block:: bash

      su - tdmr

3. Clone the repository and set up environment:

   .. code-block:: bash

      git clone https://github.com/fossgis/3dmr.git
      cd 3dmr
      python3 -m venv .venv
      source .venv/bin/activate
      pip install -r requirements.txt

4. Install the glTF Validator:

   Download the appropriate binary release from the `KhronosGroup glTF-Validator releases <https://github.com/KhronosGroup/glTF-Validator/releases/>`_ page:

   .. code-block:: bash
      mkdir ~/gltf_validator
      cd ~/gltf_validator
      wget https://github.com/KhronosGroup/glTF-Validator/releases/download/2.0.0-dev.3.10/gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
      tar -xf gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
   
   The binary should now be at ~/gltf_validator/gltf_validator

5. Configure `.env` file:

   .. code-block:: bash

      cp .env.example .env
      nano .env

   Update the following fields:

   - Set `DEBUG=False`
   - Generate a `DJANGO_SECRET_KEY` (see dev instructions)
   - Fill in PostgreSQL credentials
   - Add OSM OAuth client ID and secret
   - Set `MODEL_DIR=/home/tdmr/models`
   - Set `STATIC_ROOT=/home/tdmr/staticfiles`
   - Set `GLTF_VALIDATOR_PATH=/home/tdmr/gltf_validator/gltf_validator`
   - Set `ALLOWED_HOSTS=your.domain.com`

6. Migrate database and collect static files:

   .. code-block:: bash

      ./manage.py migrate
      mkdir ~/models
      mkdir ~/staticfiles
      ./manage.py collectstatic


4. Gunicorn Setup
-----------------

Create a `gunicorn.service` file for systemd:

.. code-block:: bash

   sudo nano /etc/systemd/system/3dmr.service

.. code-block:: ini

   # /etc/systemd/system/3dmr.service
   [Unit]
   Description=3DMR Gunicorn daemon
   After=network.target

   [Service]
   User=tdmr
   Group=www-data
   WorkingDirectory=/home/tdmr/3dmr
   Environment="PATH=/home/tdmr/3dmr/.venv/bin"
   ExecStart=/home/tdmr/3dmr/.venv/bin/gunicorn modelrepository.wsgi:application --bind unix:/run/3dmr.sock

   [Install]
   WantedBy=multi-user.target

Enable and start the service:

.. code-block:: bash

   sudo systemctl daemon-reexec
   sudo systemctl daemon-reload
   sudo systemctl enable 3dmr
   sudo systemctl start 3dmr


5. Nginx Setup
--------------

1. Create a config file:

.. code-block:: nginx

   # /etc/nginx/sites-available/3dmr
   server {
       listen 80;
       listen [::]:80;
       server_name your.domain.com;

       location /static/ {
           alias /home/tdmr/staticfiles/;
       }

       location / {
           include proxy_params;
           proxy_pass http://unix:/run/3dmr.sock;
       }
   }

2. Enable the site and restart Nginx:

   .. code-block:: bash

      sudo ln -s /etc/nginx/sites-available/3dmr /etc/nginx/sites-enabled
      sudo nginx -t
      sudo systemctl restart nginx

3. Ensure permissions:

   .. code-block:: bash

      sudo chown -R tdmr:www-data /home/tdmr
      sudo chmod -R 755 /home/tdmr/models
      sudo chmod -R 755 /home/tdmr/staticfiles


6. Nightly Job Setup
--------------------

1. Create the script:

   .. code-block:: bash

      nano /home/tdmr/nightly.sh

   Contents:

   .. code-block:: bash

      #!/bin/bash
      cd /home/tdmr/3dmr/
      source .venv/bin/activate
      ./manage.py nightly
      mv 3dmr-nightly.zip /home/tdmr/staticfiles/mainapp

   Make it executable:

   .. code-block:: bash

      chmod +x /home/tdmr/nightly.sh
      ./nightly.sh

2. Add to crontab:

   .. code-block:: bash

      crontab -u tdmr -e

   Add:

   .. code-block::

      0 4 * * * /home/tdmr/nightly.sh


7. Done!
--------

Your 3DMR instance is now live and running via **Gunicorn and Nginx**.
