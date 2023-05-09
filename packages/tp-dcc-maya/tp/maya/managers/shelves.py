class ShelvesManager:
	"""
	Class that handles tp-dcc-tools Shelve creation for Maya
	"""

	def __init__(self):
		super().__init__()

		self._shelves = list()					# type list[Shelf]
		self._original_shelf = list()			# type: list[dict]
