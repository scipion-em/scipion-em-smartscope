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
from smartscope import Plugin
from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
from . import smartscopeConnection

#external imports
import time
from ..constants import *
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
    percentBins = ['0','10','20', '30', '40', '50']
    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL

        self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
        self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
        self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)

        self.pyClient = MainPyClient(self.token, self.endpoint)
        self.connectionClient = dataCollection(self.pyClient)
        self.BIN_RANGE = [5, 101]
        self.dictArraysByGrid = {}
        self.listGridsStatistics = {}

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
        form.addParam('micsPassFilter', params.PointerParam, pointerClass='SetOfMicrographs',
                      important=True, allowsNull=False,
                      label='Filtered micrographs',
                      help='Select a set of micrographs filtered by any protocol.')
        form.addParam('triggerMicrograph', params.IntParam, default=200,
                      label="Micrographs to launch the protocol",
                      help='Number of micrographs filtered to launch the statistics')
        form.addParam('emptyBinsPercent', params.EnumParam,
                      choices=self.percentBins, default=1, display=params.EnumParam.DISPLAY_COMBO,
                      #expertLevel=params.LEVEL_ADVANCED,
                      label="Percent empty bins in the histogram",
                      help="In the histogram of number of holes acquired (with movies), this parameter represent the"
                            " percent of empty bins allowed to feedback Smartscope (10% by default). Higher less restrictive")
        form.addSection('Streaming')

        form.addParam('refreshTime', params.IntParam, default=240,
                      label="Time to refresh data collected (secs) and update the feedback if neccesary")

        form.addParallelSection(threads=3, mpi=1)

    def _initialize(self):
        self.rTime = self.refreshTime.get()
        if self.rTime < 180:
            self.rTime = 180
        self.zeroTime = time.time()
        self.finish = False
        self.smartscopeConnectionProtocol = self.getInputProtocol()
        updatedProt = getUpdatedProtocol(self.smartscopeConnectionProtocol)
        if hasattr(updatedProt, 'Grids'):
            self.grids = updatedProt.Grids
        if hasattr(updatedProt, 'Holes'):
            self.holes = updatedProt.Holes
        if hasattr(updatedProt, 'MoveiesSS'):
            self.movies = updatedProt.MoveiesSS

    def getInputProtocol(self):
        prot = self.inputProtocol.get()
        prot.setProject(self.getProject())
        if isinstance(prot, smartscopeConnection):
            return prot
        else:
            return False

    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        self._initialize()

        while not self.finish:
            rTime = time.time() - self.zeroTime
            if rTime >= self.rTime:
                self.zeroTime = time.time()
                if len(self.micsPassFilter.get()) >= self.triggerMicrograph.get():
                    self.fMics = self.micsPassFilter.get()
                    self.collectHoles()
                    self.assignGridHoles()
                    self.statistics()
                    self.createOutputs()
                    if not self.fMics.isStreamOpen():
                        self.info('Not more micrographs are expected, set closed')
                        self.finish = True
                else:
                    self.info('Waiting enought micrographs to launch protocol.'
                              ' triggerMicrograph: {}, micrographsFiltered: {}'.format(self.triggerMicrograph.get(), len(self.micsPassFilter.get())))

    def collectHoles(self):
        self.holespassFilter = []
        self.dictMovies = {}
        self.dictHoles = {}
        self.dictHolesWithMic = {}
        self.dictPassHoles = {}
        self.dictRejectHoles = {}

        for hole in self.holes:
            self.dictHoles[hole.getHoleId()] = hole.clone()
        for m in self.movies:
            self.dictMovies[m.getMicName()] = m.clone()
            self.dictHolesWithMic[m.getHoleId()] = self.dictHoles[m.getHoleId()].clone()
        for mic in self.fMics:
            H_ID = self.dictMovies[mic.getMicName()].getHoleId()
            self.dictPassHoles[H_ID] = self.dictHoles[H_ID].clone()
        self.dictRejectHoles = {key: value.clone() for key, value in self.dictHolesWithMic.items() if key not in self.dictPassHoles}

    def assignGridHoles(self):
        '''This function create list of holes based on the behaves of a grids'''
        from collections import defaultdict
        self.totalHolesByGrid_value = defaultdict(list)
        self.withMicsHolesByGrid_value = defaultdict(list)
        self.passHolesByGrid_value = defaultdict(list)
        self.rejectedHolesByGrid_value = defaultdict(list)
        self.totalHolesByGrid = defaultdict(list)
        self.withMicsHolesByGrid = defaultdict(list)
        self.passHolesByGrid = defaultdict(list)
        self.rejectedHolesByGrid = defaultdict(list)
        for h in self.dictHoles.values():
            grid_id = h.getGridId()
            self.totalHolesByGrid_value[grid_id].append(h.getSelectorValue())
            self.totalHolesByGrid[grid_id].append(h.getHoleId())
        for h in self.dictHolesWithMic.values():
            grid_id = h.getGridId()
            self.withMicsHolesByGrid_value[grid_id].append(h.getSelectorValue())
            self.withMicsHolesByGrid[grid_id].append(h.getHoleId())

        for h in self.dictPassHoles.values():
            grid_id = h.getGridId()
            self.passHolesByGrid_value[grid_id].append(h.getSelectorValue())
            self.passHolesByGrid[grid_id].append(h.getHoleId())

        for grid_id, holes in self.withMicsHolesByGrid.items():
            holesPass = self.passHolesByGrid[grid_id]
            self.rejectedHolesByGrid_value[grid_id] = [self.dictRejectHoles[hole].getSelectorValue() for hole in holes if hole not in holesPass]
            self.rejectedHolesByGrid[grid_id] = [hole for hole in holes if hole not in holesPass]

        with open(os.path.join(self._getExtraPath(),'gridsName.txt'), 'w') as fi:
            for g in self.grids:
                fi.write(g.getName())
                fi.write('\n')

    # --------------------------- STATISTICS functions -----------------------------------
    def statistics(self):
        for grid in self.grids:
            self.listGridsStatistics[grid.getName()] = {}
            self.info('\n################\nGRID: {}\n################\n'.format(grid.getName()))
            gridId = grid.getGridId()
            self.dictArraysByGrid[gridId] = {'totalArrayHoles':  np.array(self.totalHolesByGrid_value[gridId]),
                                             'withMicsArrayHoles': np.array(self.withMicsHolesByGrid_value[gridId]),
                                             'passArrayHoles': np.array(self.passHolesByGrid_value[gridId])}
            minI = min(self.totalHolesByGrid_value[gridId])
            maxI = max(self.totalHolesByGrid_value[gridId])

            #BINS CALCULLATION
            nBins = self.sturgesBinsCalc(len(self.passHolesByGrid_value[gridId]))
            print('Number of bins estimated: {}'.format(nBins))

            #REPRESENTATIVENESS
            percentEmptyBins_Mics, empty_bin_ranges_Mics = self.representativeness(minI, maxI, nBins, gridId)
            if percentEmptyBins_Mics > int(self.percentBins[self.emptyBinsPercent.get()]):
                self.info('{}% of bins empty > {}% allowed. We need more holes acquired in this ranges of intensity'
                          ' to calculate the best ranges of intensities to acquire and feedback Smartscope\n'
                          'Ranges of empty bins: {}'.format(round(percentEmptyBins_Mics, 1), self.percentBins[self.emptyBinsPercent.get()], empty_bin_ranges_Mics))
                continue
            #NORMAL DISTRIBUTION
            else:
                self.info('{}% of bins empty <= {}% configured.\nRanges of empty bins: {}'.format(
                    round(percentEmptyBins_Mics, 1),  self.percentBins[self.emptyBinsPercent.get()], empty_bin_ranges_Mics))
                mu, sigma = self.normalDistribution(minI, maxI, nBins, gridId)
                rangeIntensityMin = round((mu - sigma),1)
                rangeIntensityMax = round((mu + sigma), 1)
                self.info('Best range of intensity to collect movies: {} - {}'.format(rangeIntensityMin, rangeIntensityMax))
                self.listGridsStatistics[grid.getName()]['minIntensityL'] = rangeIntensityMin
                self.listGridsStatistics[grid.getName()]['maxIntensityL'] = rangeIntensityMax
                self.listGridsStatistics[grid.getName()]['mu'] = mu
                self.listGridsStatistics[grid.getName()]['sigma'] = sigma

            #Posting Smartscope
            self.postingBack2Smartscope()
            #Prepare viewer
            self.prepareViewer(gridId, grid.getName(), nBins, minI, maxI)

    def checkEmptyBins(self, minI, maxI, nBins, array):
        bins = np.linspace(minI, maxI, nBins)
        histTotal, rangeIntensity = np.histogram(array, bins=bins)
        histTotal[np.isinf(histTotal)] = 0.0
        histTotal[np.isnan(histTotal)] = 0.0
        empty_bins = np.where(histTotal == 0)[0]  # Índices de los bins vacíos
        empty_bin_ranges = [(round(bins[i], 1), round(bins[i + 1], 1)) for i in empty_bins]  # Rango de cada bin vacío
        percentEmptyBins = self.precentEmpty(empty_bins, nBins)
        return empty_bins, empty_bin_ranges, percentEmptyBins

    def precentEmpty(self, empty_bins, nBins):
        return (len(empty_bins) * 100) / nBins

    def sturgesBinsCalc(self, numElementes):
        import math
        return int(round(1 + math.log2(numElementes)))

    def representativeness(self, minI, maxI, nBins, gridId ):
        empty_bins_Mics, empty_bin_ranges_Mics, percentEmptyBins_Mics = self.checkEmptyBins(minI, maxI, nBins,
                                                                        self.dictArraysByGrid[gridId][ 'withMicsArrayHoles'])
        empty_bins_total, empty_bin_ranges_total, percentEmptyBins_total = self.checkEmptyBins(minI, maxI, nBins,
                                                                            self.dictArraysByGrid[gridId]['totalArrayHoles'])
        self.info('{} bins without holes'.format(len(empty_bins_total)))
        self.info('{} bins without acquired holes '.format(len(empty_bins_Mics)))
        matches = list(set(empty_bins_Mics) & set(empty_bins_total))
        if len(matches) != 0:
            empty_bins_Mics = [x for x in empty_bins_Mics if x not in matches]
            empty_bins_total = [x for x in empty_bins_total if x not in matches]
            empty_bin_ranges_Mics = [empty_bin_ranges_Mics[i] for i in range(len(empty_bin_ranges_Mics)) if i not in matches]
            empty_bin_ranges_total = [empty_bin_ranges_total[i] for i in range(len(empty_bin_ranges_total)) if i not in matches]
            percentEmptyBins_Mics = self.precentEmpty(len(empty_bins_Mics), nBins)
        return percentEmptyBins_Mics, empty_bin_ranges_Mics

    def normalDistribution(self, minI, maxI, nBins, gridId):
        '''
        Calculate the normal distribution of the % holes that pass the filters / holes with movies using the precalculate number of bins
        '''
        histHolesMics, rangeIntensity = np.histogram(self.dictArraysByGrid[gridId]['withMicsArrayHoles'], bins=nBins, range=(minI, maxI))
        histHolesPass, ranges = np.histogram(self.dictArraysByGrid[gridId]['passArrayHoles'], bins=nBins, range=(minI, maxI))
        assert len(histHolesMics) == len(histHolesPass), "Los histogramas no tienen la misma cantidad de bins"
        histRatio = np.divide(histHolesPass, histHolesMics, out=np.zeros_like(histHolesPass, dtype=float), where=histHolesMics != 0)
        histRatio[np.isinf(histRatio)] = 0.0
        histRatio[np.isnan(histRatio)] = 0.0
        mu = np.sum(ranges[:-1] * histRatio) / np.sum(histRatio)
        sigma = np.sqrt(np.sum(histRatio * (ranges[:-1] - mu) ** 2) / np.sum(histRatio))
        return mu, sigma

    # --------------------------- VIEWER functions -----------------------------------

    def prepareViewer(self, gridId, gridName, nBins, minI, maxI):
        '''Creating files with arrays to let viewer plot it'''

        arrayHoles = np.array(self.totalHolesByGrid_value[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        rangeFile = self._getExtraPath("{}-rangeI.txt".format(gridName))
        np.savetxt(rangeFile, rangeIntensity[:-1].reshape(1, -1), fmt='%.8f', delimiter=' ')

        #Total hole histogram
        totalHistFile = self._getExtraPath("{}-totalHist.txt".format(gridName))
        np.savetxt(totalHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')

        #With mics hole histogram
        arrayHoles = np.array(self.withMicsHolesByGrid_value[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        withMicsHistFile = self._getExtraPath("{}-withMicsHist.txt".format(gridName))
        np.savetxt(withMicsHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')

        #Pass hole histogram
        arrayHoles = np.array(self.passHolesByGrid_value[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        passHistFile = self._getExtraPath("{}-passHist.txt".format(gridName))
        np.savetxt(passHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')

        #Rejected hole histogram
        arrayHoles = np.array(self.rejectedHolesByGrid_value[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        rejectedHistFile = self._getExtraPath("{}-rejectedHist.txt".format(gridName))
        np.savetxt(rejectedHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')

    # --------------------------- POSTING functions -----------------------------------
    def postingBack2Smartscope(self):
        for grid in self.grids:

            gridID = grid.getGridId()
            currentMinRange, currentMaxRange = self.pyClient.getRangeOfIntensityGrid(gridID)
            self.info('ranges before feedback: {} - {}'.format(currentMinRange, currentMaxRange))
            minI = self.listGridsStatistics[grid.getName()]['minIntensityL']
            maxI = self.listGridsStatistics[grid.getName()]['maxIntensityL']
            self.pyClient.postRangeIntensity(route='', ID=gridID, data={"low_limit": minI, "high_limit": maxI})
            time.sleep(10) #wait until Smartscope manage the posting
            currentMinRange, currentMaxRange = self.pyClient.getRangeOfIntensityGrid(gridID)
            if currentMinRange == minI and currentMaxRange == maxI:
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
            else:
                self.error('could not configure the range of intensities in Smartscope')
                summaryF = self._getExtraPath("summary.txt")
                summaryF = open(summaryF, "w")
                summaryF.write('\nGRID: {}\n'.format(grid.getName()))
                summaryF.write('Could not configure in Smartscope the range of intensities calculated {}-{} '.format(
                                     self.listGridsStatistics[grid.getName()]['minIntensityL'],
                                            self.listGridsStatistics[grid.getName()]['maxIntensityL']))

    # --------------------------- CREATE OUTPUTS functions -----------------------------------
    def createOutputs(self):
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


    # --------------------------- VALIDATION functions -----------------------------------
    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response




    # --------------------------- INFO functions -----------------------------------
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

        if self.getInputProtocol() == False:
            errors.append('Protocol imnported is not the SmartscopeConnection one')
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