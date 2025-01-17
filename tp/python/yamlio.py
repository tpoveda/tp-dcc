from __future__ import annotations

import os
import logging

import yaml
import yaml.representer

logger = logging.getLogger(__name__)


def validate_yaml(dictionary: dict) -> bool:
    """
    Validates whether the given dictionary can be dumped into a YAML file.

    :param dictionary: dictionary to store.
    :return: True if the dictionary is valid; False otherwise.
    """

    # noinspection PyBroadException
    try:
        yaml.dump(dictionary)
        return True
    except Exception:
        return False


def write_to_file(data: dict, filename: str, **kwargs) -> str | None:
    """
    Writes data to YAML file.

    :param data: data to store into YAML file.
    :param filename: name of the YAML file we want to store data into.
    :return: file name of the stored file.
    """

    indent = kwargs.pop("indent", 2)
    dumper = kwargs.pop("Dumper", None)
    kwargs["default_flow_style"] = kwargs.pop("default_flow_style", False)
    kwargs["width"] = kwargs.pop("width", 200)

    try:
        with open(filename, "w") as yaml_file:
            if not dumper:
                try:
                    yaml.safe_dump(data, yaml_file, indent=indent, **kwargs)
                except yaml.representer.RepresenterError:
                    yaml.dump(data, yaml_file, indent=indent, **kwargs)
            else:
                yaml.dump(data, yaml_file, indent=indent, Dumper=dumper, **kwargs)
    except IOError:
        logger.error("Data not saved to file {}".format(filename))
        return None

    logger.debug("File correctly saved to: {}".format(filename))

    return filename


def read_file(filename: str) -> dict | list | None:
    """
    Returns data from YAML file.

    :param filename: name of YAML file we want to read data from.
    :return: data read from YAML file as dictionary.
    """

    if os.stat(filename).st_size == 0:
        return None
    else:
        try:
            with open(filename, "r") as yaml_file:
                data = yaml.safe_load(yaml_file)
        except Exception as exc:
            logger.warning("Could not read {} : {}".format(filename, exc))
            return None

    return data
