from __future__ import annotations

import logging

from . import config
from .convention import NamingConvention
from .preset import PresetsManager
from .rule import Rule

logger = logging.getLogger(__name__)

_PRESET_MANAGER: PresetsManager | None = None
_ACTIVE_NAMING_CONVENTION: NamingConvention | None = None


def naming_preset_manager(
    configuration: config.NamingConfiguration | None = None,
) -> PresetsManager:
    """Returns the global project naming convention.

    Args:
        configuration: Optional naming configuration to use. If not provided, uses the global configuration.

    Returns:
        PresetsManager: preset manager instance.

    Raises:
        RuntimeError: if no naming preset file path is found in configured paths.
    """

    global _PRESET_MANAGER
    if _PRESET_MANAGER is not None:
        return _PRESET_MANAGER

    cfg = configuration or config.get_configuration()

    # Find default preset file from configured paths.
    default_preset_file = cfg.find_preset_file(cfg.default_preset_name)
    if default_preset_file is None:
        raise RuntimeError(
            f'No preset file "{cfg.default_preset_name}" found in configured paths: {cfg.preset_paths}. '
            "Make sure to configure preset paths using config.add_preset_path()."
        )

    _PRESET_MANAGER = PresetsManager.from_configuration(configuration=cfg)

    return _PRESET_MANAGER


def reset_preset_manager():
    """Resets the global preset manager."""

    global _PRESET_MANAGER
    _PRESET_MANAGER = None
    logger.debug("Global preset manager reset")


def naming_convention(
    name: str = "global", set_as_active: bool = False
) -> NamingConvention | None:
    """Returns the naming convention with given name defined within global naming preset manager.

    Args:
        name: Name of the naming convention to get instance of. If not given, global naming convention will be used.
        set_as_active: Sets whether the found naming convention should be set as the active naming convention.

    Returns:
        NamingConvention or None: naming convention instance.
    """

    preset_manager = naming_preset_manager()
    if preset_manager is None:
        return None

    found_naming_conventions = preset_manager.find_naming_conventions_by_type(
        name
    )
    found_naming_convention = (
        found_naming_conventions[0] if found_naming_conventions else None
    )

    if found_naming_convention is not None and set_as_active:
        set_active_naming_convention(found_naming_convention)

    return found_naming_convention


def active_naming_convention() -> NamingConvention | None:
    """Returns current active naming convention.

    Returns:
        NamingConvention or None: active naming convention.
    """

    global _ACTIVE_NAMING_CONVENTION
    return _ACTIVE_NAMING_CONVENTION


def set_active_naming_convention(
    naming_convention_to_activate: NamingConvention | None,
):
    """Sets the active naming convention.

    Args:
        naming_convention_to_activate (NamingConvention): naming convention.
    """

    global _ACTIVE_NAMING_CONVENTION
    _ACTIVE_NAMING_CONVENTION = naming_convention_to_activate


def solve(
    *args,
    rule_name: str | None = None,
    naming_convention: NamingConvention | None = None,
    recursive: bool = True,
    **key_values,
) -> str:
    """Resolves the given rule expression using the given tokens as values.
    Each token value will be converted using naming convention token table. If a token or a token key-value
    does not exist, given value will be used instead.

    Args:
        rule_name (str or None): optional name of the rule to resolve. If None, active rule will be used to solve
            the name.
        naming_convention (NamingConvention or None): optional naming convention to use to solve the name. If not given,
            current active naming convention will be used.
        recursive (bool): whether solve will be used taking into consideration rules and tokens of the parent
            naming convention.

    Returns:
        str: resolved rule expression.

    Raises:
        RuntimeError: if no naming convention to solve name with is set/given.
    """

    _naming_convention = naming_convention or active_naming_convention()
    if _naming_convention is None:
        raise RuntimeError("No naming convention given to solve name")

    return _naming_convention.solve(
        *args, rule_name=rule_name, recursive=recursive, **key_values
    )


def parse(
    solved_name: str,
    naming_convention: NamingConvention | None = None,
    recursive: bool = True,
) -> dict[str, str]:
    """Parses given solved name taking into account all available rules within the naming convention.

    Args:
        solved_name (str): resolved name to get expression from.
        naming_convention (NamingConvention or None): optional naming convention to use to solve the name. If not given,
            current active naming convention will be used.
        recursive (bool): whether to iterate parent naming convention tokens recursively.

    Returns:
        dict[str, str]: dictionary containing each one of the solved name token keys and solved values.

    Raises:
        RuntimeError: if no naming convention to solve name with is set/given.
    """

    _naming_convention = naming_convention or active_naming_convention()
    if _naming_convention is None:
        raise RuntimeError("No naming convention given to solve name")

    return _naming_convention.parse(solved_name, recursive=recursive)


def parse_by_rule(
    solved_name: str,
    naming_convention: NamingConvention | None = None,
    rule_name: str | None = None,
    recursive: bool = True,
) -> dict[str, str]:
    """Parses given solved name taking into account all available rules within the naming convention.

    Args:
        solved_name (str): resolved name to get expression from.
        naming_convention (NamingConvention or None): optional naming convention to use to solve the name. If not given,
            current active naming convention will be used.
        recursive (bool): whether to iterate parent naming convention tokens recursively.

    Returns:
        dict[str, str]: dictionary containing each one of the solved name token keys and solved values.

    Raises:
        RuntimeError: if no naming convention to solve name with is set/given.
        RuntimeError: if rule with given name does not exist within naming convention.
    """

    _naming_convention = naming_convention or active_naming_convention()
    if _naming_convention is None:
        raise RuntimeError("No naming convention given to solve name")

    rule: Rule | None = None
    if rule_name:
        rule = _naming_convention.rule(rule_name, recursive=recursive)
        if rule is None:
            raise RuntimeError(
                f'No rule with "{rule_name}" found within naming convention {_naming_convention}'
            )

    if rule is not None:
        return _naming_convention.parse_by_rule(rule, solved_name)
    else:
        return _naming_convention.parse_by_active_rule(solved_name)
