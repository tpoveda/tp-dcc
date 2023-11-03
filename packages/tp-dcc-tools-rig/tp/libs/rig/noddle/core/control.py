from tp.core import dcc
from tp.libs.rig.noddle.abstract import control


if dcc.is_maya():
    from tp.libs.rig.noddle.maya.core import control as maya_control
    Control = maya_control.Control
else:
    Control = control.AbstractControl
