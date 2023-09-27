# **************************************************************************
# *
# * Authors: Daniel Marchan (da.marchan@cnb.csic.es)
#            Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)
# *
# *
# * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA
# * 02111-1307  USA
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************


from pwem.viewers.viewers_data import DataViewer
#from ..objects.data_deprecated import *
from ..objects.data import *
from pwem.viewers import DataView, ObjectView
from pwem.viewers.showj import ORDER, VISIBLE, MODE, RENDER, MODE_MD, ZOOM
from pwem.viewers.showj import *

# class DataViewer_cnb(DataViewer):
#     _targets = [SetOfLowMagImages]
#
#     def _visualize(self, obj, **kwargs):
#         self._views.append(DataView(obj.getFileName()))
#         return self._views
#

class DataViewer_smartscope(DataViewer):
    _targets = [SetOfGrids, SetOfAtlas, SetOfSquares, SetOfHoles, SetOfMoviesSS]

    def _visualize(self, obj, **kwargs):
        if isinstance(obj, SetOfSquares):
            labels = ('_pngDir _square_id _atlas_id _status _selected _completion_time _area _shape_x _shape_y _sampligRate')
            self._views.append(ObjectView(self._project,
                                           obj.strId(),
                                           obj.getFileName(),
                               viewParams={VISIBLE: labels,
                                           RENDER: '_pngDir',
                                           SORT_BY: labels}))
        elif isinstance(obj, SetOfAtlas):
            labels = ('_pngDir _grid_id _atlas_id _binning_factor _status _completion_time _shape_x _shape_y _sampligRate')
            self._views.append(ObjectView(self._project,
                                           obj.strId(),
                                           obj.getFileName(),
                               viewParams={VISIBLE: labels,
                                           RENDER: '_pngDir',
                                           SORT_BY: labels}))
        elif isinstance(obj, SetOfGrids):
            labels = ('_grid_id _status _position _hole_angle _mesh_angle _quality _status _start_time _last_update _mesh_size mesh_material _hole_type')
            self._views.append(ObjectView(self._project,
                                           obj.strId(),
                                           obj.getFileName(),
                               viewParams={VISIBLE: labels,
                                           SORT_BY: labels}))
        elif isinstance(obj, SetOfHoles):
            labels = ('_pngDir _hole_id _grid_id _status _selected _completion_time _shape_x _shape_y _sampligRate _number _area')
            self._views.append(ObjectView(self._project,
                                           obj.strId(),
                                           obj.getFileName(),
                               viewParams={VISIBLE: labels,
                                           RENDER: '_pngDir',
                                           SORT_BY: labels}))
        elif isinstance(obj, SetOfMoviesSS):
            labels = ('_micName _hm_id _hole_id _status _completion_time _samplingRate _shape_x _shape_y')
            self._views.append(ObjectView(self._project,
                                           obj.strId(),
                                           obj.getFileName(),
                               viewParams={VISIBLE: labels,
                                           MODE: MODE_MD,
                                           SORT_BY: labels}))
        else:
            self._views.append(DataView(obj.getFileName()))
        return self._views
