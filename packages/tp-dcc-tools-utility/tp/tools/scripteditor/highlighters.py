from __future__ import annotations

from tp.common.qt import api as qt


def text_format(color: qt.QColor, style: str = '') -> qt.QTextCharFormat:
	"""
	Return a QTextCharFormat with the given attributes.
	"""

	_format = qt.QTextCharFormat()
	_format.setForeground(color)
	if 'bold' in style:
		_format.setFontWeight(qt.QFont.Bold)
	if 'italic' in style:
		_format.setFontItalic(True)

	return _format


# Syntax styles that can be shared by all languages
STYLES = {
	'keyword': text_format(qt.QColor('#cc7832'), 'bold'),
	# 'operator': format('red'),
	# 'brace': format('darkGray'),
	'defclass': text_format(qt.QColor('#cc7832')),
	'string': text_format(qt.QColor(255, 255, 0)),
	'string2': text_format(qt.QColor('#829755'), 'italic'),
	'comment': text_format(qt.QColor('#47802c')),
	'self': text_format(qt.QColor('#94558d')),
	'numbers': text_format(qt.QColor('#6897bb')),
}


class PythonHighlighter(qt.QSyntaxHighlighter):
	"""
	Syntax highlighter for the Python language
	"""

	KEYWORDS = [
		'and', 'assert', 'break', 'class', 'continue', 'def',
		'del', 'elif', 'else', 'except', 'exec', 'finally',
		'for', 'from', 'global', 'if', 'import', 'in',
		'is', 'lambda', 'not', 'or', 'pass', 'print',
		'raise', 'return', 'try', 'while', 'yield',
		'None', 'True', 'False',
	]

	OPERATORS = [
		'=',
		# Comparison
		'==', '!=', '<', '<=', '>', '>=',
		# Arithmetic
		'\+', '-', '\*', '/', '//', '\%', '\*\*',
		# In-place
		'\+=', '-=', '\*=', '/=', '\%=',
		# Bitwise
		'\^', '\|', '\&', '\~', '>>', '<<',
	]

	# Python braces
	BRACES = [
		'\{', '\}', '\(', '\)', '\[', '\]',
	]

	def __init__(self, parent: qt.QTextDocument | None = None):
		super(PythonHighlighter, self).__init__(parent)

		self._triple_quotes_within_strings = []

		# Multi-line strings (expression, flag, style)
		self.tri_single = (qt.QRegExp("'''"), 1, STYLES['string2'])
		self.tri_double = (qt.QRegExp('"""'), 2, STYLES['string2'])

		rules = []

		# Keyword, operator, and brace rules
		rules += [(r'\b%s\b' % w, 0, STYLES['keyword']) for w in PythonHighlighter.KEYWORDS]
		# rules += [(r'%s' % o, 0, STYLES['operator'])
		#           for o in PythonHighlighter.operators]
		# rules += [(r'%s' % b, 0, STYLES['brace'])
		#           for b in PythonHighlighter.braces]

		# All other rules
		rules += [
			# 'self'
			(r'\bself\b', 0, STYLES['self']),

			# 'def' followed by an identifier
			(r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
			# 'class' followed by an identifier
			(r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

			# Numeric literals
			(r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
			(r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
			(r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),

			# Double-quoted string, possibly containing escape sequences
			(r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
			# Single-quoted string, possibly containing escape sequences
			(r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

			# From '#' until a newline
			(r'#[^\n]*', 0, STYLES['comment']),
		]

		# Build a QRegExp for each pattern
		self.rules = [(qt.QRegExp(pat), index, fmt) for (pat, index, fmt) in rules]

	def highlightBlock(self, text: str):
		"""
		Apply syntax highlighting to the given block of text.
		"""

		self._triple_quotes_within_strings = []
		# Do other syntax formatting
		for expression, nth, _format in self.rules:
			index = expression.indexIn(text, 0)
			if index >= 0:
				# if there is a string we check
				# if there are some triple quotes within the string
				# they will be ignored if they are matched again
				if expression.pattern() in [r'"[^"\\]*(\\.[^"\\]*)*"', r"'[^'\\]*(\\.[^'\\]*)*'"]:
					inner_index = self.tri_single[0].indexIn(text, index + 1)
					if inner_index == -1:
						inner_index = self.tri_double[0].indexIn(text, index + 1)

					if inner_index != -1:
						triple_quote_indexes = range(inner_index, inner_index + 3)
						self._triple_quotes_within_strings.extend(triple_quote_indexes)

			while index >= 0:
				# skipping triple quotes within strings
				if index in self._triple_quotes_within_strings:
					index += 1
					expression.indexIn(text, index)
					continue

				# We actually want the index of the nth match
				index = expression.pos(nth)
				length = len(expression.cap(nth))
				self.setFormat(index, length, _format)
				index = expression.indexIn(text, index + length)

		self.setCurrentBlockState(0)

		# Do multi-line strings
		in_multiline = self._match_multiline(text, *self.tri_single)
		if not in_multiline:
			in_multiline = self._match_multiline(text, *self.tri_double)

	def _match_multiline(self, text: str, delimiter: qt.QRegExp, in_state: int, style: qt.QColor | int) -> bool:
		"""
		Do highlight of multi-line strings. ``delimiter`` should be a ``QRegExp`` for triple-single-quotes or
		triple-double-quotes, and ``in_state`` should be a unique integer to represent the corresponding state changes
		when inside those strings. Returns True if we're still inside a multi-line string when this function is finished.
		"""

		# If inside triple-single quotes, start at 0
		if self.previousBlockState() == in_state:
			start = 0
			add = 0
		# Otherwise, look for the delimiter on this line
		else:
			start = delimiter.indexIn(text)
			# skipping triple quotes within strings
			if start in self._triple_quotes_within_strings:
				return False
			# Move past this match
			add = delimiter.matchedLength()

		# As long as there's a delimiter match on this line...
		while start >= 0:
			# Look for the ending delimiter
			end = delimiter.indexIn(text, start + add)
			# Ending delimiter on this line?
			if end >= add:
				length = end - start + add + delimiter.matchedLength()
				self.setCurrentBlockState(0)
			# No; multi-line string
			else:
				self.setCurrentBlockState(in_state)
				length = len(text) - start + add
			# Apply formatting
			self.setFormat(start, length, style)
			# Look for the next match
			start = delimiter.indexIn(text, start + length)

		# Return True if still inside a multi-line string, False otherwise
		if self.currentBlockState() == in_state:
			return True
		else:
			return False


class JsonHighlighter(qt.QSyntaxHighlighter):
	"""
	Syntax highlighter for the JSON language
	"""

	class HighlightRule:
		def __init__(self, pattern: qt.QRegExp, char_format: qt.QTextCharFormat):
			self.pattern = pattern
			self.format = char_format

	def __init__(self, parent: qt.QTextDocument | None = None):
		super().__init__(parent)

		self._rules = list()

		# numeric value
		char_format = qt.QTextCharFormat()
		char_format.setForeground(qt.Qt.darkBlue)
		char_format.setFontWeight(qt.QFont.Bold)
		pattern = qt.QRegExp("([-0-9.]+)(?!([^\"]*\"[\\s]*\\:))")

		rule = JsonHighlighter.HighlightRule(pattern, char_format)
		self._rules.append(rule)

		# key
		char_format = qt.QTextCharFormat()
		pattern = qt.QRegExp("(\"[^\"]*\")\\s*\\:")
		char_format.setFontWeight(qt.QFont.Bold)

		rule = JsonHighlighter.HighlightRule(pattern, char_format)
		self._rules.append(rule)

		# value
		char_format = qt.QTextCharFormat()
		pattern = qt.QRegExp(":+(?:[: []*)(\"[^\"]*\")")
		char_format.setForeground(qt.Qt.darkGreen)

		rule = JsonHighlighter.HighlightRule(pattern, char_format)
		self._rules.append(rule)

	def highlightBlock(self, text: str):
		for rule in self._rules:
			# create a regular expression from the retrieved pattern
			expression = qt.QRegExp(rule.pattern)

			# check what index that expression occurs at with the ENTIRE text
			index = expression.indexIn(text)
			while index >= 0:
				# get the length of how long the expression is
				# set format from the start to the length with the text format
				length = expression.matchedLength()
				self.setFormat(index, length, rule.format)

				# set index to where the expression ends in the text
				index = expression.indexIn(text, index + length)
