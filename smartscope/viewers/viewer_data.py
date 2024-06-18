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
from pwem.viewers import DataView, ObjectView, EmPlotter
from pwem.viewers.showj import ORDER, VISIBLE, MODE, RENDER, MODE_MD, ZOOM, SORT_BY
from pwem.viewers.showj import *
from pyworkflow.viewer import DESKTOP_TKINTER, WEB_DJANGO, ProtocolViewer
from smartscope.protocols.protocol_feedback_filter import smartscopeFeedbackFilter
from pyworkflow.protocol.params import IntParam, LabelParam

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

class SmartscopeFilterFeedbackViewer(ProtocolViewer):
    """

    """
    _label = 'viewer feedback holes filter'
    _environments = [DESKTOP_TKINTER, WEB_DJANGO]
    _targets = [smartscopeFeedbackFilter]

    def _defineParams(self, form):
        form.addSection(label='Visualization')
        group = form.addGroup('Holes')
        group.addParam('visualizeAllHoles', LabelParam,
                       label="Visualize all holes",
                       help="")
        group.addParam('visualizeFilteredHoles', LabelParam,
                       label="Visualize filtered holes",
                       help="")
        group2 = form.addGroup('Statistics')
        group2.addParam('visualizeHistograms', LabelParam,
                       label="Visualize the histograms of intensity",
                       help="Visualize the histograms of intensity per holes")


    def _getVisualizeDict(self):
        return {
                 'visualizeAllHoles': self._visualizeAllHoles,
                 'visualizeFilteredHoles': self._visualizeFilteredHoles,
                 'visualizeHistograms': self._visualizeHistograms,
                }

    def _visualizeAllHoles(self, e=None):
        return self._visualizeHoles("SetOfHoles")

    def _visualizeFilteredHoles(self, e=None):
        return self._visualizeHoles("SetOfHoles")

    def _visualizeHoles(self, obj):
        labels = (
            '_pngDir _hole_id _grid_id _status _selected _completion_time _shape_x _shape_y _sampligRate _number _area')
        self._views.append(ObjectView(self._project,
                                      obj.strId(),
                                      obj.getFileName(),
                                      viewParams={VISIBLE: labels,
                                                  RENDER: '_pngDir',
                                                  SORT_BY: labels}))

    def _visualizeHistograms(self, e=None):
        plotter = EmPlotter()
		#
        # # Calcular la media (mu) y la desviaci�n est�ndar (sigma)
        # mu = np.sum(eje_x * eje_y) / np.sum(eje_y)
        # sigma = np.sqrt(np.sum(eje_y * (eje_x - mu) ** 2) / np.sum(eje_y))
		#
        # # Plotear los datos
        # plt.figure(figsize=(10, 6))
		#
        # # Scatter plot de los datos originales
        # plt.scatter(eje_x, eje_y, label='Datos', color='b')
		#
        # # Generar puntos para la distribuci�n normal
        # x_fit = np.linspace(np.min(eje_x), np.max(eje_x), 100)
        # y_fit = np.exp(-(x_fit - mu) ** 2 / (2 * sigma ** 2)) / (sigma * np.sqrt(2 * np.pi))
		#
        # # Plotear la distribuci�n normal
        # plt.plot(x_fit, y_fit, label=f'Distribuci�n Normal ($\mu$={mu:.2f}, $\sigma$={sigma:.2f})', color='r')
		#
        # # Configuraci�n del gr�fico
        # plt.title('Distribuci�n de datos y ajuste a distribuci�n normal')
        # plt.xlabel('Eje X')
        # plt.ylabel('Eje Y')
        # plt.legend()
        # plt.grid(True)
		#
        # # Mostrar el gr�fico
        # plt.show()