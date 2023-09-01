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
    This protocol provide the CTF and or the alignment to Smartscope
    """
    _label = 'provide smartscope calculations'
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


        #sesion de Smartscope -> para cada hole pregunto de que sesion viene su grid
        form.addParam('goodClasses2D', params.PointerParam,
                       pointerClass='SetOfCtf',
                       label="CTF",
                       help='Set of CTFs')

        form.addParam('badClasses2D', params.PointerParam,
                       pointerClass='SetOfMicrographs',
                       label='Set of micrographs',
                       help='Set of micrographs aligned')

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


    def readCTF(self):
        '''
        Get the movie of the CTF, and get the highmag id (hm_id)
        Run postCTF with the parameters to post
        :return:
        '''
        pass

    def readMicrograph(self):
        pass

    def postCTF(self):
        pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
                                     data={"astig": '100.00'})
        pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
                                 data={"ctffit": '100.00'})
        pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
                                 data={"defocus": '100.00'})
        pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
                                 data={"offset": '100.00'})
    def postMicrograph(self):
        pass




    def _summary(self):
        summary = []


        return summary


    def _validate(self):
        errors = []
        self._validateThreads(errors)

        return errors