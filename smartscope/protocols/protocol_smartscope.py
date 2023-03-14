# -*- coding: utf-8 -*-
# **************************************************************************
# *
# * Authors:     you (you@yourinstitution.email)
# *
# * your institution
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
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
# *  e-mail address 'you@yourinstitution.email'
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



    # --------------------------- STEPS functions ------------------------------
    def _initialize(self):
        self.connectionClient = dataCollection(
            Authorization=self.Authorization,
            endpoint=self.endpoint)
    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep(self._initialize)
        self._insertFunctionStep('metadataCollection')
        self._insertFunctionStep('screeningCollection')

    def metadataCollection(self):
        self.connectionClient.metadataCollection()

        print('Microscopes: ')
        print(self.connectionClient.microscopeList)

        print('Detectors: ')
        print(len(self.connectionClient.detectorList))

        print('Sessions elements: ')
        print(len(self.connectionClient.sessionList))


    def screeningCollection(self):
        self.connectionClient.screeningCollection()



    def createOutputStep(self):
        # register how many times the message has been printed
        # Now count will be an accumulated value
        #self._defineOutputs(count=)
        pass

    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        """ Summarize what the protocol has done"""
        summary = []

        if self.isFinished():
            summary.append("This protocol has printed *%s* %i times." % (self.message, self.times))
        return summary

    def _methods(self):
        methods = []

        if self.isFinished():
            methods.append("%s has been printed in this run %i times." % (self.message, self.times))
            if self.previousCount.hasPointer():
                methods.append("Accumulated count from previous runs were %i."
                               " In total, %s messages has been printed."
                               % (self.previousCount, self.count))
        return methods
