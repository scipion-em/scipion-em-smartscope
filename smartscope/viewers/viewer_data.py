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
import numpy as np
import matplotlib.pyplot as plt

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
        self._views = []
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
        group.addParam('visualizeFilteredOutHoles', LabelParam,
                       label="Visualize filtered out holes",
                       help="")
        group.addParam('visualizeFilteredHoles', LabelParam,
                       label="Visualize filtered holes",
                       help="")
        group2 = form.addGroup('Statistics')
        group2.addParam('visualizeHistograms', LabelParam,
                       label="Visualize the histograms of intensity",
                       help="Visualize the histograms of intensity per holes. The last serie"
                            " is scattered and the first (the older) and the last (newest) 5 gaussian reconstructions")


    def _getVisualizeDict(self):
        return {
                 'visualizeFilteredOutHoles': self._visualizeFilteredOut,
                 'visualizeFilteredHoles': self._visualizeFilteredHoles,
                 'visualizeHistograms': self._visualizeHistograms,
                }


    def _visualizeFilteredHoles(self, e=None):
        views = []
        if hasattr(self.protocol, 'SetOfHolesFiltered'):
            labels = (
                '_pngDir _hole_id _grid_id _status _selected _completion_time _shape_x _shape_y _sampligRate _number _area')
            views.append(ObjectView(self._project,
                                    self.protocol.SetOfHolesFiltered.strId(),
                                    self.protocol.SetOfHolesFiltered.getFileName(),
                                    viewParams={VISIBLE: labels,
                                                RENDER: '_pngDir',
                                                SORT_BY: labels}))
            return views

    def _visualizeFilteredOut(self, e=None):
        views = []
        if hasattr(self.protocol, 'SetOfHolesFilteredOut'):
            labels = (
                '_pngDir _hole_id _grid_id _status _selected _completion_time _shape_x _shape_y _sampligRate _number _area')
            views.append(ObjectView(self._project,
                                          self.protocol.SetOfHolesFilteredOut.strId(),
                                          self.protocol.SetOfHolesFilteredOut.getFileName(),
                                          viewParams={VISIBLE: labels,
                                                      RENDER: '_pngDir',
                                                      SORT_BY: labels}))
            return views


    def _visualizeHistograms(self, e=None):
        def muSigma(intensityRange, coefHoles):
            mu = np.sum(intensityRange * coefHoles) / np.sum(coefHoles)
            sigma = np.sqrt(np.sum(coefHoles * (intensityRange - mu) ** 2) / np.sum(coefHoles))
            return mu, sigma
        listRangesFiles = []
        listHistFiles = []
        listRanges = []
        listHist = []
        files = os.listdir(self.protocol._getExtraPath())
        with open(os.path.join(self.protocol._getExtraPath(),'pathsFile.txt'), 'w') as fi:
            for f in files:
                fi.write(f)
                fi.write('\n')

        for f in files:
            if f.find('rangeI') != -1:
                listRangesFiles.append(f)
            elif f.find('histRatio') != -1:
                listHistFiles.append(f)

        def extraer_numero(rango):
            return int(rango.split('-')[1].split('.')[0])

        # Ordenar la lista utilizando la función de clave personalizada
        listRangesFiles = sorted(listRangesFiles, key=extraer_numero)[::-1]
        listHistFiles = sorted(listHistFiles, key=extraer_numero)[::-1] #the first the newer
        for f in listRangesFiles:
            listRanges.append(np.loadtxt(os.path.join(self.protocol._getExtraPath(), f), dtype=np.float))
        for f in listHistFiles:
            listHist.append(np.loadtxt(os.path.join(self.protocol._getExtraPath(), f), dtype=np.float))#TODO no carga datos del fichero

        mu = []
        sigma = []
        if len(listRangesFiles) > 0:
            for index, _ in enumerate(listRangesFiles):
                if len(listHist) > 0:
                    m, s = muSigma(listRanges[index], listHist[index])
                    mu.append(m)
                    sigma.append(s)

        # Crear figura y ejes
        fig, ax1 = plt.subplots(figsize=(12, 8))
        # Calcular el ancho de los bins
        bin_widths = int((listRanges[0][1] - listRanges[0][0])) #truncated number

        # Configuración del primer eje (izquierdo) para los puntos
        color = 'tab:blue'
        ax1.set_xlabel('Holes Intensity')
        ax1.set_ylabel('total holes / good holes')
        ax1.bar(listRanges[0], listHist[0], label='Coef good holes (Last update)', color='midnightblue', width=bin_widths, alpha=0.8, edgecolor='black')
        ax1.tick_params(axis='y')
        ax1.legend(loc='upper left')
        ax1.set_ylim(0, 1)
        ax1.grid(True)

        # Crear el segundo eje (derecho) para la distribución normal
        ax2 = ax1.twinx()
        color = 'black'
        ax2.set_ylabel('Gaussian Distribution', color=color)
        numSerie2 = 0
        colors = ['midnightblue', 'mediumblue', 'slateblue', 'mediumpurple']
        order = ['Last', 'Second to last', 'Third to last', 'Fourth to last']
        for _ in listRanges[:4]:
            x_fit = np.linspace(np.min(listRanges[numSerie2]), np.max(listRanges[numSerie2]), 100)
            y_fit1 = np.exp(-(x_fit - mu[numSerie2]) ** 2 / (2 * sigma[numSerie2] ** 2)) / (sigma[numSerie2] * np.sqrt(2 * np.pi))
            ax2.plot(x_fit, y_fit1, label=f'{order[numSerie2]} ($\mu$={mu[numSerie2]:.2f}, $\sigma$={sigma[numSerie2]:.2f})',
                     color=colors[numSerie2])

            ax2.tick_params(axis='y', labelcolor=color)
            ax2.legend(loc='upper right')
            numSerie2 += 1
        ax2.fill_between(x_fit, 0, y_fit1, where=((x_fit >= mu[0] - sigma[0]) & (x_fit <= mu[0] + sigma[0])),
                         color='green', alpha=0.3, label=f'Rango $\mu \pm \sigma$')
        ax2.set_ylim(0, max(y_fit1) * 1.1)

        plt.title('Intensity - total / good holes')
        plt.show()
