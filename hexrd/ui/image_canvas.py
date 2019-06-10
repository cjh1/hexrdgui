import math
import os

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import fabio

import hexrd.ui.constants

class ImageCanvas(FigureCanvas):

    def __init__(self, parent=None, image_files=None):
        self.figure = Figure()
        super(ImageCanvas, self).__init__(self.figure)

        self.axes_images = []
        self.cmap = hexrd.ui.constants.DEFAULT_CMAP

        if image_files is not None:
            self.load_images(image_files)

    def __del__(self):
        # This is so that the figure can be cleaned up
        plt.close(self.figure)

    def load_images(self, image_files):
        self.figure.clear()
        self.axes_images.clear()

        cols = 1
        if len(image_files) > 1:
            cols = 2

        rows = math.ceil(len(image_files) / cols)

        for i, file in enumerate(image_files):
            img = fabio.open(file).data

            axis = self.figure.add_subplot(rows, cols, i + 1)
            axis.set_title(os.path.basename(file))
            self.axes_images.append(axis.imshow(img, cmap=self.cmap))

        self.figure.tight_layout()
        self.draw()

    def set_cmap(self, cmap):
        self.cmap = cmap
        for axes_image in self.axes_images:
            axes_image.set_cmap(cmap)
        self.draw()

    def set_norm(self, norm):
        self.norm = norm
        for axes_image in self.axes_images:
            axes_image.set_norm(norm)
        self.draw()

    def get_min_max(self):
        minimum = 1e10
        maximum = 0
        for axes_image in self.axes_images:
            minimum = min(minimum, axes_image.get_array().min())
            maximum = max(maximum, axes_image.get_array().max())

        return minimum, maximum

def main():
    import sys
    from PySide2.QtWidgets import QApplication

    app = QApplication(sys.argv)

    image_files = ['0.tiff', '1.tiff', '2.tiff', '3.tiff']

    images = ImageCanvas(image_files=image_files)
    images.show()

    # start event processing
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
