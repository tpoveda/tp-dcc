from tp.common.nodegraph.core import node


class DropdownMenuNode(node.BaseNode):

	__identifier__ = 'nodes.widget'
	NODE_NAME = 'menu'

	def __init__(self):
		super(DropdownMenuNode, self).__init__()

		self.add_input('in 1')
		self.add_output('out 1')
		self.add_output('out 2')

		items = ['item 1', 'item 2', 'item 3']
		self.add_combo_menu('my_menu', 'Menu Test', items=items)


class TextInputNode(node.BaseNode):

	__identifier__ = 'nodes.widget'
	NODE_NAME = 'text input'

	def __init__(self):
		super(TextInputNode, self).__init__()

		self.add_input('in')
		self.add_output('out')

		self.add_text_input('my_input', 'Text Input', tab='widgets')


class CheckboxNode(node.BaseNode):

	__identifier__ = 'nodes.widget'
	NODE_NAME = 'checkbox'

	def __init__(self):
		super(CheckboxNode, self).__init__()

		self.add_input('in', color=(200, 100, 0))
		self.add_output('out', color=(0, 100, 200))

		self.add_checkbox('cb_1', '', 'Checkbox 1', True)
		self.add_checkbox('cb_2', '', 'Checkbox 2', True)
