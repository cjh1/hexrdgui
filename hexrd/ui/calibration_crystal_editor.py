import copy
import numpy as np
from numpy.linalg import LinAlgError

from PySide2.QtCore import QObject, QSignalBlocker, Signal

from hexrd import matrixutil

from hexrd.ui.hexrd_config import HexrdConfig
from hexrd.ui.ui_loader import UiLoader
from hexrd.ui.utils import convert_angle_convention
from hexrd.ui.calibration_crystal_slider_widget import CalibrationCrystalSliderWidget


class CalibrationCrystalEditor(QObject):

    # Emitted when the params get modified
    params_modified = Signal()

    def __init__(self, params=None, parent=None):
        super().__init__(parent)

        loader = UiLoader()
        self.ui = loader.load_file('calibration_crystal_editor.ui', parent)

        self.params = params

        self.update_gui()
        self.update_orientation_suffixes()

        self.setup_connections()

        # Load slider widget
        slider_widget = CalibrationCrystalSliderWidget(self.ui)
        self.ui.slider_widget_parent.layout().addWidget(slider_widget.ui)
        self.ui.tab_widget.removeTab(2)  # remove deprecated sliders

    def setup_connections(self):
        HexrdConfig().euler_angle_convention_changed.connect(
            self.euler_angle_convention_changed)

        for w in self.all_widgets:
            w.valueChanged.connect(self.value_changed)

    @property
    def params(self):
        return self._params

    @params.setter
    def params(self, v):
        self._params = copy.deepcopy(v)
        self.update_gui()

    def value_changed(self):
        sender = self.sender()

        if sender in self.orientation_widgets:
            self.params[:3] = self.orientation
        elif sender in self.position_widgets:
            self.params[3:6] = self.position
        else:
            # If the stretch matrix was modified, we may need to update
            # a duplicate value in the matrix.
            self.update_duplicate(sender)
            try:
                self.params[6:] = self.inverse_stretch
            except LinAlgError as e:
                self.set_matrix_invalid(str(e))
                return

            self.set_matrix_valid()

        self.params_modified.emit()

    def euler_angle_convention_changed(self):
        self.update_gui()
        self.update_orientation_suffixes()

    def update_orientation_suffixes(self):
        suffix = '' if HexrdConfig().euler_angle_convention is None else '°'
        for w in self.orientation_widgets:
            w.setSuffix(suffix)

    def update_params(self):
        if self.params is None:
            return

        self.params[:3] = self.orientation
        self.params[3:6] = self.position
        self.params[6:] = self.inverse_stretch
        self.params_modified.emit()

    def update_gui(self):
        if self.params is None:
            return

        self.orientation = self.params[:3]
        self.position = self.params[3:6]
        self.inverse_stretch = self.params[6:]

    @property
    def stretch_matrix_duplicates(self):
        return {
            1: 3,
            2: 6,
            5: 7,
            7: 5,
            6: 2,
            3: 1
        }

    def update_duplicate(self, w):
        ind = int(w.objectName().replace('stretch_matrix_', ''))
        dup_ind = self.stretch_matrix_duplicates.get(ind)
        if dup_ind is not None:
            dup = getattr(self.ui, f'stretch_matrix_{dup_ind}')
            blocker = QSignalBlocker(dup)  # noqa: F841
            dup.setValue(w.value())

    def set_matrix_valid(self):
        self.set_matrix_style_sheet('background-color: white')
        self.set_matrix_tooltips('')

    def set_matrix_invalid(self, msg=''):
        self.set_matrix_style_sheet('background-color: red')
        self.set_matrix_tooltips(msg)

    def set_matrix_style_sheet(self, s):
        for w in self.stretch_matrix_widgets:
            w.setStyleSheet(s)

    def set_matrix_tooltips(self, s):
        for w in self.stretch_matrix_widgets:
            w.setToolTip(s)

    @staticmethod
    def convert_angle_convention(values, old_conv, new_conv):
        values[:] = convert_angle_convention(values, old_conv, new_conv)

    @property
    def orientation(self):
        # This automatically converts from Euler angle conventions
        values = [x.value() for x in self.orientation_widgets]
        if HexrdConfig().euler_angle_convention is not None:
            convention = HexrdConfig().euler_angle_convention
            self.convert_angle_convention(values, convention, None)

        return values

    @orientation.setter
    def orientation(self, v):
        # This automatically converts to Euler angle conventions
        if HexrdConfig().euler_angle_convention is not None:
            v = copy.deepcopy(v)
            convention = HexrdConfig().euler_angle_convention
            self.convert_angle_convention(v, None, convention)

        for i, w in enumerate(self.orientation_widgets):
            blocker = QSignalBlocker(w)  # noqa: F841
            w.setValue(v[i])

    @property
    def position(self):
        return [x.value() for x in self.position_widgets]

    @position.setter
    def position(self, v):
        for i, w in enumerate(self.position_widgets):
            blocker = QSignalBlocker(w)  # noqa: F841
            w.setValue(v[i])

    @property
    def inverse_stretch(self):
        m = np.array(self.stretch_matrix).reshape(3, 3)
        return matrixutil.symmToVecMV(np.linalg.inv(m), scale=True)

    @inverse_stretch.setter
    def inverse_stretch(self, v):
        m = matrixutil.vecMVToSymm(v, scale=True)
        self.stretch_matrix = np.linalg.inv(m).flatten()

    @property
    def stretch_matrix(self):
        return [x.value() for x in self.stretch_matrix_widgets]

    @stretch_matrix.setter
    def stretch_matrix(self, v):
        for i, w in enumerate(self.stretch_matrix_widgets):
            blocker = QSignalBlocker(w)  # noqa: F841
            w.setValue(v[i])

    @property
    def orientation_widgets(self):
        # Take advantage of the naming scheme
        return [getattr(self.ui, f'orientation_{i}') for i in range(3)]

    @property
    def position_widgets(self):
        # Take advantage of the naming scheme
        return [getattr(self.ui, f'position_{i}') for i in range(3)]

    @property
    def stretch_matrix_widgets(self):
        # Take advantage of the naming scheme
        return [getattr(self.ui, f'stretch_matrix_{i}') for i in range(9)]

    @property
    def all_widgets(self):
        return (
            self.orientation_widgets +
            self.position_widgets +
            self.stretch_matrix_widgets
        )
