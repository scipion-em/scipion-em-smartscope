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
from collections import defaultdict
import numpy as np



class smartscopeFeedback2D(ProtImport, ProtStreamingBase):
    """
    This protocol will calculate which are the best holes of the session based
    on the good particles of each hole. After knowing the good holes, will
    sort the queue of hole acquisition that Smartscope uses.
    """
    _label = 'Feedback from particles'
    _devStatus = BETA
    _possibleOutputs = {'SetOfHoles': SetOfHoles,
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
        form.addParam('percentGoodPartcilesHole', params.EnumParam,
                      choices=self.percentBins, default=5, display=params.EnumParam.DISPLAY_COMBO,
                      label="Percent good particles to consider good Hole",
                      help="Percent of good particles in a Hole to consider that the hole is a good Hole or a Hole to consider. Default 50%")

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
        self.SOH = SetOfHoles.create(outputPath=self._getPath())
        self.outputsToDefine = {'SetOfHoles': self.SOH}
        self._defineOutputs(**self.outputsToDefine)

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
        self.dictHoles2Add = {}

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
        self._insertFunctionStep(self.holesStatistis, needsGPU=False)
        self._insertFunctionStep(self.smartscopeFeedback, needsGPU=False)
        self._insertFunctionStep(self.createOutputStep, needsGPU=False)


    def readClasses(self):
        self.info('\nReading inputs...')
        self.info(f'Total classe: {len(self.totalC)} Good Classe: {len(self.goodC)}')

        totalParticlesNum = sum(c.getSize() for c in self.totalC.iterItems())
        goodParticlesNum = sum(c.getSize() for c in self.goodC.iterItems())
        self.info(f'Total particles: {totalParticlesNum}\n'
                  f'Good particles: {goodParticlesNum}\n'
                  f'Bad particles: {totalParticlesNum - goodParticlesNum}')

        time0 = time.time()
        self.info('\nCollecting particles from good classes...')
        good_ids = set(p.getObjId() for p in self.goodC.iterClassItems())
        time1 = time.time()
        self.info(f'Collect particles from good classes Time: {round(time1 - time0, 0)} s')
        self.info('Assigning good/bad particles to holes...')
        #particles = list(self.totalC.iterClassItems())
        movie_cache = {}

        for p in self.totalC.iterClassItems(): #iterRows
            mic_name = p.getCoordinate().getMicName()
            if mic_name in movie_cache:
                movie = movie_cache[mic_name]
            else:
                movie = self.movies.getItem("_micName", mic_name)
                movie_cache[mic_name] = movie
            H_ID = movie.getHoleId()
            #self.debug(f"micName: {p.getCoordinate().getMicName()} | H_ID: {H_ID}")
            obj_id = p.getObjId()
            is_good = obj_id in good_ids
            if H_ID not in self.dictHoles2Add:
                self.dictHoles2Add[H_ID] = [0, 0, self.holes.getItem("_hole_id", H_ID).getSelectorValue()]
            if is_good:
                self.dictHoles2Add[H_ID][0] += 1
                #self.debug('H_ID: {}  resolution: {}'.format(H_ID, p.getCTF().getResolution()))
            else:
                self.dictHoles2Add[H_ID][1] += 1
                #self.debug('hole: {} \t- movie: {}'.format(H_ID, os.path.basename(movie.getMicName())))


        time2 = time.time()
        self.info(f'Assign good/bad particles to holes Time: {round(time2 - time1, 0)} s')
        for key, value in self.dictHoles2Add.items():
            self.debug(f'{key} {value}')
            hole = self.holes.getItem('_hole_id', key)
            hole.setGoodParticles(int(hole.getGoodParticles()) + value[0])
            hole.setBadParticles(int(hole.getBadParticles()) + value[1])
            hole.setTotalParticles(int(hole.getGoodParticles()) + value[0] + int(hole.getBadParticles()) + value[1])

        time4 = time.time()
        self.info(f'iter to set holes particles Time: {round(time4 - time2, 0)} s')
        self.info(f'Total collecting time: {round(time4 - time0, 0)} s')

        summaryF = self._getExtraPath("summary.txt")
        summaryF = open(summaryF, "w")
        summaryF.write(f'Total classe: {len(self.totalC)} Good Classe: {len(self.goodC)}\n')
        summaryF.write(f'Total particles: {totalParticlesNum}\n' +
                       f'Good particles: {goodParticlesNum}\n' +
                       f'Bad particles: {totalParticlesNum - goodParticlesNum}')
        summaryF.close()

    def holesStatistis(self):
        '''
        Determine good and bad holes and sort the holes for the acquisition
        :return:
        '''
        self.info('\n-Calculating statistics...')

        for grid in self.grids:
            values = np.array(list(self.dictHoles2Add.values()))
            goodParticles = values[:, 0]
            badParticles = values[:, 1]
            percentGood = goodParticles / (goodParticles + badParticles)
            intensity = values[:, 2]
            bins = 5
            bin_edges = np.linspace(intensity.min(), intensity.max(), bins + 1)
            y_bin = np.zeros(bins)
            for i in range(bins):
                mask = (intensity >= bin_edges[i]) & (intensity < bin_edges[i + 1])
                maskNoZero = mask != 0
                y_bin[i] = goodParticles[maskNoZero].mean()
            x_bin = (bin_edges[:-1] + bin_edges[1:]) / 2

            import matplotlib.pyplot as plt

            plt.bar(x_bin, percentGood, width=(bin_edges[1] - bin_edges[0]) * 0.9)
            plt.xlabel('Intensity')
            plt.ylabel('Mean good particles')
            plt.show()

    def smartscopeFeedback(self):
        '''
        connect to the Smartscope API and provide the sorted queue
        :return:
        '''
        pass

    def createOutputStep(self):
        time0 = time.time()

        self.SOH.copyInfo(self.holes)

        for key, value in self.dictHoles2Add.items():
            self.debug(key)
            self.debug(value)
            h = self.holes.getItem("_hole_id", key)
            h.setGoodParticles(int(h.getGoodParticles()) + value[0])
            h.setBadParticles(int(h.getBadParticles()) + value[1])
            hole2Add_copy = Hole()
            hole2Add_copy.copy(h, copyId=False)
            self.SOH.append(hole2Add_copy)
            if self.hasAttribute('SetOfHoles'):
                self.SOH.write()
                outputAttr = getattr(self, 'SetOfHoles')
                outputAttr.copy(self.SOH, copyId=False)
                self._store(outputAttr)

        #self._store(self.SOH)
        time1 = time.time()
        self.info(f'Create output step Time: {round(time1 - time0, 0)} s')

    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response


    def _summary(self):
        summary = []
        summaryF = self._getExtraPath("summary.txt")
        if not os.path.exists(summaryF):
            summary.append("No summary file yet.")
        else:
            summaryF = open(summaryF, "r")
            for line in summaryF.readlines():
                summary.append(line.rstrip())
            summaryF.close()
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