# **************************************************************************
# *
# * Authors: Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)
# *          Daniel Marchan (da.marchan@cnb.csic.es)
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
from pwem.objects import SetOfClasses2D
from . import smartscopeConnection

import pyworkflow.utils as pwutils
from smartscope import Plugin
from pyworkflow.object import Set
from ..objects.data import Hole

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *



class smartscopeFeedback2D(ProtImport, ProtStreamingBase):
    """
    This protocol will calculate which are the best holes of the session based
    on the good particles of each hole. After knowing the good holes, will
    sort the queue of hole acquisition that Smartscope uses.
    """
    _label = 'Feedback from particles'
    _devStatus = BETA
    _possibleOutputs = {'SetOfHolesRejected': SetOfHoles,
                        'SetOfHolesPassFilter': SetOfHoles,
                        'IntensityRange': Integer}
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
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputProtocol', params.PointerParam,
                      pointerClass='EMProtocol', label="Input Smartscope connection protocols", important=True,
                      help="Smartscope connection protocol")

        form.addParam('totalClasses2D', params.PointerParam, allowsNull=False,
                       pointerClass='SetOfClasses2D',
                       label="Classes2D",
                       help='Set of Classes2D calculated by a classifier')
        form.addParam('goodClasses2D', params.PointerParam, allowsNull=False,
                       pointerClass='SetOfClasses2D',
                       label="Good Classes2D",
                       help='Set of good Classes2D calculated by a ranker')
        form.addParam('percentBadPartcilesHole', params.EnumParam,
                      choices=self.percentBins, default=8, display=params.EnumParam.DISPLAY_COMBO,
                      label="Percent bad particles to consider bad Hole",
                      help="Percent of bad particles in a Hole to consider that the hole is a bad Hole or a Hole to reject. Default 80%")

        form.addSection('Streaming')
        form.addParam('refreshMethod', params.EnumParam, default=0,
                      choices=['Input micrographs', 'Time'],
                      display=params.EnumParam.DISPLAY_HLIST,
                      label='Select input to refresh the protocol',
                      help='Select the parameter which triger the refresh of the protocol.')
        form.addParam('refreshTime', params.IntParam, default=240,
                      condition='refreshMethod==1',
                      label="Time to refresh protocol",
                      help = "Time to refresh data collected (minimum 240 secs) and update the feedback if neccesary")
        form.addParam('refreshMics', params.IntParam, default=200,
                      condition='refreshMethod==0',
                      label = 'Input micrographs to refresh protocol',
                      help="Number of new micrographs to refresh data collected and update the feedback if neccesary")


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

        self.smartscopeConnectionProtocol = self.getInputProtocol()
        updatedProt = getUpdatedProtocol(self.smartscopeConnectionProtocol)
        if hasattr(updatedProt, 'Grids'):
            self.grids = updatedProt.Grids
        if hasattr(updatedProt, 'Holes'):
            self.holes = updatedProt.Holes
        if hasattr(updatedProt, 'MoviesSS'):
            self.movies = updatedProt.MoviesSS

        self.totalC = self.totalClasses2D.get()
        self.goodC = self.goodClasses2D.get()
        self.badC = []

        for t in self.totalC:
            flag = False
            for g in self.goodC:
                if t.getObjId() == g.getObjId():
                    flag = True
                    break
            if flag == False:
                self.badC.append(t)

    def getInputProtocol(self):
        prot = self.inputProtocol.get()
        prot.setProject(self.getProject())
        if isinstance(prot, smartscopeConnection):
            return prot
        else:
            return False

    def _insertAllSteps(self):
        self._insertFunctionStep(self._initialize, needsGPU=False)
        self._insertFunctionStep(self.readClasses, needsGPU=False)


    def readClasses(self):
        self.info('\nReading inputs...')
        self.info(f'Total classe: {len(self.totalC)} Good Classe: {len(self.goodC)}')
        SOH = SetOfHoles.create(outputPath=self._getPath())
        SOHR = SetOfHoles.create(outputPath=self._getPath())
        self.outputsToDefine = {'SetOfHolesPassFilter': SOH, 'SetOfHolesRejected': SOHR}
        self._defineOutputs(**self.outputsToDefine)

        dictHoles2Add = {}
        totalParticlesNum = sum(c.getSize() for c in self.totalC.iterItems())
        goodParticlesNum = sum(c.getSize() for c in self.goodC.iterItems())
        self.info(f'Total particles: {totalParticlesNum}\n'
                  f'Good particles: {goodParticlesNum}\n'
                  f'Bad particles: {totalParticlesNum - goodParticlesNum}')

        time0 = time.time()
        self.info('\nCollecting particles from good classes...')
        good_ids = set(p.getObjId() for p in self.goodC.iterClassItems())
        time1 = time.time()
        self.info(f'good classes particles Time: {round(time1 - time0, 0)} s')

        self.info('\nAssigning good/bad particles to holes...')
        #particles = list(self.totalC.iterClassItems())
        time2 = time.time()
        self.info(f'collecting all particles Time: {round(time2 - time1, 0)} s')
        #TODO Assigna mal los holes: {'LH11_3_square386_holXEZjZogOFw': [180366, 66024], 'LH11_3_square386_holAztiwnsCIa': [0, 77], 'LH11_3_square386_holzZfSm7jRF3': [0, 588], 'LH11_3_square386_holrUjBES1gSF': [50930, 19425], 'LH11_3_square386_hol929tIJ390T': [1396, 945], 'LH11_3_square386_holMTwXvE57NR': [0, 937], 'LH11_3_square407_hol3DEBuxJg8d': [0, 49], 'LH11_3_square386_hol7hjl1W6ZhS': [0, 367], 'LH11_3_square386_holpNyyHkWKC2': [0, 450], 'LH11_3_square386_holCdWRh4lEDt': [0, 1843], 'LH11_3_square386_hol9fBjbaa63T': [0, 198]}
        #TODO el bucle de abajo tarda como 1 hora...
        movie_cache = {}

        for p in self.totalC.iterClassItems(): #iterRows
            timeA = time.time()
            mic_name = p.getCoordinate().getMicName()
            if mic_name in movie_cache:
                movie = movie_cache[mic_name]
            else:
                movie = self.movies.getItem("_micName", mic_name)
                movie_cache[mic_name] = movie

            timeB = time.time()
            self.info(f'time getItem: {timeB - timeA}\n') #TODO to sloww. 0.01 sec each time
            H_ID = movie.getHoleId()
            #self.debug(f"micName: {p.getCoordinate().getMicName()} | H_ID: {H_ID}")
            obj_id = p.getObjId()
            is_good = obj_id in good_ids
            if H_ID not in dictHoles2Add:
                dictHoles2Add[H_ID] = [0, 0]
            if is_good:
                dictHoles2Add[H_ID][0] += 1
                #self.debug('H_ID: {}  resolution: {}'.format(H_ID, p.getCTF().getResolution()))
            else:
                dictHoles2Add[H_ID][1] += 1
                #self.debug('hole: {} \t- movie: {}'.format(H_ID, os.path.basename(movie.getMicName())))


        time3 = time.time()
        self.info(f'iter to assign holes to particles Time: {round(time3 - time2, 0)} s')
        for key, value in dictHoles2Add.items():
            self.debug(f'{key} {value}')
            hole = self.holes.getItem('_hole_id', key)
            hole.setGoodParticles(int(hole.getGoodParticles()) + value[0])
            hole.setBadParticles(int(hole.getBadParticles()) + value[1])
            hole.setTotalParticles(int(hole.getGoodParticles()) + value[0] + int(hole.getBadParticles()) + value[1])
            #self.createOutputStep(SOH, hole, self.holes) #TODO in time develope the statistics

        time4 = time.time()
        self.info(f'iter to create outputs Time: {round(time4 - time3, 0)} s')
        self.info(f'Total collecting time: {round(time4 - time0, 0)} s')


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

    def createOutputStep(self, SOH, hole, Setholes):
        SOH.copyInfo(Setholes)
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

        if Plugin.getVar(SMARTSCOPE_TOKEN) == 'Read Smartscope documentation to get the token...':
            errors.append('SMARTSCOPE_TOKEN has not been configured, '
                          'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
        if Plugin.getVar(SMARTSCOPE_LOCALHOST) == None:
            errors.append(
                'SMARTSCOPE_LOCALHOST has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
        if Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH) == 'Path assigned to the data in the Smartscope installation':
            errors.append(
                'SMARTSCOPE_DATA_SESSION_PATH has not been configured, '
                'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')

        response = self.checkSmartscopeConnection()
        try:
            response[0]['username']
        except Exception as e:
            try:
                errors.append('Error Smartscope connection:\n{}'.format(response['detail']))
            except Exception:
                errors.append('Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(response))

        return errors