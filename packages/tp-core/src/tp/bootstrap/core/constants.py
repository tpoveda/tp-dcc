from __future__ import annotations

from typing import Final

# Defines the folder name where TP DCC pipeline development files are located.
DEV_FOLDER_NAME: Final[str] = "dev"

# Defines the folder name where the TP DCC package config files are located.
CONFIG_FOLDER_NAME: Final[str] = "config"

# Defines the folder name where the TP DCC packages are located.
PACKAGES_FOLDER_NAME: Final[str] = "packages"

# Defines the name of the TP DCC packages configuration file.
PACKAGE_NAME: Final[str] = "package.yaml"

# Defines the environment variable that can be used to override the log level
# of the TP DCC pipeline.
LOG_LEVEL_ENV_VAR = "TP_DCC_LOG_LEVEL"

# Root directory of the TP_DCC pipeline.
ROOT_DIRECTORY_ENV_VAR: Final[str] = "TP_DCC_PIPELINE_ROOT_DIRECTORY"

# Defines the environment variable that can be used to override the path to the
# TP DCC pipeline site packages. This should be defined for each host.
SITE_PACKAGES_ENV_VAR: Final[str] = "TP_DCC_PIPELINE_SITE_PACKAGES"

# Defines the environment variable that can be used to override the path to the
# environment configuration file.
PACKAGES_ENVIRONMENT_CONFIG_PATH_ENV_VAR: Final[str] = (
    "TP_DCC_PACKAGES_ENVIRONMENT_CONFIG_PATH"
)

# Defines the environment variable that can be used to override the file name
# of the environment configuration file.
PACKAGES_ENVIRONMENT_CONFIG_FILE_ENV_VAR: Final[str] = (
    "TP_DCC_PACKAGES_ENVIRONMENT_CONFIG_FILE"
)

# Defines the environment used for the cache.
CACHE_FOLDER_PATH_ENV_VAR: Final[str] = "TP_DCC_CACHE_FOLDER_PATH"

# Filter for the package dependencies in the package descriptor.
PACKAGE_DEPENDENCIES_FILTER = r"\{(.*?)\}"

# Environment variable that defines if the current user is a TP DCC admin user.
TP_DCC_ADMIN_ENV_VAR = "TP_DCC_ADMIN"
