#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Helper utility methods related with time in Maya
"""

from collections import OrderedDict

import maya.cmds
import maya.OpenMaya

time_unit_to_fps = OrderedDict()
for k, v in (
        ('game', 15), ('film', 24), ('pal', 25), ('ntsc', 30), ('show', 48), ('palf', 50), ('ntscf', 60),
        ('millisec', 1000),
        ('sec', 1), ('min', 1 / 60.0), ('hour', 1 / 3600.0)):
    time_unit_to_fps.update({k: v})
for val in (2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 40, 75, 80, 100, 120, 125, 150,
            200, 240, 250, 300, 375, 400, 500, 600, 750, 1200, 1500, 2000, 3000, 6000):
    time_unit_to_fps.update({'{}fps'.format(val): val})

time_unit_to_const = dict([(v, i) for i, v in time_unit_to_fps.items()])

# This is used because OpenMaya.MTime doesnt't default to the current fps setting
fps_to_mtime = OrderedDict()
fps_to_mtime.update({'hour': maya.OpenMaya.MTime.kHours})
fps_to_mtime.update({'min': maya.OpenMaya.MTime.kMinutes})
fps_to_mtime.update({'sec': maya.OpenMaya.MTime.kSeconds})  # 1 fps
fps_to_mtime.update({'2fps': maya.OpenMaya.MTime.k2FPS})
fps_to_mtime.update({'3fps': maya.OpenMaya.MTime.k3FPS})
fps_to_mtime.update({'4fps': maya.OpenMaya.MTime.k4FPS})
fps_to_mtime.update({'5fps': maya.OpenMaya.MTime.k5FPS})
fps_to_mtime.update({'6fps': maya.OpenMaya.MTime.k6FPS})
fps_to_mtime.update({'8fps': maya.OpenMaya.MTime.k8FPS})
fps_to_mtime.update({'10fps': maya.OpenMaya.MTime.k10FPS})
fps_to_mtime.update({'12fps': maya.OpenMaya.MTime.k12FPS})
fps_to_mtime.update({'game': maya.OpenMaya.MTime.kGames})  # 15 FPS
fps_to_mtime.update({'16fps': maya.OpenMaya.MTime.k16FPS})
fps_to_mtime.update({'20fps': maya.OpenMaya.MTime.k20FPS})
fps_to_mtime.update({'film': maya.OpenMaya.MTime.kFilm})  # 24 fps
fps_to_mtime.update({'pal': maya.OpenMaya.MTime.kPALFrame})  # 25 fps
fps_to_mtime.update({'ntsc': maya.OpenMaya.MTime.kNTSCFrame})  # 30 fps
fps_to_mtime.update({'40fps': maya.OpenMaya.MTime.k40FPS})
fps_to_mtime.update({'show': maya.OpenMaya.MTime.kShowScan})  # 48 fps
fps_to_mtime.update({'palf': maya.OpenMaya.MTime.kPALField})  # # 50 fps
fps_to_mtime.update({'ntscf': maya.OpenMaya.MTime.kNTSCField})  # 60 fps
fps_to_mtime.update({'75fps': maya.OpenMaya.MTime.k75FPS})
fps_to_mtime.update({'80fps': maya.OpenMaya.MTime.k80FPS})
fps_to_mtime.update({'100fps': maya.OpenMaya.MTime.k100FPS})
fps_to_mtime.update({'120fps': maya.OpenMaya.MTime.k120FPS})
fps_to_mtime.update({'125fps': maya.OpenMaya.MTime.k125FPS})
fps_to_mtime.update({'150fps': maya.OpenMaya.MTime.k150FPS})
fps_to_mtime.update({'200fps': maya.OpenMaya.MTime.k200FPS})
fps_to_mtime.update({'240fps': maya.OpenMaya.MTime.k240FPS})
fps_to_mtime.update({'250fps': maya.OpenMaya.MTime.k250FPS})
fps_to_mtime.update({'300fps': maya.OpenMaya.MTime.k300FPS})
fps_to_mtime.update({'375fps': maya.OpenMaya.MTime.k375FPS})
fps_to_mtime.update({'400fps': maya.OpenMaya.MTime.k400FPS})
fps_to_mtime.update({'500fps': maya.OpenMaya.MTime.k500FPS})
fps_to_mtime.update({'600fps': maya.OpenMaya.MTime.k600FPS})
fps_to_mtime.update({'750fps': maya.OpenMaya.MTime.k750FPS})
fps_to_mtime.update({'millisec': maya.OpenMaya.MTime.kMilliseconds})  # 1000 fps
fps_to_mtime.update({'1200fps': maya.OpenMaya.MTime.k1200FPS})
fps_to_mtime.update({'1500fps': maya.OpenMaya.MTime.k1500FPS})
fps_to_mtime.update({'2000fps': maya.OpenMaya.MTime.k2000FPS})
fps_to_mtime.update({'3000fps': maya.OpenMaya.MTime.k3000FPS})
fps_to_mtime.update({'6000fps': maya.OpenMaya.MTime.k6000FPS})


def current_time_unit():
    """
    Returns the current time unit name.
    :return: str, name of the current fps
    """

    return maya.cmds.currentUnit(query=True, time=True)
