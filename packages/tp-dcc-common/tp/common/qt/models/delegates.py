from overrides import override
from Qt.QtCore import Qt, QRectF, QSize, QModelIndex
from Qt.QtWidgets import QApplication, QStyle, QStyledItemDelegate, QStyleOptionViewItem
from Qt.QtGui import QFontMetrics, QColor, QPainter, QTextOption, QTextCursor, QTextDocument

from tp.common.qt.models import consts


def paint_html(delegate: QStyledItemDelegate, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
	"""
	Paints given HTML delegate.

	:param QStyledItemDelegate delegate: delegate to paint.
	:param QPainter painter: painter received from delegate paint function.
	:param QStyleOptionViewItem option: option received from delegate paint function
	:param index index: model index received from delegate paint function
	:return: True if the paint operation was successful; False otherwise.
	:rtype: bool
	"""

	delegate.initStyleOption(option, index)
	if not option.text:
		return False

	model = index.model()
	text_color = model.data(index, Qt.ForegroundRole)
	text_margin = model.data(index, consts.textMarginRole)
	text_option = QTextOption()
	text_option.setWrapMode(QTextOption.WordWrap if QStyleOptionViewItem.WrapText else QTextOption.ManualWrap)
	text_option.setTextDirection(option.direction)
	doc = QTextDocument()
	doc.setDefaultTextOption(text_option)
	doc.setHtml('<font color=\"{}\">{}</font>'.format(text_color.name(QColor.HexRgb), option.text))
	doc.setDefaultFont(option.font)
	doc.setDocumentMargin(text_margin)
	doc.setTextWidth(option.rect.width())
	doc.adjustSize()
	if doc.size().width() > option.rect.width():
		# Elide text
		cursor = QTextCursor(doc)
		cursor.movePosition(QTextCursor.End)
		elided_postfix = '...'
		metric = QFontMetrics(option.font)
		postfix_width = metric.horizontalAdvance(elided_postfix)
		while doc.size().width() > option.rect.width() - postfix_width:
			cursor.deletePreviousChar()
			doc.adjustSize()
		cursor.insertText(elided_postfix)

	style = option.widget.style() if option.widget else QApplication.style()
	option.text = ""
	style.drawControl(QStyle.CE_ItemViewItem, option, painter, option.widget)

	# Figure out where to render the text in order to follow the requested alignment
	text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, option)
	document_size = QSize(int(doc.size().width()), int(doc.size().height()))
	layout_rect = QStyle.alignedRect(Qt.LayoutDirectionAuto, option.displayAlignment, document_size, text_rect)

	painter.save()

	try:
		# Translate the painter to the origin of the layout rectangle in order for the text to be
		# rendered at the correct position
		painter.translate(layout_rect.topLeft())
		doc.drawContents(painter, QRectF(text_rect.translated(-text_rect.topLeft())))
	finally:
		painter.restore()

	return True


class HtmlDelegate(QStyledItemDelegate):

	@override
	def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
		if not paint_html(self, painter, option, index):
			return super().paint(painter, option, index)

	@override
	def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
		self.initStyleOption(option, index)
		if not option.text:
			return super().sizeHint(option, index)

		model = index.model()
		text_margin = model.data(index, consts.textMarginRole)
		if not text_margin:
			return super().sizeHint(option, index)

		doc = QTextDocument()
		doc.setHtml(option.text)
		doc.setDefaultFont(option.font)
		doc.setDocumentMargin(text_margin)

		return QSize(int(doc.idealWidth()), int(doc.size().height()))
