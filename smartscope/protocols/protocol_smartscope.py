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

"""
This protocol connect with smartscope in streaming. Recive all information
from the API, collect it in Scipion objects and will be able to communicate
to Smartscope to take decission about the acquisition
"""
from pyworkflow.protocol import Protocol, params, Integer
from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from ..objects.data import *
from ..objects.dataCollection import *
import time

class smartscopeConnection(Protocol):
    """
    This protocol will print hello world in the console
    IMPORTANT: Classes names should be unique, better prefix them
    """
    _label = 'smartscope connection'
    _devStatus = BETA

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('Authorization', params.StringParam,
                      default='Token ...',
                      label='Authorization token', important=True,
                      help='Provide the authorization token to communicate to Smartscope'
                           'Token xxxxc9f9fceb89117ae61b9dc0b5adxxxxxxxxxxxx')

        form.addParam('endpoint', params.StringParam,
                      default='http://localhost:48000/api/',
                      label='endpoint', important=True,
                      help='The url to connect to Smartscope.'
                           ' Check the port set up to smartscope in the installation.')

        form.addParam('dataPath', params.StringParam,
                      default='',
                      label='Smartscope data path', important=True,
                      help='Path assigned to the data in the Smartscope installation')



    # --------------------------- STEPS functions ------------------------------
    def _initialize(self):
        self.connectionClient = dataCollection(
            Authorization=self.Authorization,
            endpoint=self.endpoint)
        self.acquisition = Acquisition()
        self.microscopeList = [] #list of microscope Scipion object
        self.detectorList = [] #list of detector Scipion object
        self.sessionList = []#list of sessions Scipion object
        self.setOfGrids = SetOfGrids.create(outputPath=self._getPath())
        self.setOfAtlas = SetOfAtlas.create(outputPath=self._getPath())
        self.setOfSquares = SetOfSquares.create(outputPath=self._getPath())
        self.setOfHoles = SetOfHoles.create(outputPath=self._getPath())
        self.setOfMovies = SetOfMoviesSS.create(outputPath=self._getPath())

    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep(self._initialize)
        self._insertFunctionStep(self.metadataCollection)
        self._insertFunctionStep(self.screeningCollection)
        self._insertFunctionStep(self.createOutputStep)


    def metadataCollection(self):
        self.connectionClient.metadataCollection(self.microscopeList,
                                                 self.detectorList,
                                                 self.sessionList,
                                                 self.acquisition)

        print('Microscopes: ', len(self.microscopeList))
        print('Detectors: ', len(self.detectorList))
        print('Sessions elements: ', len(self.sessionList))

        self.sessionId = '20230216pruebaguenaQHCyjsBSSMq'
        self.sessionName = 'pruebaguena'

        # self.sessionId = '20230323speedFXaazIWcNSJSoQeaY'
        # self.sessionName = 'speed'

    def screeningCollection(self):
        start = time.time()
        self.connectionClient.screeningCollection(self.dataPath,
                                                  self.sessionId,
                                                  self.sessionName,
                                                  self.setOfGrids,
                                                  self.setOfAtlas,
                                                  self.setOfSquares,
                                                  self.setOfHoles,
                                                  self.setOfMovies,
                                                  self.acquisition)
        print('ScreeningTime: {}s'.format(round(time.time() - start, 1)))

        self.setOfGrids.write()
        self.setOfAtlas.write()
        self.setOfSquares.write()
        self.setOfHoles.write()
        self.setOfMovies.write()
        self._store(self.setOfGrids)
        self._store(self.setOfAtlas)
        self._store(self.setOfSquares)
        self._store(self.setOfHoles)
        self._store(self.setOfMovies)



    def createOutputStep(self):
        self.outputsToDefine = {'Squares': self.setOfSquares,
                                 'Atlas': self.setOfAtlas,
                                 'Grids': self.setOfGrids,
                                 'Holes': self.setOfHoles,
                                 'Movies': self.setOfMovies}

        self._defineOutputs(**self.outputsToDefine)
        self._store(self.setOfSquares)

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():
            summary.append("This protocol has printed *%s* %i times." % (self.message, self.times))
        return summary

