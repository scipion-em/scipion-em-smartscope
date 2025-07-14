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
from pwem.protocols import EMProtocol

from smartscope import Plugin
from pyworkflow.protocol import params, StringParam
from pwem.objects import SetOfMicrographs, Micrograph
from ..objects.dataCollection import *
from . import smartscopeConnection
from collections import defaultdict

#external imports

class smartscopeSimulator(EMProtocol):
    """
    This protocol will simulate a streaming acquisition with Smartscope. It simulate the set of intensity range calculated by the Feedback micrograph protocol
    The protocol takes the first set of micrographs, the intensityRange calculated for the Feedback Micrograph prptocol and a nes set of micrograph.
    The protocol returns a set of micrographs with the first set unaltered and the second crop by the intensity range criteria.
    """
    _label = 'Simulator'
    _devStatus = BETA
    _possibleOutputs = {"outputMicrographs" : SetOfMicrographs}


    def __init__(self, **args):
        EMProtocol.__init__(self, **args)

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
        form.addParam('micsNoFiltered', params.PointerParam, pointerClass='SetOfMicrographs',
                      important=True, allowsNull=False,
                      label='Second set of  micrographs',
                      help='Second set of micrographs.')
        form.addParam('intensityRange', params.StringParam, important=True, allowsPointers=True,
                      label="Intensity Range", pointerClass= StringParam,
                      help='Intensity Range calculated by Feedback Micrograph protocol with the first set of micrographs')

    def _initialize(self):
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
        self.micsInsideRange = SetOfMicrographs.create(outputPath=self._getPath())
        self.dictHoles = {}
        self.dictMovies = {}
        self.setOfMicsNoFiltered = self.micsNoFiltered.get()
        self.smartscopeConnectionProtocol = self.getInputProtocol()
        updatedProt = getUpdatedProtocol(self.smartscopeConnectionProtocol)
        if hasattr(updatedProt, 'MoviesSS'):
            self.movies = updatedProt.MoviesSS
        if hasattr(updatedProt, 'Holes'):
            self.holes = updatedProt.Holes
        self.intensityRangeList = [float(x.strip()) for x in self.intensityRange.get().split('-')]

    def getInputProtocol(self):
        prot = self.inputProtocol.get()
        prot.setProject(self.getProject())
        if isinstance(prot, smartscopeConnection):
            return prot
        else:
            return False

    def _insertAllSteps(self):
        self._initialize()
        self.filterMicByIntensity()
        self.createOutput()

    def filterMicByIntensity(self):
        self.info('\n-Filtering micrographs by intensity hole ...')

        for hole in self.holes:
            holeC = hole.clone()
            self.dictHoles[hole.getHoleId()] = {'Hole':  holeC, 'GridID': holeC.getGridId(), 'Shots': hole.getShots(), 'Intensity': holeC.getSelectorValue()}

        for m in self.movies:
            self.dictMovies[m.getMicName()] = m.getHoleId()

        self.micsInsideRange.copyInfo(self.setOfMicsNoFiltered)
        # for mic in self.setOfMicsNoFiltered.iterItems(iterate=False):
        #
        #     holeId = self.dictMovies[mic.getMicName()]
        #     intensityHole = self.dictHoles[holeId]['Intensity']
        #     if min(self.intensityRangeList) <= intensityHole <= max(self.intensityRangeList):
        #         mic2Add = mic.clone()
        #         self.micsInsideRange.append(mic2Add)
        self.micsInsideRange.write()

    def createOutput(self):
        self.info('\n-Generating outputs ...')
        self.outputsToDefine = {"outputMicrographs" : self.micsInsideRange}
        self._defineOutputs(outputMicrographs=self.outputsToDefine)
        #self._store()


