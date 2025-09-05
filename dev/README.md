# 🧪 TP DCC Development Cookbook

This guide provides useful commands and steps for setting up and maintaining 
the TP DCC development environment.

## Requirements

### Install UV (Python package and environment manager)

```bash
iwr https://astral.sh/uv/install.ps1 -useb | iex
```

---

## 🔄 Setting up Virtual Environments

The following scripts will:
* ✅ Check if each venv exists.
* 🔧 Create the virtual environment it if missing.
* 📦 Install and sync requirements.

`
### Development
`
```bash
python scripts/venv_setup.py --create --env dev
```

```bash
python ./scripts/venv_setup.py --create --force --env dev
```

```bash
python ./scripts/venv_setup.py --update --env dev
```

### Maya 2026

```bash
python scripts/venv_setup.py --create --env maya2026
```

```bash
python ./scripts/venv_setup.py --create --force --env maya2026
```

```bash
python ./scripts/venv_setup.py --update --env maya2026
```

---

### Unreal Engine 5

```bash
python scripts/venv_setup.py --create --env ue5
```

```bash
python ./scripts/venv_setup.py --create --force --env ue5
```

```bash
python ./scripts/venv_setup.py --update --env ue5
```

---

### MotionBuilder 2026

```bash
python scripts/venv_setup.py --create --env mobu2026
```

```bash
python ./scripts/venv_setup.py --create --force --env mobu2026
```

```bash
python ./scripts/venv_setup.py --update --env mobu2026
```

### Houdini 20.5.522

```bash
python scripts/venv_setup.py --create --env hou20522
```

```bash
python ./scripts/venv_setup.py --create --force --env hou20522
```

```bash
python ./scripts/venv_setup.py --update --env hou20522
```

## 📦 Creating a New TP DCC Python Package
To create a new TP DCC package using the Cookiecutter template, run:

```bash
uv tool install cookiecutter
```

```bash
cookiecutter cookiecutter/package --output-dir ../packages
```

You'll be prompted for:
* `package_name` (e.g., `tp-xyz`)
* `module_name` (Python module inside the tp/ namespace)
* `description`
* `version` (e.g., `0.1.0`)
* `author_name`
* `author_email`

This will:
* 📁 Generate a new `tp-xyz` package in the `packages/` folder.
