# PS Helper

**PS Helper** is a Python package developed by the Professional Services team.  
It provides a set of helper libraries and command-line tools to speed up and standardize development workflows.

---

## 🚀 Features
- Ready-to-use Python utilities for internal projects.
- CLI commands for common tasks (e.g., creating repository templates).
- Easy to install and extend.

---

## 📦 Installation

You can install **PS Helper** in two ways:

### Option 1: Local installation (development mode)
Clone the repository and install it with `pip`:

```bash
git clone https://github.com/bitmakerla/ps-helper.git
cd ps-helper
pip install -e .
```

This will install the package in editable mode, so any code changes will be reflected immediately.

### Option 2: Install directly from GitHub

You can install the package without cloning:

```bash
pip install git+https://github.com/bitmakerla/ps-helper.git
```

---

## 🛠 Usage
Check available commands:
```bash
ps-helper --help
```

Create a new project from the template:
```bash
ps-helper create-repo-template MyProject
```
