class CritError(Exception):

	MSG = ''

	def __init__(self, msg: str = '', *args, **kwargs):
		msg = self.MSG.format(msg)
		super().__init__(msg, *args)


class CritRigDuplicationError(CritError):

	MSG = 'Duplicated rigs in the scene, please use namespace filtering: {}'

	def __init__(self, dupes, *args, **kwargs):
		super().__init__(dupes, *args, **kwargs)
