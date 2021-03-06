import copy
import numpy as np

from hexrd.unitcell import _StiffnessDict

from hexrd.ui.hexrd_config import HexrdConfig
from hexrd.ui.matrix_editor import MatrixEditor
from hexrd.ui.ui_loader import UiLoader
from hexrd.ui.utils import compose


class MaterialPropertiesEditor:

    stiffness_tensor_shape = (6, 6)

    def __init__(self, parent=None):
        loader = UiLoader()
        self.ui = loader.load_file('material_properties_editor.ui', parent)

        self.null_tensor = np.zeros(self.stiffness_tensor_shape)
        self.stiffness_tensor_editor = MatrixEditor(self.null_tensor, self.ui)
        self.ui.stiffness_tensor_editor_layout.addWidget(
            self.stiffness_tensor_editor)

        self.setup_connections()

        self.update_gui()

    def setup_connections(self):
        self.stiffness_tensor_editor.data_modified.connect(
            self.stiffness_tensor_edited)

    @property
    def material(self):
        return HexrdConfig().active_material

    def update_gui(self):
        material = self.material
        if hasattr(material.unitcell, 'stiffness'):
            data = copy.deepcopy(material.unitcell.stiffness)
        else:
            # Just use zeros...
            data = np.zeros(self.stiffness_tensor_shape)

        enabled, constraints = _StiffnessDict[material.unitcell._laueGroup]

        constraints_func = compose(apply_symmetric_constraint, constraints)

        editor = self.stiffness_tensor_editor
        editor.enabled_elements = enabled
        editor.apply_constraints_func = constraints_func
        editor.data = data

    def stiffness_tensor_edited(self):
        material = self.material
        material.unitcell.stiffness = copy.deepcopy(
            self.stiffness_tensor_editor.data)


def apply_symmetric_constraint(x):
    # Copy values from upper triangle to lower triangle.
    # Only works for square matrices.
    for i in range(x.shape[0]):
        for j in range(i):
            x[i, j] = x[j, i]
    return x
