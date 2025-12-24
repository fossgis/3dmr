# Deployment Instructions

These are step-by-step instructions to deploy the 3DMR repository using **Gunicorn** as the WSGI server and **Nginx** as the reverse proxy. These steps have been tested on a fresh Debian 13 installation.

## 1. System Setup

1. Update packages:

    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2. Install required packages:

    ```bash
    sudo apt install -y postgresql postgresql-client git python3 python3-pip nginx python3-venv nodejs npm
    ```

## 2. PostgreSQL Setup

1. Switch to the `postgres` user:

    ```bash
    sudo -u postgres -i
    ```

2. Create a PostgreSQL user and database:

    ```bash
    createuser -d -P 3dmr
    createdb -O 3dmr 3dmr
    ```

3. Exit back to your original user:

    ```bash
    exit
    ```

## 3. Application Setup

1. Create a system user to run the app:

    ```bash
    sudo adduser tdmr
    sudo usermod -aG www-data tdmr
    ```

2. Switch to that user:

    ```bash
    su - tdmr
    ```

3. Clone the repository and set up environment:

    ```bash
    git clone https://github.com/fossgis/3dmr.git
    cd 3dmr
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

4. Install the glTF Validator:

    Download the appropriate binary release from the [KhronosGroup glTF-Validator releases](https://github.com/KhronosGroup/glTF-Validator/releases/) page:

    ```bash
    mkdir ~/gltf_validator
    cd ~/gltf_validator
    wget https://github.com/KhronosGroup/glTF-Validator/releases/download/2.0.0-dev.3.10/gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
    tar -xf gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
    ```

    The binary should now be at `~/gltf_validator/gltf_validator`.

5. Configure `.env` file:

    ```bash
    cp .env.example .env
    nano .env
    ```

    The following values are recommended for a standard production deployment:
    - Set `DEBUG=False`
    - Generate a `DJANGO_SECRET_KEY`

        ```python
        from django.core.management.utils import get_random_secret_key
        print(get_random_secret_key())
        ```

    - Fill in PostgreSQL credentials
    - Add OSM OAuth client ID and secret
    - Set `MODEL_DIR=/home/tdmr/models`
    - Set `STATIC_ROOT=/home/tdmr/staticfiles`
    - Set `GLTF_VALIDATOR_PATH=/home/tdmr/gltf_validator/gltf_validator`
    - Set `ALLOWED_HOSTS=your.domain.com`

6. Build static files:
    Navigate to the `mainapp/static_src` directory and run:

    ```bash
    npm install
    npm run build
    ```

    This will compile the static files needed for the web application and store them in `mainapp/static` directory.

7. Migrate database and collect static files:

    ```bash
    mkdir ~/models
    mkdir ~/staticfiles
    ./manage.py migrate
    ./manage.py collectstatic
    ```

## 4. Gunicorn Setup

Create a `3dmr.socket` file for systemd:

```bash
sudo nano /etc/systemd/system/3dmr.socket
```

```ini
# /etc/systemd/system/3dmr.socket
[Unit]
Description=3DMR Gunicorn socket

[Socket]
ListenStream=/run/3dmr.sock
SocketUser=www-data

[Install]
WantedBy=multi-user.target
```

Create a `3dmr.service` file for systemd:

```bash
sudo nano /etc/systemd/system/3dmr.service
```

```ini
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
```

Enable and start the service:

```bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable 3dmr
sudo systemctl start 3dmr
```

If the service fails to start, check logs with:

```bash
sudo journalctl -u 3dmr.service
```

## 5. Nginx Setup

1. Create a config file:

    ```nginx
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
    ```

2. Enable the site and restart Nginx:

    ```bash
    sudo ln -s /etc/nginx/sites-available/3dmr /etc/nginx/sites-enabled
    sudo nginx -t
    sudo systemctl restart nginx
    ```

3. Ensure permissions:

    ```bash
    sudo chown -R tdmr:www-data /home/tdmr
    sudo chmod -R 755 /home/tdmr/models
    sudo chmod -R 755 /home/tdmr/staticfiles
    ```

## 6. Nightly Job Setup

1. Create the script:

    ```bash
    nano /home/tdmr/nightly.sh
    ```

    Contents:

    ```bash
    #!/bin/bash
    cd /home/tdmr/3dmr/
    source .venv/bin/activate
    ./manage.py nightly
    mv 3dmr-nightly.zip /home/tdmr/staticfiles/mainapp
    ```

    Make it executable:

    ```bash
    chmod +x /home/tdmr/nightly.sh
    ./nightly.sh
    ```

2. Add to crontab:

    ```bash
    crontab -u tdmr -e
    ```

    Add:

    ```bash
    0 4 * * * /home/tdmr/nightly.sh
    ```

## 7. User administration

3DMR provides a Django management command to grant or remove administrator privileges for users.

Users can be targeted either by their **3DMR username** (which might differ from user's latest OSM display_name) or by their OpenStreetMap user ID (`uid`). The optional `--dismiss` flag removes administrator access.

### Usage

```bash
# Grant admin privileges
python manage.py make_admin --username AyushDharDubey
python manage.py make_admin --uid 22632699

# Remove admin privileges
python manage.py make_admin --username AyushDharDubey --dismiss
python manage.py make_admin --uid 22632699 --dismiss
```

## 8. Completion

Your 3DMR instance is now live and running via **Gunicorn and Nginx**.
