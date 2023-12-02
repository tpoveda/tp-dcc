from __future__ import annotations


from tp.libs.rig.noddle.maya.io import abstract


class PsdManager(abstract.AbstractIOManager):

    DATA_TYPE = 'psd'
    EXTENSION = 'pose'

    @classmethod
    def import_all(cls):
        pass
