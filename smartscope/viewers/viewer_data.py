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
            ax1.bar(x_positions, listRanges['totalHist'], color='black', edgecolor='black', width=bin_width * 0.95,linewidth=2, label='Total holes', alpha=0.2)
            ax1.bar(x_positions, listRanges['withMicsHist'], color='blue', edgecolor='blue', width=bin_width * 0.95,linewidth=2,  label='Holes with mics', alpha=0.2)
            ax1.bar(x_positions, listRanges['passHist'], color='green', edgecolor='green', width=bin_width * 0.95, linewidth=2, label='Holes pass filters', alpha=0.2)
            ax1.set_xlabel('Intensity Range')
            ax1.set_ylabel('Number of Holes')
            ax1.set_title('Histogram holes behave')
            ax1.legend(loc='upper right')
            plt.xticks(np.round(bin_edges).astype(int) , rotation=45, ha='right')  # Rotate labels for better readability
            ax1.set_xticks(np.round(bin_edges).astype(int) )  # Apply to ax1
            ax1.set_xticklabels([f'{edge:.2f}' for edge in bin_edges], rotation=45, ha='right')

            #PLOT 2#####################
            ratioHist = np.divide(listRanges['passHist'], listRanges['withMicsHist'], out=np.zeros_like(listRanges['withMicsHist'], dtype=float),
                                  where=(listRanges['passHist'] != 0))
            ax2.bar(x_positions, ratioHist, color='orange', edgecolor='orange', linewidth=2, width=bin_width * 0.95,
                    label='Holes with micrographs Mics / Holess pass filters', alpha=0.2)
            ax2.set_ylabel('Holes with micrographs / Holes with micrographs pass filters')
            ax2.legend(loc='upper right')
            ax2.set_xticks(np.round(bin_edges).astype(int))  # Apply to ax2
            ax2.set_xticklabels([f'{edge:.2f}' for edge in np.round(bin_edges).astype(int)], rotation=45, ha='right')
            plt.xlabel('Intensity Range')


            plt.tight_layout()

            plt.show()