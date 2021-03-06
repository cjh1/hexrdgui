import numpy as np

from PySide2.QtCore import QSignalBlocker, Signal
from PySide2.QtWidgets import QGridLayout, QWidget

from hexrd.ui.scientificspinbox import ScientificDoubleSpinBox


class MatrixEditor(QWidget):

    data_modified = Signal()

    def __init__(self, data, parent=None):
        super().__init__(parent)

        self._data = data

        # If this is not None, then only the elements present in the
        # list (as (i, j) items) will be enabled.
        self._enabled_elements = None

        # If this is set, it will be called every time the data updates
        # to apply equality constraints.
        self._apply_constraints_func = None

        self.setLayout(QGridLayout())
        self.add_spin_boxes()
        self.update_gui()

    def add_spin_boxes(self):
        layout = self.layout()
        for i in range(self.rows):
            for j in range(self.cols):
                sb = self.create_spin_box()
                layout.addWidget(sb, i, j)

    def create_spin_box(self):
        sb = ScientificDoubleSpinBox()
        sb.setKeyboardTracking(False)
        sb.valueChanged.connect(self.element_modified)
        return sb

    def element_modified(self):
        self.update_data()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, v):
        if not np.array_equal(self._data, v):
            if self._data.shape != v.shape:
                msg = (f'Shape {v.shape} does not match original shape '
                       f'{self._data.shape}')
                raise AttributeError(msg)

            self._data = v
            self.apply_constraints()
            self.update_gui()

    @property
    def rows(self):
        return self.data.shape[0]

    @property
    def cols(self):
        return self.data.shape[1]

    def update_data(self):
        self.data[:] = self.gui_data
        self.apply_constraints()
        self.data_modified.emit()

    def update_gui(self):
        self.gui_data = self.data

    @property
    def gui_data(self):
        row_range = range(self.rows)
        col_range = range(self.cols)
        return [[self.gui_value(i, j) for j in col_range] for i in row_range]

    @gui_data.setter
    def gui_data(self, v):
        blockers = [QSignalBlocker(w) for w in self.all_widgets]  # noqa: F841
        for i in range(self.rows):
            for j in range(self.cols):
                self.set_gui_value(i, j, v[i][j])

    @property
    def all_widgets(self):
        row_range = range(self.rows)
        col_range = range(self.cols)
        return [self.widget(i, j) for j in col_range for i in row_range]

    def widget(self, row, col):
        return self.layout().itemAtPosition(row, col).widget()

    def gui_value(self, row, col):
        return self.widget(row, col).value()

    def set_gui_value(self, row, col, val):
        self.widget(row, col).setValue(val)

    def update_enable_states(self):
        enable_all = self.enabled_elements is None
        for i in range(self.rows):
            for j in range(self.cols):
                enable = enable_all or (i, j) in self.enabled_elements
                self.widget(i, j).setEnabled(enable)

    @property
    def enabled_elements(self):
        return self._enabled_elements

    @enabled_elements.setter
    def enabled_elements(self, v):
        if self._enabled_elements != v:
            self._enabled_elements = v
            self.update_enable_states()

    @property
    def apply_constraints_func(self):
        return self._apply_constraints_func

    @apply_constraints_func.setter
    def apply_constraints_func(self, v):
        if self._apply_constraints_func != v:
            self._apply_constraints_func = v
            self.apply_constraints()

    def apply_constraints(self):
        func = self.apply_constraints_func
        if func is None:
            return

        func(self.data)
        self.update_gui()


if __name__ == '__main__':
    import sys

    from PySide2.QtWidgets import QApplication, QDialog, QVBoxLayout

    if len(sys.argv) < 2:
        sys.exit('Usage: <script> <matrix_size>')

    rows, cols = [int(x) for x in sys.argv[1].split('x')]
    data = np.ones((rows, cols))

    app = QApplication(sys.argv)
    dialog = QDialog()
    layout = QVBoxLayout()

    dialog.setLayout(layout)
    editor = MatrixEditor(data)
    layout.addWidget(editor)

    # def constraints(x):
    #     x[2][2] = x[1][1]

    # editor.enabled_elements = [(1, 1), (3, 4)]
    # editor.apply_constraints_func = constraints

    def on_data_modified():
        print(f'Data modified: {editor.data}')

    editor.data_modified.connect(on_data_modified)
    dialog.finished.connect(app.quit)
    dialog.show()

    app.exec_()
