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
from ..objects.data import Hole

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
    _label = 'Smartscope feedback'
    _devStatus = BETA
    _possibleOutputs = {'SetOfHoles': SetOfHoles}

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
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)

        form.addParam('inputHoles', params.PointerParam, pointerClass='SetOfHoles',
                      important=True, allowsNull=False,
                      label='Input holes from Smartscope',
                      help='Select a set of holes from Smartscope connection protocol.')
        form.addParam('inputMovies', params.PointerParam, pointerClass='SetOfMoviesSS',
                      important=True, allowsNull=False,
                      label='Input movies from Smartscope',
                      help='Select a set of movies from Smartscope connection protocol.')
        #sesion de Smartscope -> para cada hole pregunto de que sesion viene su grid
        form.addParam('totalClasses2D', params.PointerParam, allowsNull=False,
                       pointerClass='SetOfClasses2D',
                       label="Classes2D",
                       help='Set of Classes2D calculated by a classifier')
        form.addParam('goodClasses2D', params.PointerParam, allowsNull=False,
                       pointerClass='SetOfClasses2D',
                       label="Good Classes2D",
                       help='Set of good Classes2D calculated by a ranker')


        # form.addSection('Streaming')
        # form.addParam('refreshTime', params.IntParam, default=120,
        #               label="Time to refresh Smartscope synchronization (secs)")



    def _insertAllSteps(self):
        totalC = self.totalClasses2D.get()
        goodC = self.goodClasses2D.get()
        badC = []

        for t in totalC:
            flag = False
            for g in goodC:
                if t.getObjId() == g.getObjId():
                    flag = True
                    break
            if flag == False:
                badC.append(t)

        self.info('Total classe: {} Good Classe: {} Bad: {}\n'.format(
            len(totalC),len(goodC), len(badC)))
        self._insertFunctionStep('readClasses',goodC, badC,
                                 self.inputMovies.get(),  self.inputHoles.get())


    def readClasses(self, goodP, badP, movies, holes):
        '''Increase 1 to the hole.goodparticle (badParticle) based on the class ranker'''
        self.info('Reading inputs...')

        SOH = SetOfHoles.create(outputPath=self._getPath())
        self.outputsToDefine = {'SetOfHoles': SOH}
        self._defineOutputs(**self.outputsToDefine)

        self.info('Assigning good/bad particles to holes...')
        classesToiterate = {'goodParticles': goodP, 'badParticles': badP}
        dictHoles2Add = {}
        pCount = 0
        pAdded = 0

        for key, value in classesToiterate.items():
            self.info('\n\n{}'.format(key))
            for classItem in value:
                self.info('\t----->{}'.format(classItem))
                for p in classItem:
                    pCount += 1
                    for m in movies:
                        if (os.path.basename(m.getMicName()) == os.path.basename(p.getCoordinate().getMicName())):
                            for h in holes:
                                H_ID = h.getHoleId()
                                if m.getHoleId() == H_ID:
                                    keyList = [key2 for key2 in dictHoles2Add.keys()]
                                    pAdded += 1
                                    if key == 'goodParticles':
                                        if H_ID not in keyList:
                                            dictHoles2Add[H_ID] = [1, 0]
                                            self.debug('H_ID: {}  resolution: {}'.format(H_ID, p.getCTF().getResolution()))
                                            #self.debug('hole: {} \t- movie: {}'.format(H_ID, os.path.basename(m.getMicName())))
                                        else:
                                            dictHoles2Add[H_ID] = [dictHoles2Add[H_ID][0] + 1, dictHoles2Add[H_ID][1]]
                                        break
                                    elif key == 'badParticles':
                                        if H_ID not in keyList:
                                            dictHoles2Add[H_ID] = [0, 1]
                                            self.info('hole: {} \t- movie: {}'.format(H_ID, os.path.basename(m.getMicName())))
                                        else:
                                            dictHoles2Add[H_ID] = [dictHoles2Add[H_ID][0], dictHoles2Add[H_ID][1] + 1]
                                        break

        self.info('\n\nParticles to add: {}'.format(pCount))
        self.info('Particles added: {}'.format(pAdded))
        self.info('Holes to update: {}'.format(len(dictHoles2Add.items())))

        for key, value in dictHoles2Add.items():
            self.debug(key)
            self.debug(value)
            for h in holes:
                if h.getHoleId() == key:
                    h.setGoodParticles(int(h.getGoodParticles()) + value[0])
                    h.setBadParticles(int(h.getBadParticles()) + value[1])
                    break
            self.createOutputStep(SOH, h, holes)


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

    def createOutputStep(self, SOH, hole, holes):
        SOH.copyInfo(holes)
        hole2Add_copy = Hole()
        hole2Add_copy.copy(hole, copyId=False)
        SOH.append(hole2Add_copy)

        if self.hasAttribute('SetOfHoles'):
            SOH.write()
            outputAttr = getattr(self, 'SetOfHoles')
            outputAttr.copy(SOH, copyId=False)
            self._store(outputAttr)
        # STORE SQLITE
        self._store(SOH)

    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response

    def _summary(self):
        summary = []


        return summary


    def _validate(self):
        errors = []
        #self._validateThreads(errors)

        response = self.checkSmartscopeConnection()
        try:
            response[0]['username']
        except Exception as e:
            try:
                errors.append('Error Smartscope connection:\n{}'.format(response['detail']))
            except Exception:
                errors.append('Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(response))

        return errors