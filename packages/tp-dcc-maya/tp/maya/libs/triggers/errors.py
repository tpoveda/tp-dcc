class NodeHasExistingCommandError(Exception):
	pass


class NodeHasExistingTriggerError(Exception):
	pass


class MissingRegisteredCommandOnNodeError(Exception):
	pass


class InvalidMarkingMenuFileFormatError(Exception):
	pass


class MissingMarkingMenu(Exception):
	pass
