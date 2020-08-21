from PySide2.QtWidgets import (
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
from .numpy_item_editor import NumPyEditor

class ValueColumnDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

        def _entered(index):
            item = parent.model().get_item(index)
            value = item.data(index.column())
            if isinstance(value, np.ndarray):
                parent.openPersistentEditor(index)

        print(parent)
        print(parent.entered)
        parent.setMouseTracking(True)
        parent.entered.connect(_entered)


        editor_factory = ValueColumnEditorFactory(parent)
        self.setItemEditorFactory(editor_factory)

    def paint(self, painter, option, index):
        if isinstance(index.data(), np.ndarray):
            btn = QPushButton("Load NumPy Array")
            #btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogListView))
            btn.setGeometry(option.rect)
            #btn->setText(index.data().toString());

            pixmap = QPixmap.grabWidget(btn)
            painter.drawPixmap(option.rect.x(),option.rect.y(), pixmap)
        else:
            super(ValueColumnDelegate, self).paint(painter, option, index)

    def createEditor(self, parent, option, index):
        model = self.parent().model()
        item = model.get_item(index)
        value = item.data(index.column())
        if isinstance(value, np.ndarray):
            print(value)
            print(parent)
            numpy_editor = NumPyEditor(parent, index)
            def _update_item(array):
                path = model.get_path_from_root(item, index.column())
                HexrdConfig().set_instrument_config_val(path, array)

            numpy_editor.array_changed.connect(_update_item)

            return numpy_editor
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
        # elif user_type == 1307:
        #     print('new editor')
        #     return QPushButton("Set NumPy Array", parent)


        return super().createEditor(user_type, parent)
