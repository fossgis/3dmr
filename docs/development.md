# Development Setup

This project requires [PostgreSQL](https://www.postgresql.org/download/), [KhronosGroup glTF-Validator](https://github.com/KhronosGroup/glTF-Validator/), [Python](https://www.python.org/downloads/), and [Node.js](https://nodejs.org/en/download) to be installed on your system. It uses [Django](https://docs.djangoproject.com/en/6.0/intro/install/) as the web framework, and it is recommended to use a Python virtual environment for development.

## Prerequisites

### System Dependencies

1. Install Python 3 (version 3.13 recommended), `pip3`, Node (version 20.x recommended) and `npm`.

2. Install PostgreSQL and ensure the server is running. You’ll also need to create a database and user for local development.

### External tools and services

1. **Install the glTF Validator:**

    Download the appropriate binary release from the [KhronosGroup glTF-Validator releases](https://github.com/KhronosGroup/glTF-Validator/releases/) page and extract the .tar.xz release into a dedicated folder.

    ```bash
    mkdir /path/to/gltf_validator
    cd /path/to/gltf_validator
    wget https://github.com/KhronosGroup/glTF-Validator/releases/download/2.0.0-dev.3.10/gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
    tar -xf gltf_validator-2.0.0-dev.3.10-linux64.tar.xz
    ```

    The binary should now be available at `/path/to/gltf_validator/gltf_validator`.

    Either add this directory to your `PATH`, or set the path explicitly in `.env`:

    ```bash
    GLTF_VALIDATOR_PATH=/path/to/gltf_validator/gltf_validator
    ```

    This is required for model validation to work.

2. **Create OSM OAuth2 Application:**

    Go to the [OpenStreetMap OAuth2 Applications](https://www.openstreetmap.org/oauth2/applications) page and create a new application.
    You will need to provide a name, and callback URL: `http://127.0.0.1:8000/social/complete/openstreetmap-oauth2/`.
    After creating the application, you will receive a client ID and client secret.

## Setting Up the Development Server

Follow these steps to get the project running locally:

1. Clone the repository:

    ```bash
    git clone https://github.com/fossgis/3dmr.git
    ```

2. Navigate into the project directory:

    ```bash
    cd 3dmr
    ```

3. Set up a virtual environment:

    ```bash
    python3 -m venv .venv
    ```

4. Activate the virtual environment:

    ```bash
    source .venv/bin/activate
    ```

5. Install Python dependencies:

    ```bash
    pip3 install -r requirements.txt
    ```

6. Copy the example environment file:

    ```bash
    cp .env.example .env
    ```

7. Open the `.env` file and populate the the following environment variables:

    | Variable | Description |
    | :--- | :--- |
    | `POSTGRES_DB` | Name of your PostgreSQL database (e.g., `3dmr_dev`). |
    | `POSTGRES_USER` | PostgreSQL user with access to the database. It's highly recommended to create a separate unprivileged user with access restricted to only required database(s). |
    | `POSTGRES_PASSWORD` | Password for the POSTGRES_USER user. |
    | `POSTGRES_HOST` | Host where PostgreSQL is running (default is `localhost`). |
    | `POSTGRES_PORT` | Port for PostgreSQL (default is `5432`). |
    | `OSM_CLIENT_ID` | Your OpenStreetMap OAuth Application client ID. |
    | `OSM_CLIENT_SECRET` | Your OSM OAuth Application client secret. |
    | `DEBUG` | Set to `True` for development, `False` for production (default is `True`). |
    | `DJANGO_SECRET_KEY` | A secret key for Django. Generate one using: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'` |
    | `MODEL_DIR` | Path to the directory where 3D models will be stored. |
    | `STATIC_ROOT` | Path to the directory where static files will be collected. |
    | `GLTF_VALIDATOR_PATH` | Path to the directory containing the `gltf_validator` binary. |
    | `ALLOWED_HOSTS` | A comma-separated list of allowed hostnames for the Django application (e.g., `localhost,127.0.0.1`). |

8. Run Vite dev server for serving statics:

    Navigate to the `mainapp/static_src` directory and run:

    ```bash
    npm install
    npm run build
    npm start dev
    ```

    This will compile the static files needed for the web application, store them in `mainapp/static` directory and, start the static dev server.

9. Apply database migrations:

    ```bash
    ./manage.py migrate
    ```

10. Run the development server:

    ```bash
    ./manage.py runserver
    ```

Access your development server at: <http://127.0.0.1:8000/>
