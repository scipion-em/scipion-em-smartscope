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
This protocol connect with smartscope in streaming. Recives all information
from the API, collect it in Scipion objects and will be able to communicate
to Smartscope to take decission about the acquisition
"""
from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from pwem.protocols.protocol_import.base import ProtImport
from pyworkflow.protocol import ProtStreamingBase
import pyworkflow.utils as pwutils
from smartscope import Plugin
from pyworkflow.object import Set

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *

class smartscopeFeedback(ProtImport, ProtStreamingBase):
    """
    This protocol will calculate which are the best holes of the session based
     on the good particles of each hole. After knowing the good holes, will
     sort the queue of hole acquisition that Smartscope uses.
    """
    _label = 'smartscope feedback'
    _devStatus = BETA

    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL

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
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputHoles', params.PointerParam, pointerClass='SetOfHoles',
                      important=True,
                      label='Input holes from Smartscope',
                      help='Select a set of holes from Smartscope connection protocol.')


        form.addParam('inputMovies', params.PointerParam, pointerClass='SetOfMoviesSS',
                      important=True,
                      label='Input movies from Smartscope',
                      help='Select a set of movies from Smartscope connection protocol.')

        #sesion de Smartscope -> para cada hole pregunto de que sesion viene su grid
        form.addParam('goodClasses2D', params.PointerParam,
                       pointerClass='SetOfClasses2D',
                       label="Good Classes2D",
                       help='Set of good Classes2D calculated by a ranker')

        form.addParam('badClasses2D', params.PointerParam,
                       pointerClass='SetOfClasses2D',
                       label="Bad Classes2D",
                       help='Set of bad Classes2D calculated by a ranker')

        form.addSection('Streaming')
        form.addParam('refreshTime', params.IntParam, default=120,
                      label="Time to refresh Smartscope synchronization (secs)")


    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """

        while True:
            pass


    def readClasses(self):
        pass

    def writeOnHoles(self):
        '''
        Write the number of good particles, bad particles, total particles,
         GrayScaleCluster, CTFResolution, status,
        :return:
        '''
        pass

    def holesStatistis(self):
        '''
        Determine good and bad holes and sort the holes for the acquisition
        :return:
        '''
        pass

    def sortSmartscopeQueue(self):
        '''
        connect to the Smartscope API and provide the sorted queue
        :return:
        '''
        pass

    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response

    def _summary(self):
        summary = []


        return summary


    def _validate(self):
        errors = []
        self._validateThreads(errors)

        response = self.checkSmartscopeConnection()
        try:
            response[0]['username']
        except Exception as e:
            try:
                errors.append('Error Smartscope connection:\n{}'.format(response['detail']))
            except Exception:
                errors.append('Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(response))

        return errors