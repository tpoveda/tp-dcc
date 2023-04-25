import os
import sys

# register environment variables
os.environ['TPDCC_ENV_DEV'] = 'True'
os.environ['TPDCC_TOOLS_ROOT'] = r'E:\tools\dev\tp-dcc\packages\tp-dcc-bootstrap'
os.environ['TPDCC_DEPS_ROOT'] = r'E:\tools\dev\tp-dcc\venv3\Lib\site-packages'

# make sure to update sys.path so tpDcc Tools package manager an dependencies are available
root_path = os.environ['TPDCC_TOOLS_ROOT']
if os.path.isdir(root_path) and root_path not in sys.path:
    sys.path.append(root_path)
    
def reload_modules():
    """
    Function that forces the reloading of all related modules
    """

    modules_to_reload = ('tp')
    for k in sys.modules.copy().keys():
        found = False
        for mod in modules_to_reload:
            if mod == k:
                del sys.modules[mod]
                found = True
                break
        if found:
            continue
        if k.startswith(modules_to_reload):
            del sys.modules[k]
            
import tp.bootstrap
try:
    tp.bootstrap.shutdown()
except Exception: 
    pass
reload_modules()

# register environment variables after shutdown
os.environ['TPDCC_DEV'] = 'False'

# load framework
import tp.bootstrap
tp.bootstrap.init()
