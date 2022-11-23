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
from ..objects.data import *
from pwem.viewers import DataView, ObjectView
from pwem.viewers.showj import ORDER, VISIBLE, MODE, RENDER, MODE_MD

class DataViewer_cnb(DataViewer):
    _targets = [SetOfLowMagImages]

    def _visualize(self, obj, **kwargs):
        self._views.append(DataView(obj.getFileName()))
        return self._views

    # def _visualize(self, obj, **kwargs):
    #     fn = obj.getFileName()
    #     # Enabled for the future has to be available
    #     labels = ('_PieceCoordinates _MinMaxMean _TiltAngle _StagePosition _StageZl ')
    #     renderLabels = '_filename '
    #     moviesView = self._addObjView(obj, fn, {ORDER: labels,
    #                                             VISIBLE: labels,
    #                                             MODE: MODE_MD,
    #                                             RENDER: renderLabels})
    #     return moviesView

