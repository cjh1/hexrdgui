import copy
import numpy as np

from skimage.draw import polygon

from hexrd.ui import constants
from hexrd.ui.create_hedm_instrument import create_hedm_instrument
from hexrd.ui.hexrd_config import HexrdConfig


def apply_threshold_mask(imageseries):
    comparison = HexrdConfig().threshold_comparison
    value = HexrdConfig().threshold_value
    for det in HexrdConfig().detector_names:
        ims = imageseries[det]
        masked_ims = [None for i in range(len(ims))]
        for idx in range(len(ims)):
            img = copy.copy(ims[idx])
            masked_img, mask = _create_threshold_mask(img, comparison, value)
            masked_ims[idx] = masked_img
            HexrdConfig().set_threshold_mask(mask)
        HexrdConfig().imageseries_dict[det] = masked_ims


def remove_threshold_mask(ims_dict_copy):
    HexrdConfig().imageseries_dict = copy.copy(ims_dict_copy)


def _create_threshold_mask(img, comparison, value):
    mask = np.ones(img.shape, dtype=bool)
    if comparison == constants.UI_THRESHOLD_LESS_THAN:
        mask = (img < value)
    elif comparison == constants.UI_THRESHOLD_GREATER_THAN:
        mask = (img > value)
    elif comparison == constants.UI_THRESHOLD_EQUAL_TO:
        mask = (img == value)
    img[mask] = 0
    return img, mask


def convert_polar_to_raw(line):
    line_data = []
    for key, panel in create_hedm_instrument().detectors.items():
        cart = panel.angles_to_cart(np.radians(line))
        raw = panel.cartToPixel(cart)
        line_data.append((key, raw))
    return line_data


def create_raw_mask(name, line_data):
    for line in line_data:
        det, data = line
        img = HexrdConfig().image(det, 0)
        rr, cc = polygon(data[:, 1], data[:, 0], shape=img.shape)
        if len(rr) >= 1:
            mask = np.ones(img.shape, dtype=bool)
            mask[rr, cc] = False
            HexrdConfig().raw_masks[name] = (det, mask)
