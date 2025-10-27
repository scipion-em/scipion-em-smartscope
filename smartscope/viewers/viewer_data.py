# **************************************************************************
# *
# * Authors:  Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)
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



from pwem.viewers import ObjectView
from pwem.viewers.showj import *
from pyworkflow.viewer import DESKTOP_TKINTER, WEB_DJANGO, ProtocolViewer
from smartscope.protocols.protocol_feedback_filter import smartscopeFeedbackFilter
from smartscope.protocols.protocol_feedback_2D import smartscopeFeedback2D
from smartscope.protocols.protocol_smartscope import smartscopeConnection
from pyworkflow.protocol.params import LabelParam

# === Standard Library Imports ===
import base64
import io
import math
import os
import re
import threading
import webbrowser
from pathlib import Path

# === Third-Party Library Imports ===
import dash
from dash import Dash, dcc, html, Output, Input
from dash.dependencies import Input, Output, State
import matplotlib.pyplot as plt
import mrcfile
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image as PILImage, ImageDraw

# === Local Application Imports ===
from smartscope import Plugin
from ..constants import *
from ..objects.dataCollection import *


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
            self.gridsList = [line.strip() for line in fi]
        for grid in self.gridsList:
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

#
# class SmartscopeParticlesFeedbackViewer(ProtocolViewer):
#     """
#
#     """
#     _label = 'viewer feedback holes particles'
#     _environments = [DESKTOP_TKINTER, WEB_DJANGO]
#     _targets = [smartscopeFeedback2D]
#
#     def _defineParams(self, form):
#         form.addSection(label='Visualization')
#         group = form.addGroup('Holes')
#         group.addParam('visualizeBestHolesWithParticles', LabelParam,
#                        label="Visualize best 100 holes by good particles",
#                        help="")
#         group2 = form.addGroup('Statistics')
#         group2.addParam('visualizeHistograms', LabelParam,
#                        label="Histograms of intensity",
#                        help="Visualize the histograms of intensity per holes and particles.")
#         group2.addParam('classesDistribution', LabelParam,
#                        label="Class distribution of particles by intensity",
#                        help="")
#
#     def _getVisualizeDict(self):
#         return {
#                  'visualizeBestHolesWithParticles': self._visualizeBestHolesWithParticles,
#                  'classesDistribution': self._classesDistribution,
#                  'visualizeHistograms': self._visualizeHistograms
#                 }
#
#     def _visualizeBestHolesWithParticles(self, e=None):
#         views = []
#         if hasattr(self.protocol, 'SetOfBestHoles'):
#             labels = ('_pngDir _hole_id _grid_id _goodParticles _badParticles _totalParticles')
#             views.append(ObjectView(self._project,
#                                     self.protocol.SetOfBestHoles.strId(),
#                                     self.protocol.SetOfBestHoles.getFileName(),
#                                     viewParams={VISIBLE: labels,
#                                                 RENDER: '_rawDir',
#                                                 SORT_BY: labels}))
#             return views
#
#
#     def _classesDistribution(self, e=None):
#         import math
#         import numpy as np
#         import mrcfile
#         from matplotlib.widgets import RangeSlider, Button
#
#         # DEBUGALBERTO START
#         import os
#         fname = "/home/agarcia/Documents/attachActionDebug.txt"
#         if os.path.exists(fname):
#             os.remove(fname)
#         fjj = open(fname, "a+")
#         fjj.write('ALBERTO--------->onDebugMode PID {}'.format(os.getpid()))
#         fjj.close()
#         print('ALBERTO--------->onDebugMode PID {}'.format(os.getpid()))
#         import time
#         time.sleep(2)
#         # DEBUGALBERTO END
#
#
#         with open(os.path.join(self.protocol._getExtraPath(),'gridsName.txt'), 'r') as fi:
#             gridsList = [line.strip() for line in fi]
#         for grid in gridsList:
#             dictFiles = {}
#             files = os.listdir(self.protocol._getExtraPath())
#             for f in files:
#                 if f.find('{}-xBin'.format(grid)) != -1:
#                     dictFiles['xBin'] = f
#                 elif f.find('{}-holeCount'.format(grid)) != -1:
#                     dictFiles['holeCount'] = f
#                 elif f.find('{}-holeTotalCount'.format(grid)) != -1:
#                     dictFiles['holeTotalCount'] = f
#                 elif f.find('{}-bin_edges'.format(grid)) != -1:
#                     dictFiles['bin_edges'] = f
#                 elif f.find('{}-classes-'.format(grid)) != -1:
#                     classNum = f[f.find('class'):]
#                     match = re.search(r"\d+", classNum)
#                     if match:
#                         dictFiles[f'class-{int(match.group())}'] = f
#
#         # --- Preparación de datos ---
#         numClasses = range(sum(1 for key in dictFiles if "class" in key))
#         listRanges = {
#             'xBin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['xBin'])),
#             'holeCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeCount'])),
#             'holeTotalCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeTotalCount'])),
#             'bin_edges': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['bin_edges']))
#         }
#
#         classesList = [c for c, v in dictFiles.items() if "-classes-" in v]
#         for v in classesList:
#             listRanges[v] = np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles[v]))
#         classesList = sorted(classesList, key=lambda x: int(x.split('-')[1]))
#
#         # -----------------------------
#         # DATA manipulation
#         # -----------------------------
#
#         # 1. Build dictionary of representative images
#         classImagesDict = {}
#         for c in self.protocol.goodClasses2D.get():
#             path_mrc = c.getRepresentative().getFileName()
#             classNumber = c.getRepresentative().getIndex()
#             classImagesDict[classNumber] = f"{classNumber}@{path_mrc}"
#
#         # 2. Filter empty bins
#         matrix = np.vstack([listRanges[c] for c in classesList])  # shape (n_classes, n_bins)
#         mask = matrix.sum(axis=0) > 0  # only bins with some value
#         xBin_filtered = listRanges['xBin'][mask]
#         matrix_filtered = matrix[:, mask]
#         particles_per_class = matrix_filtered.sum(axis=1)
#
#         # 3. Normalize to percentages
#         col_sums = matrix_filtered.sum(axis=0)
#         percent_matrix = matrix_filtered / col_sums * 100  # each column sums to 100%
#
#         # 4. Prepare subplots grid
#         n_classes = len(classesList)
#         n_cols = 4 if n_classes <= 12 else 5
#         n_rows = math.ceil(n_classes / n_cols)
#
#
#         # -----------------------------
#         #FIGURE Creation
#         # -----------------------------
#
#         fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows), sharex=True, sharey=True)
#
#         # 1. Slider for intensity range
#         # fig.text(0.5, 0.98, "Select range of intensity", ha="center", va="center", fontsize=14, fontweight="bold")
#
#         # # Slider axes
#         # ax_slider = fig.add_axes([0.15, 0.92, 0.5, 0.03])
#         # slider = RangeSlider(
#         #     ax_slider,
#         #     "",  # no label since title is above
#         #     valmin=float(np.min(xBin_filtered)),
#         #     valmax=float(np.max(xBin_filtered)),
#         #     valinit=(float(np.min(xBin_filtered)), float(np.max(xBin_filtered))),
#         #     facecolor="blue"
#         # )
#         # slider.track.set_color("lightgray")  # color of unselected range
#         # ax_button = fig.add_axes([0.75, 0.92, 0.15, 0.04])
#         # button = Button(ax_button, "Apply")
#
#         # # Callback function
#         # def apply_range(event):
#         #     vmin, vmax = slider.val
#         #     for ax in axes:
#         #         ax.set_xlim(vmin, vmax)  # update x-limits for all subplots
#         #     fig.canvas.draw_idle()
#
#         fig.suptitle("Percentage Distribution of Particles per Bin for Each 2D Class",
#             fontsize=14, fontweight="bold", y=0.98)
#         #plt.subplots_adjust(top=0.65) # leave space for slider and titles
#         axes = axes.flatten()
#
#         x = np.arange(len(xBin_filtered))
#         ymax = int(np.ceil(np.max(percent_matrix) / 10) * 10)
#
#         # highlight_areas = []        # 5. Plot each class
#         for i, cls in enumerate(classesList):
#             ax = axes[i]
#
#             # --- Background image ---
#             class_idx = int(cls.split('-')[1])
#             img_ref = classImagesDict.get(class_idx)
#             # area = ax.axvspan(0, 3, color='blue', alpha=0.3)
#             # highlight_areas.append(area)
#             if img_ref:
#                 idx, path_mrc = img_ref.split('@')
#                 idx = int(idx)
#                 with mrcfile.open(path_mrc) as mrc:
#                     idx = idx % mrc.data.shape[0]
#                     img_data = mrc.data[idx]
#                 ax.imshow(img_data, cmap='gray', extent=[-0.5, len(x) - 0.5, 0, ymax], alpha=0.9, aspect='auto')
#
#             y = percent_matrix[i]
#
#             # # --- Filled area ---
#             fill_color = (0, 0.6, 0, 0.3)  # semi-transparent green fill
#             edge_color = (0, 0.4, 0, 1)  # darker green border
#             ax.fill_between(x, 0, y, facecolor=fill_color, edgecolor=edge_color, linewidth=2)
#
#             # --- Display number of particles ---
#             n_particles = int(particles_per_class[i])
#             ax.text(
#                 0.95, 0.9, f"Particles: {n_particles}",
#                 transform=ax.transAxes,
#                 ha='right', va='top',
#                 fontsize=10, fontweight='bold',
#                 bbox=dict(facecolor='white', alpha=0.6, edgecolor='none', boxstyle='round,pad=0.3')
#             )
#
#             # --- Points on each value ---
#             ax.plot(x, y, 'o', color=(0, 0.3, 0, 1), markersize=4)
#             ax.set_title(f"{cls}")
#             ax.set_ylim(0, ymax)
#             ax.set_xticks(x)
#             ax.set_xticklabels(np.round(xBin_filtered, 1), rotation=45)
#
#             # --- Y-axis only for first column ---
#             if i % n_cols == 0:
#                 ax.set_ylabel("Percent (%)", fontsize=11)
#
#             # --- X-axis only for last row ---
#             if i // n_cols == n_rows - 1:
#                 ax.set_xlabel("Intensity (Ice Thickness)", fontsize=11)
#
#         # --- Remove extra axes if any ---
#         for j in range(len(classesList), len(axes)):
#             fig.delaxes(axes[j])
#
#         # button.on_clicked(apply_range)
#         #
#         # def update(val):
#         #     vmin, vmax = slider.val
#         #     for area in highlight_areas:
#         #         area.set_xy([[vmin, 0], [vmin, 1], [vmax, 1], [vmax, 0], [vmin, 0]])  # actualizar coords del área
#         #     fig.canvas.draw_idle()
#         #
#         # slider.on_changed(update)
#
#         plt.tight_layout(rect=[0, 0, 1, 0.87])
#         plt.show()
#
#     def _visualizeHistograms(self, e=None):
#
#
#         with open(os.path.join(self.protocol._getExtraPath(),'gridsName.txt'), 'r') as fi:
#             gridsList = [line.strip() for line in fi]
#         for grid in gridsList:
#             dictFiles = {}
#             files = os.listdir(self.protocol._getExtraPath())
#
#             for f in files:
#                 if f.find('{}-xBin'.format(grid)) != -1:
#                     dictFiles['xBin'] = f
#                 elif f.find('{}-holeCount'.format(grid)) != -1:
#                     dictFiles['holeCount'] = f
#                 elif f.find('{}-holeTotalCount'.format(grid)) != -1:
#                     dictFiles['holeTotalCount'] = f
#                 elif f.find('{}-goodBin'.format(grid)) != -1:
#                     dictFiles['goodBin'] = f
#                 elif f.find('{}-good_binTotal'.format(grid)) != -1:
#                     dictFiles['good_binTotal'] = f
#                 elif f.find('{}-badParticles'.format(grid)) != -1:
#                     dictFiles['badParticles'] = f
#                 elif f.find('{}-totalParticles'.format(grid)) != -1:
#                     dictFiles['totalParticles'] = f
#                 elif f.find('{}-stdTotalParticles'.format(grid)) != -1:
#                     dictFiles['stdTotalParticles'] = f
#                 elif f.find('{}-percentGood'.format(grid)) != -1:
#                     dictFiles['percentGood'] = f
#                 elif f.find('{}-bin_edges'.format(grid)) != -1:
#                     dictFiles['bin_edges'] = f
#
#
#             listRanges = {'xBin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['xBin'])),
#             'holeCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeCount'])),
#             'holeTotalCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeTotalCount'])),
#             'good_bin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['goodBin'])),
#             'good_binTotal': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['good_binTotal'])),
#             'badParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['badParticles'])),
#             'totalParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['totalParticles'])),
#             'stdTotalParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['stdTotalParticles'])),
#             'bin_edges': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['bin_edges'])),
#             'percentGood': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['percentGood']))}
#
#             fig, axs = plt.subplots(1, 3, figsize=(14, 5))
#             fig.canvas.manager.set_window_title("Visualize the histogram of intensity")
#             axs[0].bar(listRanges['xBin'], listRanges['holeTotalCount'],color='gray', width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9, label='Total holes')
#             axs[0].bar(listRanges['xBin'], listRanges['holeCount'],  edgecolor='black', color='skyblue', width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9, label='Holes acquired')
#             axs[0].set_title("Num holes")
#             axs[0].set_xlabel("Holes Intensity")
#             axs[0].set_ylabel("Count")
#             axs[0].set_xlim(0, listRanges['bin_edges'][-1])
#             axs[0].legend()
#
#             axs[1].bar(listRanges['xBin'], listRanges['totalParticles'], width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9,
#                        # yerr=self.totalParticles_std_bin,
#                        capsize=5, color='gray', label='Total particles')
#             axs[1].bar(listRanges['xBin'], listRanges['good_binTotal'], width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9,
#                        # yerr=self.good_std_bin,
#                        capsize=5, color='green', edgecolor='black', label='Good particles')
#             axs[1].set_title("Sum num particles")
#             axs[1].set_xlabel("Holes Intensity")
#             axs[1].set_ylabel("particles")
#             axs[1].set_xlim(0, listRanges['bin_edges'][-1])
#             axs[1].legend()
#
#             axs[2].bar(listRanges['xBin'], listRanges['percentGood'], color='green', width=(listRanges['bin_edges'][1] - listRanges['bin_edges'][0]) * 0.9)
#             axs[2].set_title("Media de percent good")
#             axs[2].set_xlabel("Holes Intensity")
#             axs[2].set_ylabel("Percent good")
#             axs[2].set_xlim(0, listRanges['bin_edges'][-1])
#             axs[2].set_ylim(0, 1)
#
#             plt.tight_layout()
#             plt.show()
#
#     def r2_numpy(self, y, y_fit):
#         ss_res = np.sum((y - y_fit) ** 2)
#         ss_tot = np.sum((y - np.mean(y)) ** 2)
#         return 1 - ss_res / ss_tot
#
#

class SmartscopeParticlesFeedbackInteractive(ProtocolViewer):
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
        group2.addParam('interactiveClassHoles', LabelParam,
                       label="Class distribution of particles by intensity",
                       help="")

    def _getVisualizeDict(self):
        return {
                 'visualizeBestHolesWithParticles': self._visualizeBestHolesWithParticles,
                 'interactiveClassHoles': self._interactiveClassHoles,
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

    def _interactiveClassHoles(self, e=None):
        self.dataCollection()
        self.dataManipulation()
        self.plotlySetup()

    def dataCollection(self):
            with open(os.path.join(self.protocol._getExtraPath(), 'urlSmartscope.txt'), 'r') as fi:
                self.urlSmartscope = fi.read()
            with open(os.path.join(self.protocol._getExtraPath(), 'sessionDetails.txt'), 'r') as fi:
                self.sessionDetails = fi.read()
            with open(os.path.join(self.protocol._getExtraPath(),'gridsName.txt'), 'r') as fi:
                self.gridsList = [line.strip() for line in fi]
            with open(os.path.join(self.protocol._getExtraPath(), 'gridsId.txt'), 'r') as fi:
                self.gridsIdList = [line.strip() for line in fi]
            for grid in self.gridsList:
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
                    elif f.find('{}-particlesPerHole_bin'.format(grid)) != -1:
                        dictFiles['particlesPerHole_bin'] = f
                    elif f.find('{}-classes-'.format(grid)) != -1:
                        classNum = f[f.find('class'):]
                        match = re.search(r"\d+", classNum)
                        if match:
                            dictFiles[f'class-{int(match.group())}'] = f

            self.numClasses = range(sum(1 for key in dictFiles if "class" in key))
            self.listRanges = {
                'xBin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['xBin'])),
                'holeCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeCount'])),
                'holeTotalCount': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['holeTotalCount'])),
                'bin_edges': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['bin_edges'])),
                'good_bin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['goodBin'])),
                'good_binTotal': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['good_binTotal'])),
                'badParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['badParticles'])),
                'totalParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['totalParticles'])),
                'stdTotalParticles': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['stdTotalParticles'])),
                'percentGood': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['percentGood'])),
                'particlesPerHole_bin': np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles['particlesPerHole_bin'])),
            }

            self.classesList = [c for c, v in dictFiles.items() if "-classes-" in v]
            for v in self.classesList:
                self.listRanges[v] = np.loadtxt(os.path.join(self.protocol._getExtraPath(), dictFiles[v]))
            self.classesList = sorted(self.classesList, key=lambda x: int(x.split('-')[1]))

            self.classImagesDict = {}
            for c in self.protocol.goodClasses2D.get():
                path_mrc = c.getRepresentative().getFileName()
                classNumber = c.getRepresentative().getIndex()
                self.classImagesDict[classNumber] = f"{classNumber}@{path_mrc}"

    def dataManipulation(self):
        self.matrix = np.vstack([self.listRanges[c] for c in self.classesList])
        self.xBin = self.listRanges['xBin']
        self.particles_per_class = self.matrix.sum(axis=1)

        col_sums = self.matrix.sum(axis=0)
        self.col_sums = np.where(col_sums != 0, col_sums, np.finfo(float).eps)
        self.percent_matrix = self.matrix / self.col_sums * 100  # each column sums to 100%

    def plotlySetup(self):
        # === Initialization of Plugin Variables ===
        self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
        self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
        self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)

        # === PyClient Setup ===
        self.pyClient = MainPyClient(self.token, self.endpoint)

        # === Persistent Shape Containers ===
        self.persistent_shapes_top = []
        self.persistent_shapes_bottom = []

        # === Histogram Configuration ===
        bin_width = (self.listRanges['bin_edges'][1] - self.listRanges['bin_edges'][0]) * 0.9
        n_cols_top = 3
        n_cols_bottom = 5
        titles = ["Num holes", "Mean particles per hole", "Percent good particles per hole"]
        row_heights = [0.3]

        # === Create Top Figure for Histograms ===
        fig_top = make_subplots(
            rows=1,
            cols=n_cols_top,
            subplot_titles=titles,
            vertical_spacing=0.05,
            horizontal_spacing=0.07,
            row_heights=row_heights
        )
        fig_top.update_layout(
            title_text="Histograms holes and particles",
            title_font=dict(size=20, color="darkblue", family="Arial, sans-serif"),
            title_x=0.5,
            width=1200,
            height=400,
            barmode="overlay",
            bargap=0.05,
            margin=dict(l=40, r=40, t=80, b=40),
        )

        listMaxYValues = []

        # === Subplot 1: Holes Count ===
        fig_top.add_trace(go.Bar(x=self.xBin, y=self.listRanges['holeTotalCount'],
                                 name="Total holes", marker=dict(color="gray"), width=bin_width), row=1, col=1)
        fig_top.add_trace(go.Bar(x=self.xBin, y=self.listRanges['holeCount'],
                                 name="Holes acquired", marker=dict(color="#7d498a"), width=bin_width), row=1, col=1)
        fig_top.update_xaxes(title="Holes Intensity", range=[min(self.xBin), max(self.xBin)], row=1, col=1)
        fig_top.update_yaxes(title="Count", title_standoff=2, row=1, col=1)
        listMaxYValues.append(max(self.listRanges['holeTotalCount']))

        # === Subplot 2: Particles Count ===
        fig_top.add_trace(go.Bar(x=self.xBin, y=self.listRanges['particlesPerHole_bin'],
                                 name="Particles per hole mean", marker=dict(color="#7d498a",
                                                                    pattern_shape=".",
                                                                    pattern_fgcolor="rgb(196, 230, 200)",
                                                                    pattern_size=7), width=bin_width), row=1, col=2)
        fig_top.update_xaxes(title="Holes Intensity", range=[min(self.xBin), max(self.xBin)], row=1, col=2)
        fig_top.update_yaxes(title="Particles pero hole", title_standoff=2, row=1, col=2)
        listMaxYValues.append(max(self.listRanges['particlesPerHole_bin']))

        # === Subplot 3: Percent Good ===
        fig_top.add_trace(go.Bar(x=self.xBin, y=self.listRanges['percentGood'] * 100,
                         name="Percent good particles", marker=dict(color="rgba(0,150,0,0.6)"), width=bin_width), row=1,  col=3)
        fig_top.update_xaxes(title="Holes Intensity", range=[min(self.xBin), max(self.xBin)], row=1, col=3)
        fig_top.update_yaxes(title="Percent good particles", title_standoff=2,  range=[0, 100], row=1, col=3)
        listMaxYValues.append(100)


        # === Create Bottom Figure for 2D Class Distribution ===
        n_classes = len(self.classesList)
        n_rows = math.ceil(n_classes / n_cols_bottom)

        indexClass = [(i, self.classesList[i], np.sum(self.particles_per_class[i])) for i in range(len(self.classesList))]
        indexClass_sort = sorted(indexClass, key=lambda x: x[2], reverse=True)
        titles = [cls for i, cls, suma in indexClass_sort]
        fig_bottom = make_subplots(
            subplot_titles=titles,
            rows=n_rows,
            cols=n_cols_bottom,
            vertical_spacing=0.08,
            horizontal_spacing=0.03
        )
        fig_bottom.update_layout(
            title_text="Particles distributions by 2DClass",
            title_font=dict(size=20, color="darkblue", family="Arial, sans-serif"),
            title_x=0.5,
            width=1200,
            height=200 * n_rows,
            barmode="overlay",
            bargap=0.05,
            margin=dict(l=40, r=40, t=120, b=40),
            showlegend=False,
        )

        ymax_global = np.nanmax(self.percent_matrix)

        # === Loop Through Classes and Add Subplots ===


        for i, element in enumerate(indexClass_sort):
            indexClass = element[0]
            cls = element[1]

        # for i, cls in enumerate(self.classesList):
            row = (i // n_cols_bottom) + 1
            col = (i % n_cols_bottom) + 1
            listMaxYValues.append(np.nanmax(self.percent_matrix[indexClass]))
            class_idx = int(cls.split('-')[1])
            img_ref = self.classImagesDict[class_idx]

            # === Load and Normalize Class Image ===
            if img_ref:
                idx, path_mrc = img_ref.split('@')
                idx = int(idx)
                with mrcfile.open(path_mrc) as mrc:
                    idx = idx % mrc.data.shape[0]
                    img_data = mrc.data[idx - 1]

                img_norm = 255 * (img_data - img_data.min()) / (img_data.ptp() + 1e-6)
                img_norm = img_norm.astype(np.uint8)
                img_pil = PILImage.fromarray(img_norm)

                # === Create Circular Mask ===
                w, h = img_pil.size
                mask = PILImage.new("L", (w, h), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, w, h), fill=255)

                # === Apply Mask and Encode Image ===
                img_circular = PILImage.new("RGBA", (w, h), (0, 0, 0, 0))
                img_circular.paste(img_pil, (0, 0), mask=mask)
                buffer = io.BytesIO()
                img_circular.save(buffer, format="PNG")
                encoded = base64.b64encode(buffer.getvalue()).decode()

                # === Add Annotation and Bar Plot ===
                fig_bottom.add_annotation(
                    text=f"N = {round(np.sum(self.particles_per_class[indexClass] / 1000), 1)}K",
                    xref=f"x{row}{col} domain",
                    yref=f"y{row}{col} domain",
                    x=0.95, y=0.95, showarrow=False,
                    row=row, col=col,
                    font=dict(color="black", size=12),
                    bgcolor="rgba(100,100,100,0.7)",
                    bordercolor="gray", borderwidth=2, borderpad=5,
                )
                fig_bottom.add_trace(go.Bar(
                    x=self.xBin,
                    y=self.percent_matrix[indexClass],
                    name=f"Class-{class_idx}",
                    marker=dict(color="rgba(0,150,0,0.6)"),
                    width=bin_width
                ), row=row, col=col)
                fig_bottom.update_yaxes(showgrid=False, row=row, col=col)
                if col == 1:
                    fig_bottom.update_yaxes(title="Percentage (%)", row=row, col=col)

                # === Set Y-Axis Range for All Subplots ===
                for j in range(len(self.classesList)):
                    row = (j // n_cols_bottom) + 1
                    col = (j % n_cols_bottom) + 1
                    fig_bottom.update_yaxes(range=[0, ymax_global], row=row, col=col)

                # === Add Image Overlay to Subplot ===
                subplot_num = i + 1
                xref_val = 'x domain' if subplot_num == 1 else f'x{subplot_num} domain'
                yref_val = 'y domain' if subplot_num == 1 else f'y{subplot_num} domain'
                fig_bottom.add_layout_image(
                    dict(
                        source=f"data:image/png;base64,{encoded}",
                        xref=xref_val, yref=yref_val,
                        x=0.05, y=0.95,
                        sizex=0.35, sizey=0.5,
                        xanchor="left", yanchor="top",
                        sizing="stretch", opacity=0.9,
                        layer="above"
                    )
                )
        # === Dash App Initialization ===
        x_min = min(self.xBin)
        x_max = max(self.xBin)
        x_minRound = int(x_min) - (int(x_min) % 10)

        app = Dash(__name__)
        app.title = "Scipion-em-Smartscope"

        # === Controls Panel Layout ===
        controls_div = html.Div([
            html.Label("Intensity (ice-thickness) range to select",
                       style={
                           'font-size': '20px',
                           'color': 'darkblue',
                           'margin-bottom': '5px',
                           'display': 'block'
                       }),
            html.Div([
                html.A(
                    html.Button(
                        "Open Smartscope session",
                        id='smartscope-button',
                        n_clicks=0,
                        style={
                            'background-color': '#6A6A6A',
                            'color': 'white',
                            'font-weight': 'bold',
                            'padding': '10px 20px',
                            'border-radius': '8px',
                            'border': 'none',
                            'box-shadow': '2px 2px 5px rgba(0,0,0,0.3)',
                            'cursor': 'pointer'
                        }
                    ),
                    href=self.urlSmartscope,
                    target="_blank"
                ),
                html.Div([
                    dcc.RangeSlider(
                        id='x-range-slider',
                        min=int(x_min),
                        max=int(x_max),
                        step=1,
                        value=[x_minRound, int(x_max)],
                        marks={x_minRound: str(x_minRound), int(x_max): str(int(x_max))},
                        tooltip={"placement": "top", "always_visible": True}
                    )
                ], style={'width': '600px'}),
                html.Button(
                    "Apply to Smartscope",
                    id='apply-button',
                    n_clicks=0,
                    style={
                        'background-color': '#007BFF',
                        'color': 'rgba(255, 228, 196, 1)',
                        'font-weight': 'bold',
                        'padding': '10px 20px',
                        'border-radius': '8px',
                        'border': 'none',
                        'box-shadow': '2px 2px 5px rgba(0,0,0,0.3)',
                        'cursor': 'pointer'
                    }
                )
            ], style={'width': '100%', 'display': 'flex', 'flex-direction': 'row', 'align-items': 'center'}),
            html.Div([
                html.Button(
                    "Check the current Intensity Range on Smartscope session",
                    id='apply-Checkbutton',
                    n_clicks=0,
                    style={
                        'background-color': 'rgba(255, 228, 196, 0.5)',
                        'color': '#8B4513',
                        'font-weight': 'bold',
                        'padding': '10px 20px',
                        'border-radius': '8px',
                        'border': 'none',
                        'box-shadow': '2px 2px 5px rgba(0,0,0,0.3)',
                        'cursor': 'pointer'
                    }
                )
            ], style={'display': 'flex', 'margin-top': '5px', 'gap': '20px', 'flex-direction': 'row',
                      'justify-content': 'center'})
        ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center', 'gap': '15px'})

        # === Load and Encode Logos ===
        smartscope_icon = Path(__file__).parent / '../icon.png'
        scipion_icon = Path(__file__).parent / '../objects/scipion_logo_normal.png'
        encoded_image_smartscope = base64.b64encode(smartscope_icon.read_bytes()).decode()
        encoded_image_scipion = base64.b64encode(scipion_icon.read_bytes()).decode()

        # === App Layout Definition ===
        app.layout = html.Div([
            html.Div([
                html.Div([
                    html.Img(src=f"data:image/png;base64,{encoded_image_smartscope}",
                             style={'height': '50px', 'margin-bottom': '10px'}),
                    html.Img(src=f"data:image/png;base64,{encoded_image_scipion}", style={'height': '50px'}),
                ]),
                html.Div([
                    html.Div(f"Scipion project: {self._project.getShortName()}"),
                    *[html.Div(line) for line in self.sessionDetails.split('\n')]
                ], style={'font-size': '14px'}),
            ], style={
                'display': 'flex',
                'flex-direction': 'row',
                'align-items': 'center',
                'padding': '10px',
            }),

            # === Top Graph Display ===
            dcc.Graph(
                id='graph-top',
                figure=fig_top,
                style={'margin-bottom': '20px'}
            ),
            dcc.Loading(
                id='loading-overlay',
                type='circle',
                children=html.Div(),  # vacío, solo para activar el spinner
                style={
                    'position': 'absolute',
                    'top': '70%',
                    'left': '50%',
                    'transform': 'translate(-50%, -50%) scale(2)',
                    'zIndex': '10'
                }
            )        ,    # === Controls Panel ===
            controls_div,

            # === Bottom Graph Display ===
            dcc.Graph(
                id='graph-bottom',
                figure=fig_bottom
            )

        ], style={
            'display': 'flex',
            'flex-direction': 'column',
            'align-items': 'center',
            'width': '100%'
        })

        # === Callback: Highlight Area on Graphs ===
        @app.callback(
            Output('graph-top', 'figure'),
            Output('graph-bottom', 'figure'),
            Output('loading-overlay', 'children'),
            Input('apply-button', 'n_clicks'),
            Input('apply-Checkbutton', 'n_clicks'),
            Input('x-range-slider', 'value'),
        )
        # === Callback Function: Update Highlighted Range on Graphs ==
        def update_highlight(n_apply, n_check, x_range):
            triggered_id = dash.ctx.triggered_id
            print(f"Range selected: {x_range}")

            # Create fresh copies of the figures
            new_fig_top = go.Figure(fig_top)
            new_fig_bottom = go.Figure(fig_bottom)

            # Retrieve existing shapes from layout
            existing_shapes_top = list(new_fig_top.layout.shapes) if "shapes" in new_fig_top.layout else []
            existing_shapes_bottom = list(new_fig_bottom.layout.shapes) if "shapes" in new_fig_bottom.layout else []

            # Add persistent shapes stored from previous interactions
            existing_shapes_top += self.persistent_shapes_top
            existing_shapes_bottom += self.persistent_shapes_bottom

            # === Case: Slider is being moved (Preview Mode) ===
            if triggered_id == 'x-range-slider':
                # Add dashed vertical lines to top figure subplots
                for i in range(1, 4):
                    existing_shapes_top.append(dict(
                        type="line",
                        xref=f"x{i}", yref=f"y{i}",
                        x0=x_range[0], x1=x_range[0],
                        y0=0, y1=listMaxYValues[i - 1],
                        line=dict(color='#007BFF', width=2.5, dash="dash")
                    ))
                    existing_shapes_top.append(dict(
                        type="line",
                        xref=f"x{i}", yref=f"y{i}",
                        x0=x_range[1], x1=x_range[1],
                        y0=0, y1=listMaxYValues[i - 1],
                        line=dict(color='#007BFF', width=2.5, dash="dash")
                    ))

                # Add dashed vertical lines to bottom figure subplots
                for i in range(1, n_classes + 1):
                    existing_shapes_bottom.append(dict(
                        type="line",
                        xref=f"x{i}", yref=f"y{i}",
                        x0=x_range[0], x1=x_range[0],
                        y0=0, y1=np.nanmax(self.percent_matrix),
                        line=dict(color='#007BFF', width=2.5, dash="dash")
                    ))
                    existing_shapes_bottom.append(dict(
                        type="line",
                        xref=f"x{i}", yref=f"y{i}",
                        x0=x_range[1], x1=x_range[1],
                        y0=0, y1=np.nanmax(self.percent_matrix),
                        line=dict(color='#007BFF', width=2.5, dash="dash")
                    ))

            # === Case: "Apply" button clicked (Save Range) ===
            elif triggered_id == 'apply-button':
                print(f'Button clicked: Range: {x_range}')
                self.settingRangeSmartscope(x_range[0], x_range[1])
                existing_shapes_top, existing_shapes_bottom = applyCheckButton(existing_shapes_top, existing_shapes_bottom)

            # === Case: "Check" button clicked (Display Saved Range) ===
            elif triggered_id == 'apply-Checkbutton':
                existing_shapes_top, existing_shapes_bottom = applyCheckButton(existing_shapes_top, existing_shapes_bottom)

            # === Update figures with new shapes ===
            new_fig_top.update_layout(shapes=existing_shapes_top)
            new_fig_bottom.update_layout(shapes=existing_shapes_bottom)

            return new_fig_top, new_fig_bottom, html.Div()

        def applyCheckButton(existing_shapes_top, existing_shapes_bottom):
            ranges = self.collectingRangeSmartscope()
            self.persistent_shapes_top.clear()
            self.persistent_shapes_bottom.clear()
            # Add solid lines to top figure subplots
            for i in range(1, 4):
                for x_val in ranges:
                    shape = dict(
                        type="line",
                        xref=f"x{i}", yref=f"y{i}",
                        x0=x_val, x1=x_val,
                        y0=0, y1=listMaxYValues[i - 1],
                        fillcolor="rgba(255, 228, 196, 0.5)",
                        line=dict(color='#8B4513', width=2.5, dash="solid"),
                    )
                    self.persistent_shapes_top.append(shape)
                    existing_shapes_top.append(shape)

            # Add solid lines to bottom figure subplots
            for i in range(1, n_classes + 1):
                for x_val in ranges:
                    shape = dict(
                        type="line",
                        xref=f"x{i}", yref=f"y{i}",
                        x0=x_val, x1=x_val,
                        y0=0, y1=np.nanmax(self.percent_matrix),
                        fillcolor="rgba(255, 228, 196, 0.5)",
                        line=dict(color='#8B4513', width=2.5, dash="solid"),
                    )
                    self.persistent_shapes_bottom.append(shape)
                    existing_shapes_bottom.append(shape)

            return existing_shapes_top, existing_shapes_bottom


        # === Launch Dash Server in Background ===
        def open_browser():
            # Open the Dash app in the default web browser
            webbrowser.open("http://127.0.0.1:8050/")

        def run_dash():
            # Start the Dash server without reloading
            app.run_server(debug=False, port=8050, use_reloader=False)

        # Start Dash server in a background thread and open browser after 1 second
        threading.Thread(target=run_dash, daemon=True).start()
        threading.Timer(1, open_browser).start()
        print("Server Dash running: http://127.0.0.1:8050/")

        # === Retrieve Intensity Range from Smartscope ===
    def collectingRangeSmartscope(self):
        for i, grid in enumerate(self.gridsList):
            gridID = self.gridsIdList[i]
            self.info(f'\n -Posting Back to Smartscope Grid: grid: {gridID}')

            # Request current intensity range from Smartscope
            status, currentRange = self.pyClient.getRangeOfIntensityGrid(gridID, magLevel='square', devel=True)
            currentMinRange, currentMaxRange = currentRange['low_limit'], currentRange['high_limit']
            print(f'status: {status}, currentRange: {currentMinRange, currentMaxRange}')

            if status:
                return int(currentMinRange), int(currentMaxRange)

    # === Set Intensity Range in Smartscope ===
    def settingRangeSmartscope(self, LowI, hightI):
        print(f'Setting Intensity range to smartscope: {LowI} - {hightI}')

        for i, grid in enumerate(self.gridsList):
            gridID = self.gridsIdList[i]

            # Post new intensity range to Smartscope
            self.pyClient.postRangeIntensity(ID=gridID, data={"low_limit": LowI, "high_limit": hightI})
            time.sleep(10)  # Wait for Smartscope to process the update

            # Confirm the range was correctly set
            status, currentRange = self.pyClient.getRangeOfIntensityGrid(gridID, magLevel='square', devel=True)
            if status and currentRange['low_limit'] == LowI and currentRange['high_limit'] == hightI:
                return True
            else:
                return False