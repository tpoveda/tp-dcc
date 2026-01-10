"""MetaHuman Body Rig Controls - Maya Command Line Entry Point.

This script provides a simple entry point to build MetaHuman body rig controls.

Usage in Maya:
    import tp.tools.metahuman.rig as mh_rig

    # Build with motion skeleton (for animation)
    result = mh_rig.build_metahuman_body_rig(motion=True)

    # Or build without motion skeleton
    result = mh_rig.build_metahuman_body_rig(motion=False)

    # Check result
    if result.success:
        print("Rig built successfully!")
    else:
        print(f"Build failed: {result.message}")

Alternative usage:
    from tp.tools.metahuman.rig import MetaHumanBodyRigBuilder

    builder = MetaHumanBodyRigBuilder(motion=True)
    result = builder.build()
"""

from __future__ import annotations

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(motion: bool = True) -> None:
    """Main entry point for building MetaHuman body rig.

    Args:
        motion: If True, create motion skeleton for animation.
    """
    try:
        from tp.tools.metahuman.rig import build_metahuman_body_rig

        result = build_metahuman_body_rig(motion=motion)

        if result.success:
            logger.info(result.message)
        else:
            logger.error(result.message)

    except ImportError as e:
        logger.error(f"Failed to import rig module: {e}")
        raise


if __name__ == "__main__":
    main(motion=True)
