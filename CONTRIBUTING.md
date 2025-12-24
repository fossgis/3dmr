# Contributing to 3DMR

Thank you for your interest in contributing to the 3D Model Repository (3DMR). This document provides an overview of the codebase and its main dependencies.

For instructions on setting up a local development environment, see [Development Setup](docs/development.md#development-setup).

## Project overview

3DMR is a Django-based web application that provides a central repository for storing, validating, and serving real world 3D models linked to OSM objects.

The project focuses on:

- validating uploaded 3D models (glTF / GLB),
- storing models and metadata in a structured and queryable way,
- authenticating users via OpenStreetMap,
- serving models and metadata to downstream renderers and tools via dedicated API.

## Codebase structure

The repository follows a standard Django project layout with a single primary application.

```text
3dmr/
├── .github/
│   └── workflows/
│       └── test.yml              # CI configuration (tests, linting)
│
├── mainapp/                      # Core Django application
│   ├── management/
│   │   └── commands/             # Custom Django management commands
│   │       ├── make_admin.py     # Grant/revoke admin privileges
│   │       ├── nightly.py        # Scheduled maintenance tasks
│   │       └── obj2glb.py        # Model conversion utility (see #30)
│   │
│   ├── migrations/               # Database migrations
│   │
│   ├── static/                   # Compiled static assets (generated)
│   │
│   ├── static_src/               # Frontend source code (Vite)
│   │   ├── public/
│   │   │   └── mainapp/          # Public static assets (copied as-is, no bundling)
│   │   └── src/                  # ES6 frontend modules (bundleable via Vite)
│   │
│   ├── templates/
│   │   └── mainapp/              # Django HTML templates
│   │
│   ├── tests/                    # Test suite
│   │
│   └── utils/                    # Shared helper utilities
│
├── modelrepository/              # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── docs/                          # Development and deployment docs
│
├── manage.py                      # Django management entry point
├── requirements.txt               # Python dependencies
└── .env.example                   # Example environment configuration
```

## Major dependencies

### Django

[Django](https://www.djangoproject.com/) is used as the core web framework for both the website and APIs

### glTF Validator

The [KhronosGroup glTF-Validator](https://github.com/KhronosGroup/glTF-Validator/) to validate uploaded 3D models.
It is run as an external binary to ensure strict compliance.
Validation is performed server-side to avoid broken models.

### OpenStreetMap OAuth2

Authentication is handled via OpenStreetMap OAuth2.
Allowing direct association of uploaded models with OSM users,
User identity and permissions are therefore tied to OSM accounts via OSM user_id.

### django-vite

The project uses [django-vite](https://github.com/MrBin99/django-vite) to integrate the Vite build tool with Django.

This is used to:

- provide fast rebuilds and hot module replacement (HMR) during frontend development,
- keep modern JavaScript tooling isolated from Django’s runtime,
- generate optimized static assets for production builds.

During development, Vite serves frontend assets via a separate dev server. In production, assets are built ahead of time and served as static files through Django and the web server.

`django-vite` relies on the `DEBUG` variable in `settings.py` to detect the state of the server.

### Frontend tooling (Node.js)

[ViteJS](https://github.com/vitejs/vite) is used exclusively for building frontend assets.

- Source files live under `mainapp/static_src`
- Compiled assets are output to `mainapp/static`
- The backend does not depend on `Node.js` at runtime

This separation keeps frontend tooling isolated from Django’s execution path.

## Contribution guidelines

### Reporting Bugs

Please use the issue tracker to report bugs. Include a clear description, steps to reproduce, and expected behavior.

### Proposing Changes

Fork the repository and create a feature branch for your changes. Submit a [Pull Request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests) back to the main 3DMR repository. Pull requests will be reviewed to ensure they align with the project's code standards and architecture.

### General Advice

- Open an issue or comment on an existing one before starting large changes.
- Prefer small, focused pull requests.
- Keep changes scoped to a single concern when possible.
- Avoid reformatting or refactoring unrelated code.
- Write clear, descriptive commit messages.
- Include context in pull request descriptions explaining *why* a change is needed, not just *what* was changed.

If a change affects deployment, configuration, or external dependencies, please update the relevant documentation under `docs/`.

Contributions of all sizes are welcome, including documentation improvements, bug fixes, and feature enhancements.
