from __future__ import annotations

import typing
from typing import Iterable

if typing.TYPE_CHECKING:
    from ..base.rig import Rig
    from tp.libs.naming.manager import NameManager


def unique_name_for_rig(rigs: Iterable[Rig], name: str) -> str:
    """Generate a unique name for a rig ensuring it does not conflict with
    existing rig names. This function appends a numeric suffix to the given
    name if a conflict is found within the provided rigs.

    Notes:
        The numeric suffix is zero-padded to three digits for consistency.

    Args:
        rigs: A collection of Rig instances to verify against for name
            uniqueness.
        name: The base name to generate a unique name from.

    Returns:
        A unique name for the rig that avoids conflict with the names in the
            given rigs.
    """

    new_name = name
    current_names = [i.name() for i in rigs]
    index = 1
    while new_name in current_names:
        new_name = name + str(index).zfill(3)
        index += 1

    return new_name


def unique_name_for_module_by_rig(rig: Rig, name: str, side: str) -> str:
    """Generate a unique name for a module in the given rig based on the
    specified name and side.

    The function checks for existing module names in the rig and appends a
    numerical suffix to ensure uniqueness if necessary.

    Args:
        rig: The rig object containing existing modules.
        name: The base name to use for the module.
        side: The side designation (e.g., "left" or "right") for the module.

    Returns:
        A unique module name.
    """

    current_name = ":".join([name, side])
    current_names = [":".join([i.name(), i.side()]) for i in rig.iterate_modules()]
    index = 1
    while current_name in current_names:
        current_name = ":".join([name + str(index).zfill(3), side])
        index += 1

    return current_name.split(":")[0]


def compose_rig_names_for_layer(
    name_manager: NameManager, rig_name: str, layer_type: str
) -> tuple[str, str]:
    """Construct and return the hierarchy and meta-names for a specific rig
    layer type.

    This function uses the provided name manager to resolve the hierarchy and
    meta-names based on the given rig name and layer type. It constructs these
    names dynamically with predefined naming conventions.

    Args:
        name_manager: The `NameManager` object responsible for resolving
            hierarchical and meta-names based on specific naming conventions
            and rules.
        rig_name: The string representing the name of the rig for which the
            names are composed.
        layer_type: The string indicating the type of the layer for which the
            names are being resolved.

    Returns:
        A tuple containing the resolved hierarchy and meta-names.
    """

    layer_type = layer_type.replace("modRig", "")
    layer_type = layer_type[0].lower() + layer_type[1:]

    hierarchy_name = name_manager.resolve(
        "layerHrc", {"rigName": rig_name, "layerType": layer_type, "type": "hrc"}
    )
    meta_name = name_manager.resolve(
        "layerMeta", {"rigName": rig_name, "layerType": layer_type, "type": "meta"}
    )

    return hierarchy_name, meta_name


def compose_module_root_names(
    name_manager: NameManager, module_name: str, module_side: str
) -> tuple[str, str]:
    """Compose root names for a module's hierarchy and metadata.

    This function uses a `NameManager` to resolve and generate two different
    types of names for a given module: one for the hierarchy representation
    and one for the metadata representation.

    These names are useful for distinguishing between logical groupings of
    objects and their corresponding metadata in a module.

    Args:
        name_manager: A `NameManager` instance used to resolve and generate
            names.
        module_name: The name of the module for which the root names are being
            generated.
        module_side: The side (e.g., "left" or "right") of the module to help
            specify the naming context.

    Returns:
        A tuple containing two strings. The first string is the resolved name
            for the module's hierarchy ("moduleHrc"), and the second string is
            the resolved name for the module's metadata ("moduleMeta").
    """

    hierarchy_name = name_manager.resolve(
        "moduleHrc",
        {"moduleName": module_name, "side": module_side, "type": "hrc"},
    )
    meta_name = name_manager.resolve(
        "moduleMeta",
        {"moduleName": module_name, "side": module_side, "type": "meta"},
    )

    return hierarchy_name, meta_name


def compose_names_for_layer(
    name_manager: NameManager, module_name: str, module_side: str, layer_type: str
) -> tuple[str, str]:
    """Compose hierarchy and metadata layer names based on the given module
    details and layer type.

    This function uses the `NameManager` to resolve and generate names for
    a hierarchy layer and a metadata layer. The names are constructed using
    the provided module name, module side, and layer type properties.

    Args:
        name_manager: An instance of `NameManager` used for resolving and
            generating names.
        module_name: The name of the module base to be used in the naming.
        module_side: The side of the module (e.g., left, right) to include
            in the name construction.
        layer_type: The type of the layer (e.g., control, deform, rig),
            which determines the naming strategy.

    Returns:
        A tuple containing the resolved hierarchy layer name and metadata
            layer name, respectively.
    """

    hierarchy_name = name_manager.resolve(
        "layerHrc",
        {
            "moduleName": module_name,
            "side": module_side,
            "type": "hrc",
            "layerType": layer_type,
        },
    )
    meta_name = name_manager.resolve(
        "layerMeta",
        {
            "moduleName": module_name,
            "side": module_side,
            "type": "meta",
            "layerType": layer_type,
        },
    )

    return hierarchy_name, meta_name


def compose_container_name(
    name_manager: NameManager, module_name: str, module_side: str
) -> str:
    """Compose a standardized container name based on the provided module
    details and the naming conventions defined in the given name manager
    instance.

    This function uses a `NameManager` instance to generate a resolved name
    string by incorporating module-specific details, such as the module's
    name and side. The resulting string is assembled based on specific
    guidelines, ensuring a consistent naming pattern for containers within
    the intended context.

    Args:
        name_manager: The naming manager object that facilitates the
            generation of standardized name strings.
        module_name: The name of the module for which the container name is
            being composed.
        module_side: The side of the module (e.g., "left" or "right") to
            include in the container name.

    Returns:
        A resolved container name assembled using the `name_manager` and
            the provided module-specific details.
    """

    return name_manager.resolve(
        "containerName",
        {
            "moduleName": module_name,
            "side": module_side,
            "section": "root",
            "type": "container",
        },
    )


def compose_connectors_group_name(
    name_manager: NameManager, module_name: str, module_side: str
) -> str:
    """Compose and resolve the name for a connectors group based on the
    provided module name, its side, and a predefined naming convention.

    This function generates a structured naming string for a connectors group
    using the given arguments and the `NameManager` instance for resolution.

    Args:
        name_manager: An instance of `NameManager` used for resolving the final
            connectors group name.
        module_name: The name of the module for which the connectors group
            name is being generated.
        module_side: The side of the module (e.g., left, right) associated
            with the connectors group.

    Returns:
        A resolved string representing the name of the connectors group,
        following the specified format.
    """

    return name_manager.resolve(
        "connectorsGroup",
        {
            "moduleName": module_name,
            "side": module_side,
            "section": "root",
            "type": "connectorsGroup",
        },
    )
