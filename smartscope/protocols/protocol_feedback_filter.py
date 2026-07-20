# **************************************************************************
# *
# * Authors: Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)
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
from pyworkflow.protocol import params, BooleanParam
from ..objects.dataCollection import *
from . import smartscopeConnection
from collections import defaultdict
import pyworkflow.protocol.constants as cons

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
    _label = 'Feedback from micrographs'
    _devStatus = BETA
    _possibleOutputs = {'SetOfHolesRejected': SetOfHoles,
                        'SetOfHolesPassFilter': SetOfHoles,
                        'IntensityRange': Integer}
    percentBins = ['0','10','20', '30', '40', '50', '60', '70', '80', '90']

    def __init__(self, **args):
        ProtImport.__init__(self, **args)
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
                      help='Number of micrographs that pass the filters to launch the statistics')
        form.addParam('emptyBinsPercent', params.EnumParam,
                      choices=self.percentBins, default=2, display=params.EnumParam.DISPLAY_COMBO,
                      #expertLevel=params.LEVEL_ADVANCED,
                      label="Percent empty bins in the histogram",
                      help="In the histogram of number of holes acquired (with movies), this parameter represent the"
                            " percent of empty bins allowed to feedback Smartscope (20% by default). Higher less restrictive")
        form.addParam('applyFeedback', params.BooleanParam, default=False, allowsNull=False,
                      label='Apply the calculated range of intensity back to Smartscope',
                      help='Set True if you want to apply the range of intensity (ice-thickness) back to Smartscope in real time')
        form.addParam('simulator', params.BooleanParam, default=False,
                      expertLevel=cons.LEVEL_ADVANCED,
                      label="Enable to simulate the screening",
                      help='If True the number of movies available will be the ones related to the micrographs. If False the number of movies will be the number reported by SmartscopeConnection')
        form.addParam('micsAll', params.PointerParam, pointerClass='SetOfMicrographs',
                      expertLevel=cons.LEVEL_ADVANCED, allowsNull=True,
                      label='Micrographs',
                      help='Select a set of micrographs from any protocol if you are simulating')

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
        self.intensityRangeSet = False
        self.initialNumMics = 0
        self.finish = False
        self.zeroTime = time.time()
        self.rTime = self.refreshTime.get()
        if self.rTime < 240:
            self.rTime = 240

        self.launchFirstIteration = False
        self.updateProtocolInputs()
        self.micsNoProcesed = 0

    def getInputProtocol(self):
        prot = self.inputProtocol.get()
        prot.setProject(self.getProject())
        if isinstance(prot, smartscopeConnection):
            return prot
        else:
            return False

    def updateProtocolInputs(self):
        updatedProt = getUpdatedProtocol(self.getInputProtocol())
        if hasattr(updatedProt, 'Grids'):
            self.grids = updatedProt.Grids
        if hasattr(updatedProt, 'Holes'):
            self.holes = updatedProt.Holes
        if hasattr(updatedProt, 'MoviesSS'):
            self.movies = updatedProt.MoviesSS
        if hasattr(updatedProt, 'Session'):
            self.sessionId = updatedProt.Session

    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        self.time0 = time.time()
        self._initialize()
        fMics = self.micsPassFilter.get()
        self.trigeredMics = self.triggerMicrograph.get()

        while True:
            lenFilteredNics= len(fMics.getFiles())
            #lenFilteredNics = fMics.getSize()
            self.info(f'fMics.isStreamOpen(): {self.micsPassFilter.get().isStreamOpen()}')
            if self.launchFirstIteration and not fMics.isStreamOpen():
                if self.micsNoProcesed > 0:
                    self.info(f'\nLaunching protocol with {lenFilteredNics} micrographs filtered...')
                    self.stepsToRun(fMics)
                self.info('Not more micrographs are expected; input setOfMicsPassFilter closed')
                break
            if not self.launchFirstIteration:
                if self.trigeredMics <= lenFilteredNics:
                    self.launchFirstIteration = True
                    self.initialNumMics = lenFilteredNics
                    self.info(f'\nLaunching protocol with {lenFilteredNics} micrographs filtered...')
                    self.stepsToRun(fMics)
                    continue
                else:
                    self.info(f'Waiting {self.trigeredMics} micrographs filtered to launch protocol. '
                              f'Micrographs Filtered: {lenFilteredNics}')
                    time.sleep(((self.trigeredMics - lenFilteredNics) * 1))  # 10 secs to process each mic
                    continue

            if self.conditionRefresh(lenFilteredNics):
                self.info(f'\nUpdating the protocol with {lenFilteredNics} micrographs filtered...')
                self.stepsToRun(fMics)


    def stepsToRun(self, fMics):
        self.updateProtocolInputs()
        self.timeMainSteps = time.time()
        self.collectHoles(fMics)
        self.timeCollect = time.time()
        self.assignGridHoles()
        self.timeAssign = time.time()
        self.statistics()
        self.timeStatistics = time.time()
        self.createOutputs()
        self.timeOutput = time.time()
        self.info(f'Collect Time: {round(self.timeCollect - self.timeMainSteps, 0)} s')
        self.info(f'Assign Time: {round(self.timeAssign - self.timeCollect, 0)} s')
        self.info(f'Statistics Time: {round(self.timeStatistics - self.timeAssign, 0)} s')
        self.info(f'Output Time: {round(self.timeOutput - self.timeStatistics, 0)} s')
        self.info(f'Total Time: {round(self.timeOutput - self.time0, 0)} s')

    def conditionRefresh(self, lenFilteredMics):
        if self.refreshMethod.get() == 0: #mics
            self.micsNoProcesed = lenFilteredMics - self.initialNumMics
            if self.micsNoProcesed  >= self.refreshMics.get():
                self.initialNumMics = lenFilteredMics
                return True
            else:
                self.info(f'Waiting new {self.refreshMics.get()} micrographs filtered to update protocol.'
                          f' New micrographs filtered: {self.micsNoProcesed }')
                time.sleep(((self.refreshMics.get() - (self.micsNoProcesed )) * 10)) #10 secs to process each mic
                return False
        else:
            rTime = time.time() - self.zeroTime
            if rTime >= self.rTime:
                self.zeroTime = time.time()
                return True
            else:
                self.info(f'Waiting {self.rTime}s to check new inputs')
                time.sleep(self.rTime)
                return False


    def collectHoles(self, fMics):
        self.info('\n-Collectiong holes...')
        self.dictMovies = {}
        self.dictHoles = {}
        self.dictHolesWithMic = {}
        self.dictPassHoles = {}
        self.dictRejectHoles = {}
        sessionshots = self.collectSessionShots()
        #Collect session holes (all grids)
        # for g in self.grids:
        #     gridId = g.getGridId()
        #     if g.getSessionId() == self.sessionId.get():
        for hole in self.holes:
        #    if hole.getGridId() == gridId:
                holeC = hole.clone()
                self.dictHoles[hole.getHoleId()] = {'Hole':  holeC, 'GridID': hole.getGridId(), 'Shots': sessionshots, 'Acquired': 0, 'Pass': 0, 'Rejected': 0, 'Intensity': holeC.getSelectorValue()}

        if self.simulator.get():
            for m in self.movies:
                for mic in self.micsAll.get():
                    try:
                        movie = self.movies.getItem("_micName", mic.getMicName())
                        self.dictMovies[m.getMicName()] = movie.clone()
                        if movie.getHoleId() not in self.dictHolesWithMic:
                            self.dictHolesWithMic[m.getHoleId()] = self.dictHoles[movie.getHoleId()]['Hole'].clone()
                        self.dictHoles[m.getHoleId()]['Acquired'] += 1
                    except Exception:
                        pass
        else:
            for m in self.movies:
                self.dictMovies[m.getMicName()] = m.clone()
                if m.getHoleId() not in self.dictHolesWithMic:
                    self.dictHolesWithMic[m.getHoleId()] = self.dictHoles[m.getHoleId()]['Hole'].clone()
                self.dictHoles[m.getHoleId()]['Acquired'] += 1

        for mic in fMics:
            H_ID = self.dictMovies[mic.getMicName()].getHoleId()
            self.dictHoles[H_ID]['Pass'] += 1
            self.dictHoles[H_ID]['Rejected'] = self.dictHoles[H_ID]['Acquired'] - self.dictHoles[H_ID]['Pass']
            if H_ID not in self.dictPassHoles:
                self.dictPassHoles[H_ID] = {'Hole': self.dictHoles[H_ID]['Hole'].clone()}

        self.dictRejectHoles = {key: value.clone() for key, value in self.dictHolesWithMic.items() if not key in self.dictPassHoles.keys()}


    def collectSessionShots(self):
        #Assign number of shots for the holes not acquired
        #We assume that all holes in the same session have the same shots per hole
        for hole in self.holes:
            shots = hole.getShots()
            if shots != 0:
                return shots

    def assignGridHoles(self):
        '''This function create list of holes based on the behaves of a grids'''
        self.info('\n-Assigning holes...')

        self.totalMicssByGrid = defaultdict(list) #TODO it does not consider the multishot, the hole does not know about how many shots it will have
        self.acquiredMicssByGrid = defaultdict(list)
        self.passMicsByGrid = defaultdict(list)
        self.rejectedMicssByGrid = defaultdict(list)

        for holeID, hole_data in self.dictHoles.items():
            h = hole_data['Hole']
            shots = hole_data['Shots']
            acqs = hole_data['Acquired']
            passF = hole_data['Pass']
            reject = hole_data['Rejected']
            intensity = hole_data['Intensity']
            if intensity == None or intensity == '':
                print(f'hole without intensity: {holeID}')
            grid_id = h.getGridId()

            for s in range(shots):
                self.totalMicssByGrid[grid_id].append(intensity)
            if acqs != 0:
                for a in range(acqs):
                    self.acquiredMicssByGrid[grid_id].append(intensity)
            if passF != 0:
                for a in range(passF):
                    self.passMicsByGrid[grid_id].append(intensity)
            if reject != 0:
                for a in range(reject):
                    self.rejectedMicssByGrid[grid_id].append(intensity)

        with open(os.path.join(self._getExtraPath(),'gridsName.txt'), 'w') as fi:
            for g in self.grids:
                fi.write(g.getName())
                fi.write('\n')

    # --------------------------- STATISTICS functions -----------------------------------
    def statistics(self):
        self.info('\n-Calculating statistics...')

        for grid in self.grids:
            self.listGridsStatistics[grid.getName()] = {}
            self.info('\n################\nGRID: {}\n################\n'.format(grid.getName()))
            gridId = grid.getGridId()
            self.dictArraysByGrid[gridId] = {'totalArrayMics':  np.array(self.totalMicssByGrid[gridId]),
                                             'acquiredMics': np.array(self.acquiredMicssByGrid[gridId]),
                                             'passArrayMics': np.array(self.passMicsByGrid[gridId])}
            minI = min(self.totalMicssByGrid[gridId])
            maxI = max(self.totalMicssByGrid[gridId])

            #BINS CALCULLATION
            nBins = self.sturgesBinsCalc(len(self.passMicsByGrid[gridId]))
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
                self.intensityRangeSet = True
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
            if not self.simulator.get() and self.applyFeedback.get():
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
                                                                        self.dictArraysByGrid[gridId][ 'acquiredMics'])
        empty_bins_total, empty_bin_ranges_total, percentEmptyBins_total = self.checkEmptyBins(minI, maxI, nBins,
                                                                            self.dictArraysByGrid[gridId]['totalArrayMics'])
        self.info('{} bins without holes'.format(len(empty_bins_total)))
        self.info('{} bins without acquired holes '.format(len(empty_bins_Mics)))
        matches = list(set(empty_bins_Mics) & set(empty_bins_total))
        if len(matches) != 0:
            empty_bins_Mics = [x for x in empty_bins_Mics if x not in matches]
            #empty_bins_total = [x for x in empty_bins_total if x not in matches]
            empty_bin_ranges_Mics = [empty_bin_ranges_Mics[i] for i in range(len(empty_bin_ranges_Mics)) if i not in matches]
            #empty_bin_ranges_total = [empty_bin_ranges_total[i] for i in range(len(empty_bin_ranges_total)) if i not in matches]
            percentEmptyBins_Mics = self.precentEmpty(len(empty_bins_Mics), nBins)
        return percentEmptyBins_Mics, empty_bin_ranges_Mics

    def normalDistribution(self, minI, maxI, nBins, gridId):
        '''
        Calculate the normal distribution of the % holes that pass the filters / holes with movies using the precalculate number of bins
        '''
        histHolesMics, rangeIntensity = np.histogram(self.dictArraysByGrid[gridId]['acquiredMics'], bins=nBins, range=(minI, maxI))
        histHolesPass, ranges = np.histogram(self.dictArraysByGrid[gridId]['passArrayMics'], bins=nBins, range=(minI, maxI))
        assert len(histHolesMics) == len(histHolesPass), "The histograms have no the same bins number"
        histRatio = np.divide(histHolesPass, histHolesMics, out=np.zeros_like(histHolesPass, dtype=float), where=histHolesMics != 0)
        histRatio[np.isinf(histRatio)] = 0.0
        histRatio[np.isnan(histRatio)] = 0.0
        mu = np.sum(ranges[:-1] * histRatio) / np.sum(histRatio)
        sigma = np.sqrt(np.sum(histRatio * (ranges[:-1] - mu) ** 2) / np.sum(histRatio))
        if sigma == 0:
            sigma = ranges[1] - ranges[0]
        return mu, sigma


    # --------------------------- VIEWER functions -----------------------------------
    def prepareViewer(self, gridId, gridName, nBins, minI, maxI):
        '''Creating files with arrays to let viewer plot it'''
        self.info('Preparing viewer ...')

        arrayHoles = np.array(self.totalMicssByGrid[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        rangeFile = self._getExtraPath("{}-rangeI.txt".format(gridName))
        np.savetxt(rangeFile, rangeIntensity[:-1].reshape(1, -1), fmt='%.8f', delimiter=' ')

        #Total hole histogram
        totalHistFile = self._getExtraPath("{}-totalHist.txt".format(gridName))
        np.savetxt(totalHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')

        #With mics hole histogram
        arrayHoles = np.array(self.acquiredMicssByGrid[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        withMicsHistFile = self._getExtraPath("{}-withMicsHist.txt".format(gridName))
        np.savetxt(withMicsHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')

        #Pass hole histogram
        arrayHoles = np.array(self.passMicsByGrid[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        passHistFile = self._getExtraPath("{}-passHist.txt".format(gridName))
        np.savetxt(passHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')

        #Rejected hole histogram
        arrayHoles = np.array(self.rejectedMicssByGrid[gridId])
        hist, rangeIntensity = np.histogram(arrayHoles, bins=nBins, range=(minI, maxI))
        rejectedHistFile = self._getExtraPath("{}-rejectedHist.txt".format(gridName))
        np.savetxt(rejectedHistFile, hist.reshape(1, -1), fmt='%.8f', delimiter=' ')


    # --------------------------- POSTING functions -----------------------------------
    def postingBack2Smartscope(self):
        for grid in self.grids:
            self.info('\n -Posting Back to Smartscope ...')
            gridID = grid.getGridId()
            status, currentRange = self.pyClient.getRangeOfIntensityGrid(gridID, magLevel='square', devel=True)
            currentMinRange, currentMaxRange  = currentRange['low_limit'],  currentRange['high_limit']
            if status:
                self.info('ranges before feedback: {} - {}'.format(currentMinRange, currentMaxRange))
            minI = self.listGridsStatistics[grid.getName()]['minIntensityL']
            maxI = self.listGridsStatistics[grid.getName()]['maxIntensityL']
            self.pyClient.postRangeIntensity(ID=gridID, data={"low_limit": minI, "high_limit": maxI})
            time.sleep(10) #wait until Smartscope manage the posting
            status, currentRange = self.pyClient.getRangeOfIntensityGrid(gridID, magLevel='square',devel=True)
            currentMinRange, currentMaxRange  = currentRange['low_limit'],  currentRange['high_limit']
            if status and currentMinRange == minI and currentMaxRange == maxI:
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
                summaryF.close()



    # --------------------------- CREATE OUTPUTS functions -----------------------------------
    def createOutputs(self):
        self.info('\n-Generating outputs ...')
        SOHR = SetOfHoles.create(outputPath=self._getPath(), prefix='Rejected')#baseName
        SOHPF = SetOfHoles.create(outputPath=self._getPath(), prefix='Pass')
        if self.intensityRangeSet:
            minI = list(self.listGridsStatistics.values())[0]['minIntensityL'] #TODO just provide the IntensityRange od the first grid
            maxI = list(self.listGridsStatistics.values())[0]['maxIntensityL']
            IntensityRange = f'{minI} - {maxI}'
            self.outputsToDefine = {'SetOfHolesPassFilter': SOHPF, 'SetOfHolesRejected': SOHR, 'IntensityRange': String(IntensityRange)}

        else:
            self.outputsToDefine = {'SetOfHolesPassFilter': SOHPF, 'SetOfHolesRejected': SOHR}

        self._defineOutputs(**self.outputsToDefine)


        if self.dictPassHoles:
            for h in self.dictPassHoles:
                self.createOutputStepPassFilter(SOHPF,self.dictPassHoles[h]['Hole'])
        if self.dictRejectHoles:
            for h in self.dictRejectHoles:
                self.createOutputStepRejected(SOHR,self.dictRejectHoles[h])


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
        dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)
        if dataPath == 'Path assigned to the data in the Smartscope installation':
            errors.append(
        	    'SMARTSCOPE_DATA_SESSION_PATH has not been configured, '
        	    'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
        if not os.path.isdir(dataPath):
            errors.append(
        	    f'SMARTSCOPE_DATA_SESSION_PATH: {dataPath} has wrong configuration, '
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