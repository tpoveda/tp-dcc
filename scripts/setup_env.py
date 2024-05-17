from __future__ import annotations

import os
import sys
import logging
import argparse
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def create_virtualenv(venv_dir: str):
    """
    Create a virtual environment in the specified directory.

    :param venv_dir: The directory where the virtual environment will be created.
    :type venv_dir: str
    """
    
    logging.info(f'Creating virtual environment in {venv_dir}...')
    subprocess.run([sys.executable, '-m', 'venv', venv_dir])
    logging.info('Virtual environment created.')


def install_requirements(venv_dir: str, requirements_files: list[str]) -> None:
    """
    Install dependencies from the specified requirements files.

    :param venv_dir: The directory of the virtual environment.
    :type venv_dir: str
    :param requirements_files: A list of paths to requirements files.
    :type requirements_files: list[str]
    """
    
    pip_executable = (
        os.path.join(venv_dir, 'bin', 'pip')
        if os.name != 'nt'
        else os.path.join(venv_dir, 'Scripts', 'pip')
    )
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            logging.info(f'Installing dependencies from {req_file}...')
            subprocess.run([pip_executable, 'install', '--upgrade', '-r', req_file])
        else:
            logging.warning(f'{req_file} not found. Skipping.')


def main() -> None:
    """
    Main function to create a virtual environment and install dependencies.
    """
    parser = argparse.ArgumentParser(description='Create a virtual environment and install dependencies.')
    parser.add_argument('--venv-dir', dest='venv_dir', default='venv', help='Directory for virtual environment')
    args = parser.parse_args()

    requirements_files = ['../requirements.txt']
    
    create_virtualenv(args.venv_dir)
    install_requirements(args.venv_dir, requirements_files)
    logging.info('Setup completed successfully.')


if __name__ == "__main__":
    main()