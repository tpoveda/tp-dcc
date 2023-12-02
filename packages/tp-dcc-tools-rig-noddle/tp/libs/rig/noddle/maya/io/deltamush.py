from __future__ import annotations


from tp.libs.rig.noddle.maya.io import abstract


class DeltaMushManager(abstract.AbstractIOManager):

    DATA_TYPE = 'deltaMush'
    EXTENSION = 'json'

    @classmethod
    def import_all(cls):
        pass
