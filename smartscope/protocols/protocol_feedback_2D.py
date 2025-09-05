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
        self.dictHolesNoAcquired = {}
        self.dictHolesAcquired = {}


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
        for h in self.holes:
            H_ID = h.getHoleId()
            if not self.dictHoles2Add.get(H_ID, False):
                intensity = h.getSelectorValue()
                if intensity != None:
                    self.dictHolesAcquired[H_ID] = [0, 0, intensity]
                else:
                    self.dictHolesNoAcquired[H_ID] = [0, 0, None]

        time5 = time.time()

        self.info(f'iter to collect all holes  Time: {round(time5 - time4, 0)} s')
        self.info(f'Total collecting time: {round(time5 - time0, 0)} s')

        summaryF = self._getExtraPath("summary.txt")
        summaryF = open(summaryF, "w")
        summaryF.write(f'Total classe: {len(self.totalC)} Good Classe: {len(self.goodC)}\n')
        summaryF.write(f'Total particles: {totalParticlesNum}\n' +
                       f'Good particles: {goodParticlesNum}\n' +
                       f'Bad particles: {totalParticlesNum - goodParticlesNum}')
        summaryF.close()

    def sturgesBinsCalc(self, numElementes):
        import math
        return int(round(1 + math.log2(numElementes)))


    def saveStatistics(self, gridName):
        File = self._getExtraPath("{}-holeCount.txt".format(gridName))
        np.savetxt(File, self.y_count, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-goodParticles.txt".format(gridName))
        np.savetxt(File, self.good_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-stdgoodParticles.txt".format(gridName))
        np.savetxt(File, self.good_std_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-badParticles.txt".format(gridName))
        np.savetxt(File, self.bad_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-totalParticles.txt".format(gridName))
        np.savetxt(File, self.totalParticles_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-stdTotalParticles.txt".format(gridName))
        np.savetxt(File, self.totalParticles_std_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-percentGood.txt".format(gridName))
        np.savetxt(File, self.percentGood_bin, fmt='%.8f', delimiter=' ')

    def plotsTemporal(self, x_bin, bin_edges):

        import matplotlib.pyplot as plt

        fig, axs = plt.subplots(2, 2, figsize=(10, 8))
        axs[0, 0].bar(x_bin, self.y_count, width=(bin_edges[1] - bin_edges[0]) * 0.9)
        axs[0, 0].set_title("Num holes")
        axs[0, 0].set_xlabel("Intensity")
        axs[0, 0].set_ylabel("Count")

        axs[0, 1].bar(x_bin, self.totalParticles_bin, width=(bin_edges[1] - bin_edges[0]) * 0.9,
                      yerr=self.totalParticles_std_bin, capsize=5, color='skyblue', edgecolor='black')
        axs[0, 1].set_title("Mean num particles")
        axs[0, 1].set_xlabel("Intensity")
        axs[0, 1].set_ylabel("particles")

        axs[1, 0].bar(x_bin, self.percentGood_bin, width=(bin_edges[1] - bin_edges[0]) * 0.9)
        axs[1, 0].set_title("Media de percent good")
        axs[1, 0].set_xlabel("Intensity")
        axs[1, 0].set_ylabel("Percent good")

        axs[1, 1].bar(x_bin, self.good_bin, width=(bin_edges[1] - bin_edges[0]) * 0.9,
                      yerr=self.good_std_bin, capsize=5, color='skyblue', edgecolor='black')
        axs[1, 1].set_title("Mean good Particles")
        axs[1, 1].set_xlabel("Intensity")
        axs[1, 1].set_ylabel("goodParticles")

        plt.tight_layout()
        plt.show()

    def holesStatistis(self):
        '''
        Determine good and bad holes and sort the holes for the acquisition
        :return:
        '''
        self.info('\n-Calculating statistics...')

        for grid in self.grids:
            gridName = grid.getName()
            values = np.array(list(self.dictHoles2Add.values()))
            totalParticles = values[:, 0] + values[:, 1]
            goodParticles = values[:, 0]
            badParticles = values[:, 1]
            intensity = values[:, 2]
            bins = self.sturgesBinsCalc(len(self.dictHoles2Add))
            bin_edges = np.linspace(intensity.min(), intensity.max(), bins + 1)
            self.y_count, _ = np.histogram(intensity, bins=bin_edges)#TODO consider the holes without movie and the holes with movie but without partiles
            self.totalParticles_bin = np.zeros(bins)
            self.totalParticles_std_bin = np.zeros(bins)
            self.good_bin = np.zeros(bins)
            self.good_std_bin = np.zeros(bins)
            self.bad_bin = np.zeros(bins)
            self.percentGood_bin = np.zeros(bins)

            for i in range(bins):
                mask = (intensity >= bin_edges[i]) & (intensity < bin_edges[i + 1])
                maskNoZero = mask != 0
                self.totalParticles_bin[i] = totalParticles[mask].mean()
                self.totalParticles_std_bin[i] = totalParticles[mask].std()
                self.good_bin[i] = goodParticles[mask].mean()
                self.good_std_bin[i] = goodParticles[mask].std()
                self.bad_bin[i] = badParticles[mask].mean()
                self.percentGood_bin[i] = self.good_bin[i] / (self.good_bin[i] + self.bad_bin[i])

            x_bin = (bin_edges[:-1] + bin_edges[1:]) / 2

            self.saveStatistics(gridName)
            self.plotsTemporal(x_bin, bin_edges)


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