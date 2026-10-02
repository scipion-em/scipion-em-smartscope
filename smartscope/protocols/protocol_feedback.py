# **************************************************************************
# *
# * Authors: Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)# *
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
from pwem.protocols import ProtBoxSizeCheckpoint
from pyworkflow.protocol import ProtStreamingBase, getUpdatedProtocol
from pwem.objects import SetOfClasses2D, SetOfAverages, Class2D, SetOfMicrographs
from . import smartscopeConnection

import pyworkflow.utils as pwutils
from smartscope import Plugin
from pyworkflow.object import Set
from ..objects.data import Hole

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *
from collections import defaultdict
import numpy as np

NUMBER_HOLES_TO_VIEW = 100


class smartscopeFeedback2D(ProtImport, ProtStreamingBase):
    """
    This protocol will provide a weight distribution for the intensity ranges (ice tickness ranges)
    based on the processing pipeline. If only is provided the micrographs filtered, it will provide a weight distribution
    based on the percent of good holes (holes with micrographs whis pass the threshold - mainly resolution threshold)
    If the 2D class distribution and good class distribution is provided, it will provide a weight distribution based on
    the percent of good particles of each range of intensity and for each good class, will be inversely proportional to the
    population of each class. If both sets are provided the weight will be calculated taking in to acount both statistics.
    """
    _label = 'Feedback'
    _devStatus = BETA
    _possibleOutputs = {'SetOfHoles': SetOfHoles,
                        'SetOfHolesRejected': SetOfHoles,
                         'SetOfHolesPassFilter': SetOfHoles}
    percentBins = ['0','10','20', '30', '40', '50', '60', '70', '80', '90']

    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        #self.stepsExecutionMode = STEPS_PARALLEL

        self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
        self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
        self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)

        self.pyClient = MainPyClient(self.token, self.endpoint)
        self.connectionClient = dataCollection(self.pyClient)


    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # --------------------------- INPUT section ---------------------------
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputProtocol', params.PointerParam,
                      pointerClass='EMProtocol', label="Input Smartscope connection", important=True,
                      help="Smartscope connection protocol")

        # --------------------------- 2D feedback section ---------------------
        form.addSection(label='Feedback from particles')
        form.addParam('totalClasses2D', params.PointerParam, allowsNull=False,
                       pointerClass='SetOfClasses2D',
                       label="Classes2D",
                       help='Set of Classes2D calculated by a classifier')
        form.addParam('goodClassesOrigin', params.EnumParam, default=0,
                      choices=['Relion', 'Cryoasses'],
                      display=params.EnumParam.DISPLAY_HLIST,
                      label='Select the protocol that generate the good2Dclasses ranked',
                      help='Relion generates setOf2DClasses and Cryoasses SetOfAverages, select the protocol the good classes come from.')
        form.addParam('goodClasses2DRelion', params.PointerParam,
                       condition='goodClassesOrigin==0',
                       pointerClass='SetOfClasses2D',
                       label="Good Classes2D from Relion",
                       help='Set of good Classes2D calculated by Relion ranker')
        form.addParam('goodClasses2DCryoasses', params.PointerParam,
                       condition='goodClassesOrigin==1',
                       pointerClass='SetOfAverages',
                       label="Good Classes2D from Cryoasses",
                       help='Set of good Classes2D calculated by Cryoasses ranker')
        form.addParam('percentGoodPartcilesHole', params.EnumParam,
                      choices=self.percentBins, default=5, display=params.EnumParam.DISPLAY_COMBO,
                      label="Percent good particles to consider good Hole",
                      help="Percent of good particles in a Hole to consider that the hole is a good Hole or a Hole to consider. Default 50%")
        form.addParam('micrographs', params.PointerParam,
                       pointerClass='SetOfMicrographs',
                       label="Microgaphs",
                       help='Micrographs')

        # --------------------------- Filter feedback section -----------------
        form.addSection(label='Feedback from micrographs')
        form.addParam('micsPassFilter', params.PointerParam, pointerClass='SetOfMicrographs',
                      important=True, allowsNull=False,
                      label='Filtered micrographs',
                      help='Select a set of micrographs filtered by any protocol.')
        form.addParam('triggerMicrograph', params.IntParam, default=200,
                      label="Micrographs to launch the protocol",
                      help='Number of micrographs that pass the filters to launch the statistics')
        form.addParam('emptyBinsPercent', params.EnumParam,
                      choices=self.percentBins, default=2, display=params.EnumParam.DISPLAY_COMBO,
                      label="Percent empty bins in the histogram",
                      help="In the histogram of number of holes acquired (with movies), this parameter represent the"
                            " percent of empty bins allowed to feedback Smartscope (20% by default). Higher less restrictive")
        form.addParam('applyFeedback', params.BooleanParam, default=False, allowsNull=False,
                      label='Apply the calculated range of intensity back to Smartscope',
                      help='Set True if you want to apply the range of intensity (ice-thickness) back to Smartscope in real time')
        form.addParam('simulator', params.BooleanParam, default=False,
                      expertLevel=params.LEVEL_ADVANCED,
                      label="Enable to simulate the screening",
                      help='If True the number of movies available will be the ones related to the micrographs. If False the number of movies will be the number reported by SmartscopeConnection')
        form.addParam('micsAll', params.PointerParam, pointerClass='SetOfMicrographs',
                      expertLevel=params.LEVEL_ADVANCED, allowsNull=True,
                      label='Micrographs',
                      help='Select a set of micrographs from any protocol if you are simulating')

        # --------------------------- Streaming section -----------------------
        form.addSection('Streaming')
        form.addParam('refreshMethod', params.EnumParam, default=0,
                      choices=['Input micrographs', 'Time'],
                      display=params.EnumParam.DISPLAY_HLIST,
                      label='Select input to refresh the protocol',
                      help='Select the parameter which triger the refresh of the protocol.')
        form.addParam('refreshTime', params.IntParam, default=240,
                      condition='refreshMethod==1',
                      label="Time to refresh protocol",
                      help="Time to refresh data collected (minimum 240 secs) and update the feedback if neccesary")
        form.addParam('refreshMics', params.IntParam, default=200,
                      condition='refreshMethod==0',
                      label='Input micrographs to refresh protocol',
                      help="Number of new micrographs to refresh data collected and update the feedback if neccesary")

