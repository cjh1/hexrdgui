from PySide2.QtWidgets import (
    QWidget,
    QStyledItemDelegate,
    QItemEditorFactory,
    QPushButton,
    QStyle,
    QFileDialog
)
from PySide2.QtGui import QPixmap

import numpy as np

from hexrd.ui.scientificspinbox import ScientificDoubleSpinBox
from hexrd.ui.hexrd_config import HexrdConfig
from hexrd.ui.calibration.panel_buffer_dialog import PanelBufferDialog
from hexrd.ui.tree_views.base_tree_item_model import BaseTreeItemModel

BUTTON_LABEL = 'Configure Panel Buffer'
BUFFER_KEY = 'buffer'

class ValueColumnDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.btn = QPushButton(BUTTON_LABEL)

        def _entered(index):
            item = parent.model().get_item(index)
            key = item.data(BaseTreeItemModel.KEY_COL)
            if key == BUFFER_KEY:
                parent.openPersistentEditor(index)

        parent.setMouseTracking(True)
        parent.entered.connect(_entered)

        editor_factory = ValueColumnEditorFactory(parent)
        self.setItemEditorFactory(editor_factory)

    def paint(self, painter, option, index):
        item = self.parent().model().get_item(index)
        key = item.data(BaseTreeItemModel.KEY_COL)
        if key == BUFFER_KEY:
            self.btn.setGeometry(option.rect)

            pixmap = QWidget.grab(self.btn)
            painter.drawPixmap(option.rect.x(),option.rect.y(), pixmap)
        else:
            super(ValueColumnDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        model = self.parent().model()
        item = model.get_item(index)
        key = item.data(BaseTreeItemModel.KEY_COL)
        if key == BUFFER_KEY:
            edit_btn = QPushButton(BUTTON_LABEL, parent)
            def _clicked():
                path = model.get_path_from_root(item, index.column())
                detector = path[path.index('detectors') + 1]
                dialog = PanelBufferDialog(detector, self)
                dialog.show()

            edit_btn.clicked.connect(_clicked)

            return edit_btn
        else:
            return super(ValueColumnDelegate, self).createEditor(parent, option, index)


class ValueColumnEditorFactory(QItemEditorFactory):
    def __init__(self, parent=None):
        super().__init__(self, parent)

    def createEditor(self, user_type, parent):
        # Normally in Qt, we'd use QVariant (like QVariant::Double) to compare
        # with the user_type integer. However, QVariant is not available in
        # PySide2, making us use roundabout methods to get the integer like
        # below.
        float_type = (
            ScientificDoubleSpinBox.staticMetaObject.userProperty().userType()
        )
        if user_type == float_type:
            return ScientificDoubleSpinBox(parent)

        return super().createEditor(user_type, parent)
