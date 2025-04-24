# -*- coding: utf-8 -*-
# **************************************************************************
# Module to declare viewers
# Find documentation here: https://scipion-em.github.io/docs/docs/developer/creating-a-viewer
# **************************************************************************

from .viewer_data import *
from pwem.viewers.viewers_data import RegistryViewerConfig
from ..objects.data import *

labels = (
	'_pngDir _bis_type _hole_id _grid_id _selector_value _status _selected _shape_x _shape_y _sampligRate _number _area')


RegistryViewerConfig.registerConfig(SetOfHoles,
                                   {ORDER: labels,
                                   VISIBLE: labels,
                                    RENDER: '_pngDir'})