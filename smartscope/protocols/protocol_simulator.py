# **************************************************************************
# *
# * Authors: Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)
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

"""
This protocol connect with smartscope in streaming. Recives all information
from the API, collect it in Scipion objects and will be able to communicate
to Smartscope to take decission about the acquisition
"""
from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from pwem.protocols.protocol_import.base import ProtImport
from pyworkflow.protocol import ProtStreamingBase, getUpdatedProtocol
from smartscope import Plugin
from pyworkflow.protocol import params, StringParam
from pwem.objects import SetOfMicrographs
from ..objects.dataCollection import *
from . import smartscopeConnection
from collections import defaultdict

#external imports

class smartscopeSimulator(ProtImport):
    """
    This protocol will simulate a streaming acquisition with Smartscope. It simulate the set of intensity range calculated by the Feedback micrograph protocol
    The protocol takes the first set of micrographs, the intensityRange calculated for the Feedback Micrograph prptocol and a nes set of micrograph.
    The protocol returns a set of micrographs with the first set unaltered and the second crop by the intensity range criteria.
    """
    _label = 'Simulator'
    _devStatus = BETA
    _possibleOutputs = {"outputMicrographs" : SetOfMicrographs}


    def __init__(self, **args):
        ProtImport.__init__(self, **args)

    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputProtocol', params.PointerParam,
                      pointerClass='EMProtocol', label="Input Smartscope connection protocols", important=True,
                      help="Smartscope connection protocol")
        form.addParam('micsFiltered', params.PointerParam,
                      pointerClass='SetOfMicrographs', label="Set of micrographs filtered", important=True,
                      help="First set of micrographs with the IntensityRange calculated by Feedback micrograph protocol")
        form.addParam('micsNoFiltered', params.PointerParam, pointerClass='SetOfMicrographs',
                      important=True, allowsNull=False,
                      label='Second set of  micrographs',
                      help='Second set of micrographs.')
        form.addParam('intensityRange', params.StringParam, important=True, allowsPointers=True,
                      label="Intensity Range", pointerClass= StringParam,
                      help='Intensity Range calculated by Feedback Micrograph protocol with the first set of micrographs')

    def _initialize(self):
        self.micsInsideRange = set()
        self.setOfMicsNoFiltered = self.micsNoFiltered.get()
        updatedProt = getUpdatedProtocol(self.smartscopeConnectionProtocol)
        if hasattr(updatedProt, 'MoviesSS'):
            self.movies = updatedProt.MoviesSS
        if hasattr(updatedProt, 'Holes'):
            self.holes = updatedProt.Holes
        self.intensityRangeList = [float(x.strip()) for x in self.intensityRange.get().split('-')]

    def _insertAllSteps(self):
        self._initialize()
        self.filterMicByIntensity()
        self.joinMicrographs()
        self.createOutput()

    def filterMicByIntensity(self):
        self.info('\n-Filtering micrographs by intensity hole ...')

        for hole in self.holes:
            holeC = hole.clone()
            self.dictHoles[hole.getHoleId()] = {'Hole':  holeC, 'GridID': holeC.getGridId(), 'Shots': hole.getShots(), 'Intensity': holeC.getSelectorValue()}

        for m in self.movies:
            self.dictMovies[m.getMicName()] = m.clone()

        for mic in self.setOfMicsNoFiltered:
            holeId = self.dictMovies[mic.getMicName()].getHoleId()
            intensityHole = self.dictHoles[holeId].getSelectorValue()
            if min(self.intensityRangeList) <= intensityHole <= max(self.intensityRangeList):
                self.micsInsideRange.add(mic.copy())

    def joinMicrographs(self):
        self.info('\n-Joinning sets of micrographs ...')
        self.joinedSetOfMics = self.micsInsideRange.union(self.micsFiltered.get())

    def createOutput(self):
        self.info('\n-Generating outputs ...')
        self.outputsToDefine = {"outputMicrographs" : self.joinedSetOfMics}
        self._defineOutputs(**self.outputsToDefine)


