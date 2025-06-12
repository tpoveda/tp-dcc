# tp-dcc Framework

[![Python 3.11](https://img.shields.io/badge/Python-3.11-yellow?logo=python)](https://www.python.org/)
[![Windows](https://img.shields.io/badge/Windows-blue?logo=windows)](https://www.python.org/)
[![Code Style: PEP8](https://img.shields.io/badge/code_style-pep8-blue)](https://www.python.org/dev/peps/pep-0008/)
[![Maya 2026](https://img.shields.io/badge/Maya-2026-green?logo=autodesk)](https://www.autodesk.com/)
[![3ds Max 2026](https://img.shields.io/badge/3dsMax-2026-orange?logo=autodesk)](https://www.autodesk.com/)
[![MotionBuilder 2026](https://img.shields.io/badge/MoBu-2026-pink?logo=autodesk)](https://www.autodesk.com/)
[![Unreal Engine 5](https://img.shields.io/static/v1?message=UE5&color=000000&logo=unrealengine&logoColor=white&label=)](https://www.unreal.com/)
[![Houdini](https://img.shields.io/static/v1?message=Houdini&color=FF4713&logo=Houdini&logoColor=FFFFFF&label=)](https://www.houdini.com/)

---

# Development Setup

See to setup development environment: [Development Setup](./dev/README.md)

## Startup Code

```python
import os
import sys
import site

os.environ['TP_DCC_PIPELINE_ROOT_DIRECTORY'] = r'E:\tools\dev\tp-dcc'

# This should point to the site-packages of the virtual environment for the
# specific DCC application you are working with, e.g., Maya 2026, MoBu 2026, etc.
os.environ['TP_DCC_PIPELINE_SITE_PACKAGES'] = r'E:\tools\dev\tp-dcc\envs\maya2026\Lib\site-packages'

site.addsitedir(os.environ['TP_DCC_PIPELINE_SITE_PACKAGES'])

try:
    pkm.shutdown()
except Exception:
    pass
from tp import bootstrap
pkm = bootstrap.init()
```


> This code will initialize TP DCC bootstrap and will load all the packages.
After the first run, the call to `pkm.shutdown()` will ensure all the packages
are properly unloaded and related code is reloaded to streamline development 
workflow.

---