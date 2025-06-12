from __future__ import annotations

import os
import shutil


def main():
    """Function that is called after the cookiecutter template is generated.

    This function is used to rename the _package_name.py file to the package
    name defined in the cookiecutter template.
    """

    package_name = "{{ cookiecutter.package_name }}".replace("-", "_")
    scripts_dir = os.path.join(os.getcwd(), "scripts")
    old_file = os.path.join(scripts_dir, "{{ cookiecutter.package_name }}.py")
    new_file = os.path.join(scripts_dir, f"{package_name}.py")

    if os.path.exists(old_file):
        shutil.move(old_file, new_file)


if __name__ == "__main__":
    main()
