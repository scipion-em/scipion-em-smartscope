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
from scipy.stats import norm

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
        import os
        def muSigma(intensityRange, coefHoles):
            mu = np.sum(intensityRange * coefHoles) / np.sum(coefHoles)
            sigma = np.sqrt(np.sum(coefHoles * (intensityRange - mu) ** 2) / np.sum(coefHoles))
            return mu, sigma

        with open(os.path.join(self.protocol._getExtraPath(),'gridsName.txt'), 'r') as fi:
            gridsList = [line.strip() for line in fi]
        for grid in gridsList:
            dictFiles = {}
            files = os.listdir(self.protocol._getExtraPath())

            for f in files:
                if f.find('{}-rangeI'.format(grid)) != -1:
                    dictFiles['rangeI'] = f
                elif f.find('{}-totalHist'.format(grid)) != -1:
                    dictFiles['totalHist'] = f
                elif f.find('{}-withMicsHist'.format(grid)) != -1:
                    dictFiles['withMicsHist'] = f
                elif f.find('{}-passHist'.format(grid)) != -1:
                    dictFiles['passHist'] = f
                elif f.find('{}-rejectedHist'.format(grid)) != -1:
                    dictFiles['rejectedHist'] = f
            print(dictFiles)
            listRanges = {'rangeI': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['rangeI']), dtype=np.float),
            'totalHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['totalHist']), dtype=np.float),
            'withMicsHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['withMicsHist']), dtype=np.float),
            'passHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['passHist']), dtype=np.float),
            'rejectedHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['rejectedHist']), dtype=np.float)}


            #PLOT 1#####################
            nBins = len(listRanges['rangeI'])
            bin_width = (listRanges['rangeI'][-1] - listRanges['rangeI'][0]) / nBins
            bin_edges = np.linspace(listRanges['rangeI'][0], listRanges['rangeI'][-1], nBins + 1)
            x_positions = (bin_edges[:-1] + bin_edges[1:]) / 2
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
            fig.canvas.manager.set_window_title('Histograms holes smartscope')
            ax1.bar(x_positions, listRanges['totalHist'], color='black', edgecolor='black', width=bin_width,linewidth=2, label='Total Holes', alpha=0.2)
            ax1.bar(x_positions, listRanges['withMicsHist'], color='blue', edgecolor='blue', width=bin_width,linewidth=2,  label='With Mics Holes', alpha=0.2)
            ax1.bar(x_positions, listRanges['passHist'], color='green', edgecolor='green', width=bin_width, linewidth=2, label='Pass Holes', alpha=0.2)
            ax1.set_ylabel('Intensity Range')
            ax1.set_xlabel('Number of Holes')
            ax1.set_title('Histogram holes behave')
            ax1.legend(loc='upper right')

            #PLOT 2#####################
            ratioHist = np.divide(listRanges['passHist'], listRanges['withMicsHist'], out=np.zeros_like(listRanges['withMicsHist'], dtype=float),
                                  where=(listRanges['passHist'] != 0))
            ax2.bar(x_positions, ratioHist, color='purple', edgecolor='purple', linewidth=1.5, width=bin_width * 0.8,
                    label='Holes with micrographs Mics / Holess pass filters', alpha=0.5)
            # DEBUGALBERTO START
            import os
            fname = "/home/agarcia/Documents/attachActionDebug.txt"
            if os.path.exists(fname):
                os.remove(fname)
            fjj = open(fname, "a+")
            fjj.write('ALBERTO--------->onDebugMode PID {}'.format(os.getpid()))
            fjj.close()
            print('ALBERTO--------->onDebugMode PID {}'.format(os.getpid()))
            import time
            time.sleep(10)
            # DEBUGALBERTO END
            if np.any(ratioHist):  # Verificar si hay algún valor no cero
                mu = np.mean(ratioHist)
                sigma = np.std(ratioHist)
                x_fit = np.linspace(min(ratioHist), max(ratioHist), 100)
                y_fit = norm.pdf(x_fit, mu, sigma) * (np.max(ratioHist) - np.min(ratioHist)) / (np.max(y_fit) - np.min(y_fit))  # Normalizar

                # Graficar la curva normal
                ax2.plot(x_fit, y_fit, color='orange', label='Normal Curve', linewidth=2)
                ax2.fill_betweenx(y_fit, mu - sigma, mu + sigma, color='green', alpha=0.3, label='$\mu \pm \sigma$ Area')

            ax2.set_ylabel('Holes with micrographs (acquired) / Holes with micrographs that pass  the filters')
            ax2.legend(loc='upper right')
            plt.xlabel('Intensity Range')
            plt.tight_layout()

            plt.show()





            #
            #
            # mu = []
            # sigma = []
            # if len(listRangesFiles) > 0:
            #     for index, _ in enumerate(listRangesFiles):
            #         if len(listHist) > 0:
            #             m, s = muSigma(listRanges[index], listHist[index])
            #             mu.append(m)
            #             sigma.append(s)
            #
            # # Crear figura y ejes
            # fig, ax1 = plt.subplots(figsize=(12, 8))
            # # Calcular el ancho de los bins
            # bin_widths = int((listRanges[0][1] - listRanges[0][0])) #truncated number
            #
            # # Configuración del primer eje (izquierdo) para los puntos
            # color = 'tab:blue'
            # ax1.set_xlabel('Holes Intensity')
            # ax1.set_ylabel('total holes / good holes')
            # ax1.bar(listRanges[0], listHist[0], label='Coef good holes (Last update)', color='midnightblue', width=bin_widths, alpha=0.8, edgecolor='black')
            # ax1.tick_params(axis='y')
            # ax1.legend(loc='upper left')
            # ax1.set_ylim(0, 1)
            # ax1.grid(True)
            #
            # # Crear el segundo eje (derecho) para la distribución normal
            # ax2 = ax1.twinx()
            # color = 'black'
            # ax2.set_ylabel('Gaussian Distribution', color=color)
            #
            # numSerie2 = 0
            # colors = ['midnightblue', 'mediumblue', 'slateblue', 'mediumpurple']
            # order = ['Last', 'Second to last', 'Third to last', 'Fourth to last']
            # for _ in listRanges[:4]:
            #     x_fit = np.linspace(np.min(listRanges[numSerie2]), np.max(listRanges[numSerie2]), 100)
            #     y_fit1 = np.exp(-(x_fit - mu[numSerie2]) ** 2 / (2 * sigma[numSerie2] ** 2)) / (sigma[numSerie2] * np.sqrt(2 * np.pi))
            #     ax2.plot(x_fit, y_fit1, label=f'{order[numSerie2]} ($\mu$={mu[numSerie2]:.2f}, $\sigma$={sigma[numSerie2]:.2f})',
            #              color=colors[numSerie2])
            #
            #     ax2.tick_params(axis='y', labelcolor=color)
            #     ax2.legend(loc='upper right')
            #     numSerie2 += 1
            # ax2.fill_between(x_fit, 0, y_fit1, where=((x_fit >= mu[0] - sigma[0]) & (x_fit <= mu[0] + sigma[0])),
            #                  color='green', alpha=0.3, label=f'Rango $\mu \pm \sigma$')
            # ax2.set_ylim(0, max(y_fit1) * 1.1)
            #
            # plt.title('GRID: {}  Intensity - total holes / good holes'.format(grid))
            # plt.show()
