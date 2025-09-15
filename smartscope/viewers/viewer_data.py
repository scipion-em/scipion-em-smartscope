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
from smartscope.protocols.protocol_feedback_2D import smartscopeFeedback2D
from smartscope.protocols.protocol_smartscope import smartscopeConnection
from pyworkflow.protocol.params import IntParam, LabelParam
import numpy as np
import matplotlib.pyplot as plt
import webbrowser
import re
import os
import matplotlib.pyplot as plt
import math

class DataViewer_smartscope(ProtocolViewer):
    _targets = [smartscopeConnection]
    _label = 'viewer feedback holes filter'
    _environments = [DESKTOP_TKINTER, WEB_DJANGO]

    def _defineParams(self, form):
        form.addSection(label='Visualization')
        group = form.addGroup('Outputs to view')
        group.addParam('visualizeGrids', LabelParam,
                       label="Visualize grids",
                       help="")
        group.addParam('visualizeAtlas', LabelParam,
                       label="Visualize atlas",
                       help="")
        group.addParam('visualizeSquares', LabelParam,
                       label="Visualize squares",
                       help="")
        group.addParam('visualizeHoles', LabelParam,
                       label="Visualize holes",
                       help="")
        group.addParam('visualizeMovies', LabelParam,
                       label="Visualize movies",
                       help="")
        group2 = form.addGroup('Smartscope app')
        group2.addParam('browserApp', LabelParam,
                       label="Open the Smartscope app session",
                       help="")

    def _getVisualizeDict(self):
        return {
                 'visualizeGrids': self._visualizeGrids,
                 'visualizeAtlas': self._visualizeAtlas,
                 'visualizeSquares': self._visualizeSquares,
                 'visualizeHoles': self._visualizeHoles,
                 'visualizeMovies': self._visualizeMovies,
                 'browserApp': self._browserApp,
        }

    def _visualizeGrids(self, e=None):
        views = []
        labels = ('_grid_id _status _position _hole_angle _mesh_angle _quality _status _start_time _last_update _mesh_size mesh_material _hole_type')
        if hasattr(self.protocol, 'Grids'):
            views.append(ObjectView(self._project,
                                           self.protocol.Grids.strId(),
                                           self.protocol.Grids.getFileName(),
                               viewParams={VISIBLE: labels,
                                           SORT_BY: labels}))
            return views


    def _visualizeAtlas(self, e=None):
        views = []
        labels = ('_pngDir _grid_id _atlas_id _binning_factor _status _completion_time _shape_x _shape_y _sampligRate')
        if hasattr(self.protocol, 'Atlas'):
            views.append(ObjectView(self._project,
                                           self.protocol.Atlas.strId(),
                                           self.protocol.Atlas.getFileName(),
                               viewParams={VISIBLE: labels,
                                           RENDER: '_pngDir',
                                           SORT_BY: labels}))
            return views


    def _visualizeSquares(self, e=None):
        views = []
        labels = ('_pngDir _square_id _atlas_id _status _selected _completion_time _area _shape_x _shape_y _sampligRate')
        if hasattr(self.protocol, 'Squares'):
            views.append(ObjectView(self._project,
                                          self.protocol.Squares.strId(),
                                          self.protocol.Squares.getFileName(),
                                          viewParams={VISIBLE: labels,
                                                      RENDER: '_pngDir',
                                                      SORT_BY: labels}))
            return views


    def _visualizeHoles(self, e=None):
        from pwem.viewers.mdviewer.viewer import MDView
        views = []
        #labels = ('_pngDir _rawDir _hole_id _grid_id _selector_value _status _selected _completion_time _shape_x _shape_y _sampligRate _number _area')
        if hasattr(self.protocol, 'Holes'):
            views.append(MDView(self.protocol.Holes, self.protocol, self._project.port))
            return views

    def _visualizeMovies(self, e=None):
        views = []
        labels = ('_micName _hm_id _hole_id _status _completion_time _samplingRate _shape_x _shape_y')
        if hasattr(self.protocol, 'MoviesSS'):#
            views.append(ObjectView(self._project,
                                    self.protocol.MoviesSS.strId(),
                                    self.protocol.MoviesSS.getFileName(),
                                    viewParams={VISIBLE: labels,
                                                MODE: MODE_MD,
                                                SORT_BY: labels}))
            return views

    def _browserApp(self, e=None):
        with open(os.path.join(self.protocol._getExtraPath(), 'URLsmartscopeSession.txt'), 'r') as fi:
            urlsmartscope = fi.read()
        webbrowser.open(urlsmartscope)



class SmartscopeFilterFeedbackViewer(ProtocolViewer):
    """

    """
    _label = 'viewer feedback holes filter'
    _environments = [DESKTOP_TKINTER, WEB_DJANGO]
    _targets = [smartscopeFeedbackFilter]

    def _defineParams(self, form):
        form.addSection(label='Visualization')
        group = form.addGroup('Holes')
        group.addParam('visualizePassFilteredHoles', LabelParam,
                       label="Visualize pass filter holes",
                       help="")
        group.addParam('visualizeRejectedHoles', LabelParam,
                       label="Visualize rejected holes by filters",
                       help="")
        group2 = form.addGroup('Statistics')
        group2.addParam('visualizeHistograms', LabelParam,
                       label="Visualize the histograms of intensity",
                       help="Visualize the histograms of intensity per holes. The last serie"
                            " is scattered and the first (the older) and the last (newest) 5 gaussian reconstructions")

    def _getVisualizeDict(self):
        return {
                 'visualizePassFilteredHoles': self._visualizePassFilteredHoles,
                 'visualizeRejectedHoles': self._visualizeRejectedHoles,
                 'visualizeHistograms': self._visualizeHistograms,
                }

    def _visualizePassFilteredHoles(self, e=None):
        views = []
        if hasattr(self.protocol, 'SetOfHolesPassFilter'):
            labels = (
                '_pngDir _bis_type _hole_id _grid_id _selector_value _status _selected _shape_x _shape_y _sampligRate _number _area')
            views.append(ObjectView(self._project,
                                    self.protocol.SetOfHolesPassFilter.strId(),
                                    self.protocol.SetOfHolesPassFilter.getFileName(),
                                    viewParams={VISIBLE: labels,
                                                RENDER: '_rawDir',
                                                SORT_BY: labels}))
            return views

    def _visualizeRejectedHoles(self, e=None):
        views = []
        if hasattr(self.protocol, 'SetOfHolesRejected'):
            labels = (
                '_pngDir _bis_type _hole_id _grid_id _selector_value _status _selected _shape_x _shape_y _sampligRate _number _area')
            views.append(ObjectView(self._project,
                                          self.protocol.SetOfHolesRejected.strId(),
                                          self.protocol.SetOfHolesRejected.getFileName(),
                                          viewParams={VISIBLE: labels,
                                                      RENDER: '_rawDir',
                                                      SORT_BY: labels}))
            return views

    def _visualizeHistograms(self, e=None):
        import os
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


            listRanges = {'rangeI': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['rangeI'])),
            'totalHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['totalHist'])),
            'withMicsHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['withMicsHist'])),
            'passHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['passHist'])),
            'rejectedHist': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['rejectedHist']))}


            #PLOT 1#####################
            nBins = len(listRanges['rangeI'])
            bin_width = (listRanges['rangeI'][-1] - listRanges['rangeI'][0]) / nBins
            bin_edges = np.linspace(listRanges['rangeI'][0], listRanges['rangeI'][-1], nBins + 1)
            x_positions = (bin_edges[:-1] + bin_edges[1:]) / 2
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10), sharex=True)
            fig.canvas.manager.set_window_title('Histograms holes smartscope')
            ax1.bar(x_positions, listRanges['totalHist'], color='black', edgecolor='black', width=bin_width * 0.95,linewidth=2, label='Total possible Micrographs (based on holes availability)', alpha=0.2)
            bars_with_mics = ax1.bar(x_positions, listRanges['withMicsHist'], color='blue', edgecolor='blue', width=bin_width * 0.95,linewidth=2,  label='Micrographs acquired', alpha=0.2)
            bars_pass = ax1.bar(x_positions, listRanges['passHist'], color='green', edgecolor='green', width=bin_width * 0.95, linewidth=2, label='Micrographs pass filters', alpha=0.2)
            ax1.set_ylabel('Number of Micrographs')
            ax1.set_title('Histogram holes behave')
            ax1.legend(loc='upper right')
            plt.xticks(np.round(bin_edges).astype(int) , rotation=0, ha='right')  # Rotate labels for better readability
            ax1.set_xticks(np.round(bin_edges).astype(int) )  # Apply to ax1
            ax1.set_xticklabels([f'{edge:.2f}' for edge in bin_edges], rotation=45, ha='right')

            for bar in  bars_with_mics:
                height = bar.get_height()
                if height > 0:
                    ax1.text(
                        bar.get_x() + bar.get_width() / 2,
                        height,
                        f'{height:.0f}',
                        ha='left', va='bottom', fontsize=8, color='blue', rotation=45
                    )
            for bar in bars_pass:
                height = bar.get_height()
                if height > 0:
                    ax1.text(
                        bar.get_x() + bar.get_width() / 2,
                        height,
                        f'{height:.0f}',
                        ha='right', va='bottom', fontsize=8, color='green', rotation=45
                    )


            #PLOT 2#####################
            ratioHist = np.divide(listRanges['passHist'], listRanges['withMicsHist'], out=np.zeros_like(listRanges['withMicsHist'], dtype=float),
                                  where=(listRanges['passHist'] != 0))
            barHist = ax2.bar(x_positions, ratioHist, color='indigo', edgecolor='indigo', linewidth=2, width=bin_width * 0.95,
                    label='Micrographs pass filters / Total Micrographs', alpha=0.2)
            ax2.set_ylabel('Micrographs acquired / Micrographs pass filters')
            ax2.legend(loc='upper right')
            ax2.set_ylim(0, 1)
            ax2.set_xticks(np.round(bin_edges).astype(float))
            ax2.set_xticklabels([f'{edge:.2f}' for edge in bin_edges], rotation=0, ha='center')
            plt.xlabel('Intensity range of Holes')

            for bar in barHist:
                height = bar.get_height()
                if height > 0:
                    ax2.text(
                        bar.get_x() + bar.get_width() / 2,
                        height,
                        f'{(height * 100):.0f}%',
                        ha='center', va='bottom', fontsize=8, color='indigo'
                    )

            plt.tight_layout()

            plt.show()


class SmartscopeParticlesFeedbackViewer(ProtocolViewer):
    """

    """
    _label = 'viewer feedback holes particles'
    _environments = [DESKTOP_TKINTER, WEB_DJANGO]
    _targets = [smartscopeFeedback2D]

    def _defineParams(self, form):
        form.addSection(label='Visualization')
        group = form.addGroup('Holes')
        group.addParam('visualizeBestHolesWithParticles', LabelParam,
                       label="Visualize best 100 holes by good particles",
                       help="")
        group2 = form.addGroup('Statistics')
        group2.addParam('visualizeHistograms', LabelParam,
                       label="Visualize the histograms of intensity",
                       help="Visualize the histograms of intensity per holes and particles.")
        group2.addParam('classesDistribution', LabelParam,
                       label="Visualize class distribution of particles by intensity",
                       help="")

    def _getVisualizeDict(self):
        return {
                 'visualizeBestHolesWithParticles': self._visualizeBestHolesWithParticles,
                 'classesDistribution': self._classesDistribution,
                 'visualizeHistograms': self._visualizeHistograms
                }

    def _visualizeBestHolesWithParticles(self, e=None):
        views = []
        if hasattr(self.protocol, 'SetOfBestHoles'):
            labels = ('_pngDir _hole_id _grid_id _goodParticles _badParticles _totalParticles')
            views.append(ObjectView(self._project,
                                    self.protocol.SetOfBestHoles.strId(),
                                    self.protocol.SetOfBestHoles.getFileName(),
                                    viewParams={VISIBLE: labels,
                                                RENDER: '_rawDir',
                                                SORT_BY: labels}))
            return views


    def _classesDistribution(self, e=None):
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
        time.sleep(5)
        # DEBUGALBERTO END


        with open(os.path.join(self.protocol._getExtraPath(),'gridsName.txt'), 'r') as fi:
            gridsList = [line.strip() for line in fi]
        for grid in gridsList:
            dictFiles = {}
            files = os.listdir(self.protocol._getExtraPath())
            for f in files:
                if f.find('{}-xBin'.format(grid)) != -1:
                    dictFiles['xBin'] = f
                elif f.find('{}-holeCount'.format(grid)) != -1:
                    dictFiles['holeCount'] = f
                elif f.find('{}-holeTotalCount'.format(grid)) != -1:
                    dictFiles['holeTotalCount'] = f
                elif f.find('{}-bin_edges'.format(grid)) != -1:
                    dictFiles['bin_edges'] = f
                elif f.find('{}-classes-'.format(grid)) != -1:
                    classNum = f[f.find('class'):]
                    match = re.search(r"\d+", classNum)
                    if match:
                        dictFiles[f'class-{int(match.group())}'] = f


        numClasses = range(sum(1 for key in dictFiles if "class" in key))
        listRanges = {'xBin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['xBin'])),
                      'holeCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeCount'])),
                      'holeTotalCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeTotalCount'])),
                      'bin_edges': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['bin_edges']))}

        classesList = [c for c, v in dictFiles.items() if "-classes-" in v]
        for v in classesList:
            listRanges[v] = np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles[v]))
        classesList = sorted(classesList, key=lambda x: int(x.split('-')[1]))
        #Images
        classImagesDict = {}
        for c in self.protocol.goodClasses2D.get():
            path_mrc = c.getRepresentative().getFileName()
            classNumber = c.getRepresentative().getIndex()
            classImagesDict[classNumber] = f"{classNumber}@{path_mrc}"


        #PLOTS
        fig, ax = plt.subplots(figsize=(12, 6))
        # Dibujar barras agrupadas
        x = np.arange(len(listRanges['xBin']))  # posiciones en eje X
        width = 0.12  # ancho de cada barra
        for i, cls in enumerate(classesList):
            ax.bar(x + i * width, listRanges[cls], width, label=cls)
        # Etiquetas y formato
        ax.set_xticks(x + width * (len(classesList) / 2))
        ax.set_xticklabels(np.round(listRanges['xBin'], 1), rotation=45)
        ax.set_xlabel("Intensity")
        ax.set_ylabel("Frecuencia")
        ax.set_title("Distribución por clase en función de intensity")
        ax.legend()
        plt.tight_layout()
        plt.show()



        # --- Filtrar bins vacíos ---
        matrix = np.vstack([listRanges[c] for c in classesList])  # shape (n_classes, n_bins)
        mask = matrix.sum(axis=0) > 0  # bins con algún valor
        xBin_filtered = listRanges['xBin'][mask]
        matrix_filtered = matrix[:, mask]

        # --- Normalización a porcentajes ---
        col_sums = matrix_filtered.sum(axis=0)
        percent_matrix = matrix_filtered / col_sums * 100  # cada columna suma 100%

        # --- Subplots en grid ---
        n_classes = len(classesList)
        n_cols = 4
        n_rows = math.ceil(n_classes / n_cols)

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows), sharex=True, sharey=True)
        axes = axes.flatten()  # convertir a lista para indexar fácilmente

        x = np.arange(len(xBin_filtered))

        for i, cls in enumerate(classesList):
            ax = axes[i]
            ax.bar(x, percent_matrix[i], color=f"C{i % 10}")
            ax.set_title(f"{cls}")
            ax.set_ylim(0, 30)  # porque son porcentajes

            ax.set_xticks(x)
            ax.set_xticklabels(np.round(xBin_filtered, 1), rotation=45)

        # Ocultar ejes vacíos si sobran
        for j in range(len(classesList), len(axes)):
            fig.delaxes(axes[j])

        fig.suptitle("Distribución porcentual por clase en bins con valores", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        plt.show()


    def _visualizeHistograms(self, e=None):


        with open(os.path.join(self.protocol._getExtraPath(),'gridsName.txt'), 'r') as fi:
            gridsList = [line.strip() for line in fi]
        for grid in gridsList:
            dictFiles = {}
            files = os.listdir(self.protocol._getExtraPath())

            for f in files:
                if f.find('{}-xBin'.format(grid)) != -1:
                    dictFiles['xBin'] = f
                elif f.find('{}-holeCount'.format(grid)) != -1:
                    dictFiles['holeCount'] = f
                elif f.find('{}-holeTotalCount'.format(grid)) != -1:
                    dictFiles['holeTotalCount'] = f
                elif f.find('{}-goodBin'.format(grid)) != -1:
                    dictFiles['goodBin'] = f
                elif f.find('{}-good_binTotal'.format(grid)) != -1:
                    dictFiles['good_binTotal'] = f
                elif f.find('{}-badParticles'.format(grid)) != -1:
                    dictFiles['badParticles'] = f
                elif f.find('{}-totalParticles'.format(grid)) != -1:
                    dictFiles['totalParticles'] = f
                elif f.find('{}-stdTotalParticles'.format(grid)) != -1:
                    dictFiles['stdTotalParticles'] = f
                elif f.find('{}-percentGood'.format(grid)) != -1:
                    dictFiles['percentGood'] = f
                elif f.find('{}-bin_edges'.format(grid)) != -1:
                    dictFiles['bin_edges'] = f


            listRanges = {'xBin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['xBin'])),
            'holeCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeCount'])),
            'holeTotalCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeTotalCount'])),
            'good_bin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['goodBin'])),
            'good_binTotal': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['good_binTotal'])),
            'badParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['badParticles'])),
            'totalParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['totalParticles'])),
            'stdTotalParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['stdTotalParticles'])),
            'bin_edges': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['bin_edges'])),
            'percentGood': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['percentGood']))}

            fig, axs = plt.subplots(1, 3, figsize=(14, 5))
            fig.canvas.manager.set_window_title("Visualize the histogram of intensity")
            axs[0].bar(listRanges['xBin'], listRanges['holeTotalCount'],color='gray', width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9, label='Total holes')
            axs[0].bar(listRanges['xBin'], listRanges['holeCount'],  edgecolor='black', color='skyblue', width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9, label='Holes acquired')
            axs[0].set_title("Num holes")
            axs[0].set_xlabel("Holes Intensity")
            axs[0].set_ylabel("Count")
            axs[0].set_xlim(0, listRanges['bin_edges'][-1])
            axs[0].legend()

            axs[1].bar(listRanges['xBin'], listRanges['totalParticles'], width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9,
                       # yerr=self.totalParticles_std_bin,
                       capsize=5, color='gray', label='Total particles')
            axs[1].bar(listRanges['xBin'], listRanges['good_binTotal'], width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9,
                       # yerr=self.good_std_bin,
                       capsize=5, color='green', edgecolor='black', label='Good particles')
            axs[1].set_title("Sum num particles")
            axs[1].set_xlabel("Holes Intensity")
            axs[1].set_ylabel("particles")
            axs[1].set_xlim(0, listRanges['bin_edges'][-1])
            axs[1].legend()

            axs[2].bar(listRanges['xBin'], listRanges['percentGood'], color='green', width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9)
            axs[2].set_title("Media de percent good")
            axs[2].set_xlabel("Holes Intensity")
            axs[2].set_ylabel("Percent good")
            axs[2].set_xlim(0, listRanges['bin_edges'][-1])
            axs[2].set_ylim(0, 1)

            plt.tight_layout()
            plt.show()