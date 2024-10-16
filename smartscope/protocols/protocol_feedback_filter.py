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
from pyworkflow.protocol import ProtStreamingBase
import pyworkflow.utils as pwutils
from smartscope import Plugin
from pyworkflow.object import Set
from ..objects.data import Hole

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *
from scipy.stats import shapiro
import numpy as np

class smartscopeFeedbackFilter(ProtImport, ProtStreamingBase):
    """
    This protocol will calculate which are the best holes of the session based
    on the micrographs filtered by alignment, CTF estimations.... After knowing the good holes, will
    send the range of intensities of hole that Smartscope uses.
    """
    _label = 'Feedback filter'
    _devStatus = BETA
    _possibleOutputs = {'SetOfHolesRejected': SetOfHoles, 'SetOfHolesPassFilter': SetOfHoles}
    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL

        self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
        self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
        self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)

        self.pyClient = MainPyClient(self.token, self.endpoint)
        self.connectionClient = dataCollection(self.pyClient)
        self.countStreamingSteps = 0
        self.BIN_RANGE = [5, 101]

    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputGrids', params.PointerParam, pointerClass='SetOfGrids',
                      important=True, allowsNull=False,
                      label='Input grids from Smartscope',
                      help='Select a set of grids from Smartscope connection protocol.')
        form.addParam('inputHoles', params.PointerParam, pointerClass='SetOfHoles',
                      important=True, allowsNull=False,
                      label='Input holes from Smartscope',
                      help='Select a set of holes from Smartscope connection protocol.')
        form.addParam('inputMovies', params.PointerParam,
                      pointerClass='SetOfMoviesSS',
                      important=True, allowsNull=False,
                      label='Input movies from Smartscope',
                      help='Select a set of movies from Smartscope connection protocol.')
        # form.addParam('inputMicrographs', params.PointerParam, pointerClass='SetOfMicrographs',
        #               important=True, allowsNull=False,
        #               label='Input micrographs before filters',
        #               help='Select a set of holes from Smartscope connection protocol.')
        form.addParam('micsPassFilter', params.PointerParam, pointerClass='SetOfMicrographs',
                      important=True, allowsNull=False,
                      label='Filtered micrographs',
                      help='Select a set of micrographs filtered by any protocol.')
        form.addParam('triggerMicrograph', params.IntParam, default=200,
                      label="Micrographs to launch the protocol",
                      help='Number of micrographs filtered to launch the statistics')
        form.addParam('binsHist', params.IntParam, default=50,
                      expertLevel=params.LEVEL_ADVANCED,
                      label="Number of bins of the Intensity histogram",
                      help='')
        form.addSection('Streaming')

        form.addParam('refreshTime', params.IntParam, default=180,
                      label="Time to refresh data collected (secs) and update the feedback if neccesary")

        form.addParallelSection(threads=3, mpi=1)

    def _initialize(self):
        self.movies = self.inputMovies.get()
        self.holes = self.inputHoles.get()
        self.grids = self.inputGrids.get()
        self.zeroTime = time.time()
        self.finish = False

    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        self._initialize()

        while not self.finish:
            while True: #movies from other grid arrives

                rTime = time.time() - self.zeroTime
                if rTime >= self.refreshTime.get():
                    self.zeroTime = time.time()
                    self.info('len micsPassFilter: {}'.format(len(self.micsPassFilter.get())))
                    if len(self.micsPassFilter.get()) >= self.triggerMicrograph.get():
                        self.info('In progres...')
                        self.countStreamingSteps += 1

                        self.fMics = self.micsPassFilter.get()
                        self.collectSetOfHolesFiltered()
                        self.assignGridHoles()

                        self.statistics()
                        self.postingBack2Smartscope()
                        self.createSetOfFilteredHoles()
                        if not self.fMics.isStreamOpen():
                            self.info('Not more micrographs are expected, set closed')
                            self.finish = True
                    else:
                        self.info('Waiting enought micrographs to launch protocol.'
                                  ' triggerMicrograph: {}, micrographsFiltered: {}'.format(self.triggerMicrograph.get(), len(self.micsPassFilter.get())))

    def collectSetOfHolesFiltered(self):
        self.holespassFilter = []
        self.dictMovies = {}
        self.dictHoles = {}
        self.dictPassHoles = {}
        self.dictRejectHoles = {}
        for m in self.movies:
            self.dictMovies[m.getMicName()] = m.clone()
        for hole in self.holes:
            self.dictHoles[hole.getHoleId()] = hole.clone()
        for mic in self.fMics:
            H_ID = self.dictMovies[mic.getMicName()].getHoleId()
            self.dictPassHoles[H_ID] = self.dictHoles[H_ID]
        self.dictRejectHoles = {key: value.clone() for key, value in self.dictHoles.items() if key not in self.dictPassHoles}

    def assignGridHoles(self):
        '''This function create list of holes based on the behaves of a grids'''
        from collections import defaultdict
        self.totalHolesByGrid_value = defaultdict(list)
        self.passHolesByGrid_value = defaultdict(list)
        self.rejectedHolesByGrid_value = defaultdict(list)
        self.totalHolesByGrid = defaultdict(list)
        self.passHolesByGrid = defaultdict(list)
        self.rejectedHolesByGrid = defaultdict(list)
        for h in self.dictHoles.values():
            grid_id = h.getGridId()
            self.totalHolesByGrid_value[grid_id].append(h.getSelectorValue())
            self.totalHolesByGrid[grid_id].append(h.getHoleId())

        for h in self.dictPassHoles.values():
            grid_id = h.getGridId()
            self.passHolesByGrid_value[grid_id].append(h.getSelectorValue())
            self.passHolesByGrid[grid_id].append(h.getHoleId())

        for grid_id, holes in self.totalHolesByGrid.items():
            holesPass = self.passHolesByGrid.get(grid_id, [])
            self.rejectedHolesByGrid[grid_id] = [hole for hole in holes if hole not in holesPass]

        with open(os.path.join(self._getExtraPath(),'gridsName.txt'), 'w') as fi:
            for g in self.grids:
                fi.write(g.getName())
                fi.write('\n')

    def statistics(self):
        self.info('statistics')
        self.listGridsStatistics = {}

        for grid in self.grids:
            gridId = grid.getGridId()
            self.shapiroList = []
            arrayHoles = np.array(self.totalHolesByGrid_value[gridId])
            arrayFilteredHoles = np.array(self.passHolesByGrid_value[gridId])
            minI = min(self.totalHolesByGrid_value[gridId])
            maxI = max(self.totalHolesByGrid_value[gridId])

            listRange = range(self.BIN_RANGE[0], self.BIN_RANGE[1])
            for bin in listRange: #To check with prints the best bin value
                _, _, _, _ = self.calculate(bin, maxI, minI, arrayHoles, arrayFilteredHoles, grid.getName())
            self.info('\n/////////////\nGRID: {}'.format(grid))
            self.info('best bin to normal distribution: {}'.format(listRange[np.argmax(self.shapiroList)]))

            mu, sigma, minIntensityL, maxIntensityL = self.calculate(listRange[np.argmax(self.shapiroList)],
                                                            maxI, minI, arrayHoles, arrayFilteredHoles, grid.getName())
            self.listGridsStatistics[grid.getName()] = {'mu': mu, 'sigma': sigma, 'minIntensityL': minIntensityL,'maxIntensityL': maxIntensityL}

    def calculate(self, bin, maxI, minI, arrayHoles, arrayFilteredHoles, gridName):
        step = (maxI - minI) / bin
        bins = np.linspace(minI, maxI, bin)
        histTotal, rangeIntensity = np.histogram(arrayHoles, bins=bins)
        histFiltered, ranges = np.histogram(arrayFilteredHoles, bins=bins)
        assert len(histTotal) == len(histFiltered), "Los histogramas no tienen la misma cantidad de bins"
        histRatio = np.divide(histFiltered, histTotal, out=np.zeros_like(histFiltered, dtype=float), where=histTotal != 0)
        histRatio[np.isinf(histRatio)] = 0.0
        histRatio[np.isnan(histRatio)] = 0.0
        mu = np.sum(ranges[:-1] * histRatio) / np.sum(histRatio)
        sigma = np.sqrt(np.sum(histRatio * (ranges[:-1] - mu) ** 2) / np.sum(histRatio))
        minIntensityL = int(mu - sigma)
        maxIntensityL = int(mu + sigma + step)
        rangeFile = self._getExtraPath("{}-rangeI-{}.txt".format(gridName, self.countStreamingSteps))
        np.savetxt(rangeFile, rangeIntensity[:-1].reshape(1, -1), fmt='%.8f', delimiter=' ')
        histRatioFile = self._getExtraPath("{}-histRatio-{}.txt".format(gridName, self.countStreamingSteps))
        np.savetxt(histRatioFile, histRatio.reshape(1, -1), fmt='%.8f', delimiter=' ')
        shapiroTest = self.Shapiro_Wilk(histRatio)
        self.shapiroList.append(shapiroTest[1])
        return mu, sigma, minIntensityL, maxIntensityL

    def Shapiro_Wilk(self, histRatio):
        # Test de Shapiro-Wilk
        stat, p_value = shapiro(histRatio)
        print(f"Shapiro-Wilk test: W={stat:.4f}, p-value={p_value:.4f}")
        # Interpretation Shapiro-Wilk test
        alpha = 0.05
        if p_value > alpha:
            return True, p_value, "Pass the null hypothesis of Shapiro_Wilk (the data appears to be normally distributed)."
        else:
            return False, p_value, "Reject the null hypothesis of Shapiro_Wilk ({} < {}) (the data does not appear to be normally distributed).".format(
                p_value, alpha)

    def check_data_coverage(self):
        pass


    def postingBack2Smartscope(self):
        for grid in self.grids:
            minI = self.listGridsStatistics[grid.getName()]['minIntensityL']
            maxI = self.listGridsStatistics[grid.getName()]['maxIntensityL']
            self.pyClient.postParameterFromID(apiRoute='selector', route='', ID=grid.getGridId(), data={"low_limit": minI, "high_limit": maxI})

            # SUMMARY INFO
            summaryF = self._getExtraPath("summary.txt")
            summaryF = open(summaryF, "w")
            summaryF.write('\nGRID: {}\n'.format(grid.getName()))
            summaryF.write('Median value: {}\nStandard deviation: {}\nIntensity range with holes to acquire: {} - {}'.format(
                round(self.listGridsStatistics[grid.getName()]['mu'],1),
                round(self.listGridsStatistics[grid.getName()]['sigma'],1),
                self.listGridsStatistics[grid.getName()]['minIntensityL'],
                self.listGridsStatistics[grid.getName()]['maxIntensityL']))
            summaryF.close()

    def createSetOfFilteredHoles(self):
        SOHR = SetOfHoles.create(outputPath=self._getPath(), prefix='Rejected')#baseName
        SOHPF = SetOfHoles.create(outputPath=self._getPath(), prefix='Pass')
        self.outputsToDefine = {'SetOfHolesPassFilter': SOHPF, 'SetOfHolesRejected': SOHR}
        self._defineOutputs(**self.outputsToDefine)
        for grid in self.grids:
            holesRejected = self.rejectedHolesByGrid[grid.getGridId()]
            holesPAss = self.passHolesByGrid[grid.getGridId()]
            for h in holesRejected:
                self.createOutputStepRejected(SOHR, self.dictRejectHoles[h])
            for h in holesPAss:
                self.createOutputStepPassFilter(SOHPF, self.dictPassHoles[h])
			    
    def createOutputStepRejected(self, SOHR, hole):
        SOHR.copyInfo(self.holes)
        hole2Add_copy = Hole()
        hole2Add_copy.copy(hole, copyId=False)
        SOHR.append(hole2Add_copy)
        if self.hasAttribute('SetOfHolesRejected'):
            SOHR.write()
            outputAttr = getattr(self, 'SetOfHolesRejected')
            outputAttr.copy(SOHR, copyId=False)
            self._store(outputAttr)
        # STORE SQLITE
        self._store(SOHR)

    def createOutputStepPassFilter(self, SOHPF, hole):
        SOHPF.copyInfo(self.holes)
        hole2Add_copy = Hole()
        hole2Add_copy.copy(hole, copyId=False)
        SOHPF.append(hole2Add_copy)
        if self.hasAttribute('SetOfHolesPassFilter'):
            SOHPF.write()
            outputAttr = getattr(self, 'SetOfHolesPassFilter')
            outputAttr.copy(SOHPF, copyId=False)
            self._store(outputAttr)
        # STORE SQLITE
        self._store(SOHPF)
				    
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
        # self._validateThreads(errors)

        if Plugin.getVar(
        	    SMARTSCOPE_TOKEN) == 'Read Smartscope documentation to get the token...':
            errors.append('SMARTSCOPE_TOKEN has not been configured, '
                          'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
        if Plugin.getVar(SMARTSCOPE_LOCALHOST) == None:
            errors.append(
        	    'SMARTSCOPE_LOCALHOST has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
        if Plugin.getVar(
        	    SMARTSCOPE_DATA_SESSION_PATH) == 'Path assigned to the data in the Smartscope installation':
            errors.append(
        	    'SMARTSCOPE_DATA_SESSION_PATH has not been configured, '
        	    'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')

        response = self.checkSmartscopeConnection()
        try:
            response[0]['username']
        except Exception as e:
            try:
                errors.append('Error Smartscope connection:\n{}'.format(
        		    response['detail']))
            except Exception:
                errors.append(
        		    'Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(
        			    response))

        return errors