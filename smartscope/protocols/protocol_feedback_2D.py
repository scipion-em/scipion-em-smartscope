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
from pwem.protocols import ProtBoxSizeCheckpoint
from pyworkflow.protocol import ProtStreamingBase, getUpdatedProtocol
from pwem.objects import SetOfClasses2D, SetOfAverages, Class2D, SetOfMicrographs
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

NUMBER_HOLES_TO_VIEW = 100


class smartscopeFeedback2D(ProtImport, ProtStreamingBase):
    """
    This protocol will calculate which are the best holes of the session based
    on the good particles of each hole. After knowing the good holes, will
    sort the queue of hole acquisition that Smartscope uses.
    """

    """
        smartscopeFeedback2D analyzes particle classification results obtained during
        cryo EM data collection in order to identify the most productive acquisition
        holes within a Smartscope session. The protocol evaluates the distribution of
        good and bad particles across holes and generates statistical feedback that
        can be used to optimize automated microscope acquisition strategies.

        The workflow starts from a Smartscope acquisition session together with a set
        of 2D classification results. Good particle classes can originate from either
        Relion or CryoAsses classification pipelines. The protocol compares all
        particles against the selected good classes and assigns every particle to its
        corresponding acquisition hole through the associated micrograph metadata.

        For each hole, the protocol calculates the number of good particles, bad
        particles, total particles, particle class distributions, and intensity based
        statistics. Holes are then grouped according to intensity ranges using
        histogram based binning methods, allowing the protocol to estimate which
        acquisition conditions produce the highest proportion of biologically useful
        particles.

        The resulting statistics provide an experimental feedback mechanism capable
        of identifying optimal acquisition regions during ongoing cryo EM sessions.
        This strategy is especially useful for large scale automated data collection
        workflows where acquisition efficiency directly affects microscope usage,
        particle quality, and downstream reconstruction performance.

        The protocol generates detailed statistical files describing particle
        distributions, hole quality metrics, class abundances, and intensity
        dependent behavior. It also creates ordered sets of all analyzed holes and
        the best ranked holes, facilitating rapid visualization and selection of
        high quality acquisition regions.

        From a biological and data acquisition perspective, this protocol helps
        prioritize microscope acquisition toward regions producing cleaner particle
        populations and better 2D classes, improving overall dataset quality while
        reducing the collection of low information micrographs during automated
        Smartscope sessions.
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
                      pointerClass='EMProtocol', label="Input Smartscope connection", important=True,
                      help="Smartscope connection protocol")

        form.addParam('totalClasses2D', params.PointerParam, allowsNull=False,
                       pointerClass='SetOfClasses2D',
                       label="Classes2D",
                       help='Set of Classes2D calculated by a classifier')
        form.addParam('goodClassesOrigin', params.EnumParam, default=0,
                      choices=['Relion', 'Cryoasses'],
                      display=params.EnumParam.DISPLAY_HLIST,
                      label='Select the protocol that generate the good2Dclasses ranked',
                      help='Relion generates setOf2DClasses and Cryoasses SetOfAverages, select the protocol the good classes come from.')
        form.addParam('goodClasses2DRelion', params.PointerParam,
                       condition='goodClassesOrigin==0',
                       pointerClass='SetOfClasses2D',
                       label="Good Classes2D from Relion",
                       help='Set of good Classes2D calculated by Relion ranker')
        form.addParam('goodClasses2DCryoasses', params.PointerParam,
                       condition='goodClassesOrigin==1',
                       pointerClass='SetOfAverages',
                       label="Good Classes2D from Cryoasses",
                       help='Set of good Classes2D calculated by Cryoasses ranker')
        form.addParam('percentGoodPartcilesHole', params.EnumParam,
                      choices=self.percentBins, default=5, display=params.EnumParam.DISPLAY_COMBO,
                      label="Percent good particles to consider good Hole",
                      help="Percent of good particles in a Hole to consider that the hole is a good Hole or a Hole to consider. Default 50%")
        # form.addParam('triggerMovies', params.IntParam, default=200,
        #               label="Movies to launch the protocol",
        #               help='Number of movies that pass the filters to launch the statistics')
        # form.addSection('Streaming')
        # form.addParam('refreshMethod', params.EnumParam, default=0,
        #               choices=['Input micrographs', 'Time'],
        #               display=params.EnumParam.DISPLAY_HLIST,
        #               label='Select input to refresh the protocol',
        #               help='Select the parameter which triger the refresh of the protocol.')
        # form.addParam('refreshTime', params.IntParam, default=240,
        #               condition='refreshMethod==1',
        #               label="Time to refresh protocol",
        #               help = "Time to refresh data collected (minimum 240 secs) and update the feedback if neccesary")
        # form.addParam('refreshMovies', params.IntParam, default=200,
        #               condition='refreshMethod==0',
        #               label = 'Input movies to refresh protocol',
        #               help="Number of new movies to refresh data collected and update the feedback if neccesary")

        form.addParam('micrographs', params.PointerParam,
                       pointerClass='SetOfMicrographs',
                       label="Microgaphs",
                       help='Micrographs')


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
        self.SOBestH = SetOfHoles.create(outputPath=self._getPath(),suffix='Best')
        self.outputsToDefine = {'SetOfHoles': self.SOH, 'SetOfBestHoles': self.SOBestH}
        self._defineOutputs(**self.outputsToDefine)
        self.smartscopeConnectionProtocol = self.getInputProtocol()
        updatedProt = getUpdatedProtocol(self.smartscopeConnectionProtocol)

        self.saveInExtraFile('urlSmartscope', open(os.path.join(updatedProt._getExtraPath(), 'URLsmartscopeSession.txt')).read())
        self.saveInExtraFile('sessionDetails',  open(os.path.join(updatedProt._getExtraPath(), 'summary.txt')).read())

        if hasattr(updatedProt, 'Grids'):
            self.grids = updatedProt.Grids
        if hasattr(updatedProt, 'Holes'):
            self.holes = updatedProt.Holes
        if hasattr(updatedProt, 'MoviesSS'):
            self.movies = updatedProt.MoviesSS

        self.totalC = self.totalClasses2D.get()
        if self.goodClassesOrigin.get() == 0:
            self.goodC = self.goodClasses2DRelion.get()
        else:
            self.goodC = SetOfClasses2D.create(outputPath=self._getPath(), prefix='_goodC')
            self.goodC.copyInfo(self.totalC)
            listGood = []
            for c in self.goodClasses2DCryoasses.get().iterItems():
                listGood.append(c.getIndex())
            enableFunc = lambda cls: cls.getObjId() in listGood
            self.goodC.appendFromClasses(self.totalC, filterClassFunc=enableFunc)

        self.badC = []
        self.dictHolesWithMic = {}
        self.dictHolesWithoutMic = {}

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


    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        self._initialize()
        self.readClasses()
        self.holesStatistis()
        self.smartscopeFeedback()
        self.createOutputStep()

    def readClasses(self):
        self.info('\nReading inputs...')
        self.info(f'Total classe: {len(self.totalC)} Good Classe: {len(self.goodC)}')
        self.holePixelSize = None
        self.moviePixelSize = None
        self.movieShapeX = None
        self.movieShapeY = None

        totalParticlesNum = sum(c.getSize() for c in self.totalC.iterItems())
        goodParticlesNum = sum(c.getSize() for c in self.goodC.iterItems())
        self.info(f'Total particles: {totalParticlesNum}\n'
                  f'Good particles: {goodParticlesNum}\n'
                  f'Bad particles: {totalParticlesNum - goodParticlesNum}')

        time0 = time.time()
        self.info('\nCollecting particles from good classes...')
        good_ids = set(p.getObjId() for p in self.goodC.iterClassItems())
        self.goodClasses = set(c.getObjId() for c in self.goodC.iterItems(orderBy='id', direction='ASC'))

        self.particlesCoords = {'Good': {}, 'Bad': {}}
        dictClassParticles = {}
        for c in self.goodC.iterItems(orderBy='id', direction='ASC'):
            dictClassParticles[c.getObjId()] = c

        time1 = time.time()
        self.info(f'Collect particles from good classes Time: {round(time1 - time0, 0)} s')
        self.info('Assigning good/bad particles to holes...')
        movie_cache = {}

        for hole in self.holes:
            H_ID = hole.getHoleId()
            intensity = hole.getSelectorValue()
            try:
                if self.movies.getItem("_hole_id", H_ID):
                    self.dictHolesWithMic[H_ID] = {'goodParticles': 0, 'badParticles': 0, 'intensity': intensity, 'sumLocalIntP': 0, 'meanLocalIntensity': None,  'meanMicIntensity': None, 'stdMicIntensity': None, 'ClassDistribution': {}}
            except UnboundLocalError:
                #self.dictHolesWithoutMic[H_ID]['intensity']
                self.dictHolesWithoutMic[H_ID] = {'goodParticles': 0, 'badParticles': 0, 'intensity': intensity, 'sumLocalIntP': 0, 'meanLocalIntensity': None, 'meanMicIntensity': None,'stdMicIntensity': None,  'ClassDistribution': {}}

            if not self.holePixelSize and hole.getPixelSize():
                self.holePixelSize = hole.getPixelSize()

        time2 = time.time()
        self.info(f'iter to collect all holes  Time: {round(time2 - time1, 0)} s')
        for p in self.totalC.iterClassItems(): #iterRows
            mic_name = p.getCoordinate().getMicName()

            if mic_name in movie_cache:
                movie = movie_cache[mic_name]
            else:
                movie = self.movies.getItem("_micName", mic_name)
                movie_cache[mic_name] = movie

            if not self.moviePixelSize and movie.getSamplingRate():
                self.moviePixelSize = movie.getSamplingRate()
            if not self.movieShapeX and movie.getShapeX():
                self.movieShapeX = movie.getShapeX()
                self.movieShapeY = movie.getShapeY()

            H_ID = movie.getHoleId()
            partClassID = p.getClassId()
            #self.debug(f"micName: {p.getCoordinate().getMicName()} | H_ID: {H_ID}")

            obj_id = p.getObjId()
            is_good = obj_id in good_ids
            if is_good:
                if not partClassID in self.particlesCoords['Good']:
                    self.particlesCoords['Good'][partClassID] = {}
                if not H_ID in self.particlesCoords['Good'][partClassID]:
                    self.particlesCoords['Good'][partClassID][H_ID] = []
                self.particlesCoords['Good'][partClassID][H_ID].append((self.coord_highMag2MedMag(hole, movie, p.getCoordinate().getX(), p.getCoordinate().getY())))

                self.dictHolesWithMic[H_ID]['goodParticles'] += 1
                if self.dictHolesWithMic[H_ID]['ClassDistribution'].get(partClassID):
                    self.dictHolesWithMic[H_ID]['ClassDistribution'][partClassID] += 1
                else:
                    self.dictHolesWithMic[H_ID]['ClassDistribution'][partClassID] = 1
            #self.debug('H_ID: {}  resolution: {}'.format(H_ID, p.getCTF().getResolution()))
            else:
                if not partClassID in self.particlesCoords['Bad']:
                    self.particlesCoords['Bad'][partClassID] = {}
                if not H_ID in self.particlesCoords['Bad'][partClassID]:
                    self.particlesCoords['Bad'][partClassID][H_ID] = []
                self.particlesCoords['Bad'][partClassID][H_ID].append((self.coord_highMag2MedMag(hole, movie, p.getCoordinate().getX(), p.getCoordinate().getY())))

                self.dictHolesWithMic[H_ID]['badParticles'] += 1
                #self.debug('hole: {} \t- movie: {}'.format(H_ID, os.path.basename(movie.getMicName())))

            # if  p.hasAttribute('_xmipp_localAverage'):
            #     self.dictHolesWithMic[H_ID]['sumLocalIntP'] += float(p.getAttributeValue('_xmipp_localAverage'))
            #     self.dictHolesWithMic[H_ID]['meanLocalIntensity'] = self.dictHolesWithMic[H_ID]['sumLocalIntP'] / (self.dictHolesWithMic[H_ID]['goodParticles'] + self.dictHolesWithMic[H_ID]['badParticles'])
            #
            # if not self.dictHolesWithMic[H_ID]['meanMicIntensity']:
            #     mean, std, min, max = mic.getImage().computeStats()
            #     self.dictHolesWithMic[H_ID]['meanMicIntensity'] = mean
            #     self.dictHolesWithMic[H_ID]['stdMicIntensity'] = std

        time3 = time.time()
        self.info(f'Assign good/bad particles to holes Time: {round(time3 - time2, 0)} s')
        for key, value in self.dictHolesWithMic.items():
            self.debug(f'{key} {value}')
            hole = self.holes.getItem('_hole_id', key)
            good =  int(value['goodParticles'])
            bad =  int(value['badParticles'])
            hole.setGoodParticles(good)
            hole.setBadParticles(good)
            hole.setTotalParticles(good + bad)

        time4 = time.time()
        self.info(f'iter to set holes particles Time: {round(time4 - time3, 0)} s')
        self.info(f'Total collecting time: {round(time4 - time0, 0)} s')

        summaryF = self._getExtraPath("summary.txt")
        summaryF = open(summaryF, "w")
        summaryF.write(f'Total classe: {len(self.totalC)} Good Classe: {len(self.goodC)}\n')
        summaryF.write(f'Total particles: {totalParticlesNum}\n' +
                       f'Good particles: {goodParticlesNum}\n' +
                       f'Bad particles: {totalParticlesNum - goodParticlesNum}')
        summaryF.close()

    def coord_highMag2MedMag(self, hole, movie, xp, yp):
        X_p_hm_mic = xp
        X_p_mm_mic = X_p_hm_mic * (self.moviePixelSize / self.holePixelSize)
        X_p_mm_hole =  X_p_mm_mic + movie.getX() - (self.movieShapeX / 2)
        X_p_mm_holeCroped = X_p_mm_hole - hole.getCropedXOrigin()

        Y_p_hm_mic = yp
        Y_p_mm_mic = Y_p_hm_mic * (self.moviePixelSize / self.holePixelSize)
        Y_p_mm_hole =  Y_p_mm_mic + movie.getY() - (self.movieShapeY / 2)
        Y_p_mm_holeCroped = Y_p_mm_hole - hole.getCropedYOrigin()

        return X_p_mm_holeCroped, Y_p_mm_holeCroped

    def sturgesBinsCalc(self, numElementes):
        import math
        return int(round(1 + math.log2(numElementes)))


    def saveStatistics(self, gridName):
        with open(os.path.join(self._getExtraPath(),'gridsName.txt'), 'w') as fi:
            for g in self.grids:
                fi.write(g.getName())
                fi.write('\n')
        with open(os.path.join(self._getExtraPath(),'gridsId.txt'), 'w') as fi:
            for g in self.grids:
                fi.write(g.getGridId())
                fi.write('\n')
        File = self._getExtraPath("{}-xBin.txt".format(gridName))
        np.savetxt(File, self.x_bin , fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-holeCount.txt".format(gridName))
        np.savetxt(File, self.y_count, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-holeTotalCount.txt".format(gridName))
        np.savetxt(File, self.y_countTotal, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-goodBin.txt".format(gridName))
        np.savetxt(File, self.good_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-good_binTotal.txt".format(gridName))
        np.savetxt(File, self.good_binTotal, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-badParticles.txt".format(gridName))
        np.savetxt(File, self.bad_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-totalParticles.txt".format(gridName))
        np.savetxt(File, self.totalParticles_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-stdTotalParticles.txt".format(gridName))
        np.savetxt(File, self.totalParticles_std_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-percentGood.txt".format(gridName))
        np.savetxt(File, self.percentGood_bin, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-bin_edges.txt".format(gridName))
        np.savetxt(File, self.bin_edges, fmt='%.8f', delimiter=' ')
        File = self._getExtraPath("{}-particlesPerHole_bin.txt".format(gridName))
        np.savetxt(File, self.particlesPerHole_bin, fmt='%.8f', delimiter=' ')

        for c in self.classes_bin_dict:
            File = self._getExtraPath("{}-classes-{}_bin.txt".format(gridName, c))
            np.savetxt(File, self.classes_bin_dict[c], fmt='%.8f', delimiter=' ')


    def holesStatistis(self):
        '''
        Determine good and bad holes and sort the holes for the acquisition
        :return:
        '''
        self.info('\n-Calculating statistics...')
        self.dictTotalHoles = self.dictHolesWithMic.copy()
        self.dictTotalHoles.update(self.dictHolesWithoutMic)
        for grid in self.grids:
            gridName = grid.getName()
            values = np.array(list(self.dictHolesWithMic.values()))
            goodParticles = np.array([d['goodParticles'] for d in values])
            badParticles = np.array([d['badParticles'] for d in values])
            totalParticles = badParticles + goodParticles

            classDist = np.array([d['ClassDistribution'] for d in values])
            classesDictParticles = {i: [0] * len(self.dictHolesWithMic) for i in self.goodClasses}
            for idx, Hole in enumerate(classDist):
                for cl, value in Hole.items():
                    classesDictParticles[cl][idx] = value

            for cl in classesDictParticles:
                classesDictParticles[cl] = np.array(classesDictParticles[cl])

            intensity = np.array([d['intensity'] for d in values])
            valuesTotal = np.array(list(self.dictTotalHoles.values()))#
            intensityTotal = np.array([d['intensity'] for d in valuesTotal])
            bins = self.sturgesBinsCalc(len(self.dictTotalHoles))
            self.classes_bin_dict = {i: np.zeros(bins) for i in self.goodClasses}
            self.bin_edges = np.linspace(intensityTotal.min(), intensityTotal.max(), bins + 1)
            self.y_count, _ = np.histogram(intensity, bins=self.bin_edges)
            self.y_countTotal, _ = np.histogram(intensityTotal, bins=self.bin_edges)
            self.totalParticles_bin = np.zeros(bins)
            self.totalParticles_std_bin = np.zeros(bins)
            self.good_bin = np.zeros(bins)
            self.good_binTotal = np.zeros(bins)
            self.good_std_bin = np.zeros(bins)
            self.bad_bin = np.zeros(bins)
            self.percentGood_bin = np.zeros(bins)
            self.particlesPerHole_bin = np.zeros(bins)



            for i in range(bins):
                mask = (intensity >= self.bin_edges[i]) & (intensity < self.bin_edges[i + 1])
                maskNoZero = mask != 0
                self.totalParticles_bin[i] = totalParticles[mask].sum()
                denominator = self.y_count[i].sum()
                if denominator and not np.isnan(denominator):
                    self.particlesPerHole_bin[i] = totalParticles[mask].sum() / denominator
                else:
                    self.particlesPerHole_bin[i] = 0
                self.good_binTotal[i] = goodParticles[mask].sum()
                valsGood = goodParticles[mask]
                if valsGood.size > 0:
                    self.good_bin[i] = valsGood.sum()
                    self.good_std_bin[i] = goodParticles[mask].std()
                else:
                    self.good_bin[i] = 0
                    self.good_std_bin[i] = 0
                valsBad = badParticles[mask]
                if valsBad.size > 0:
                    self.bad_bin[i] = valsBad.sum()
                else:
                    self.bad_bin[i] = 0

                if self.good_bin[i] != 0 or self.bad_bin[i] != 0:
                    self.percentGood_bin[i] = self.good_bin[i] / (self.good_bin[i] + self.bad_bin[i])

                for cl in self.classes_bin_dict:
                    self.classes_bin_dict[cl][i] = classesDictParticles[cl][mask].sum()

            self.x_bin = (self.bin_edges[:-1] + self.bin_edges[1:]) / 2

            self.saveStatistics(gridName)


    def smartscopeFeedback(self):
        '''
        connect to the Smartscope API and provide the sorted queue
        :return:
        '''
        pass

    def createOutputStep(self):
        time0 = time.time()
        self.SOH.copyInfo(self.holes)
        self.SOBestH.copyInfo(self.holes)
        for key, value in self.dictHolesWithMic.items():
            self.debug(key)
            self.debug(value)
            h = self.holes.getItem("_hole_id", key)
            good = int(value['goodParticles'])
            bad = int(value['badParticles'])
            total = good + bad
            h.setGoodParticles(good)
            h.setBadParticles(bad)
            h.setTotalParticles(total)
            # h.setMeanLocalIntensity(value['meanLocalIntensity'])
            # h.setMeanMicIntensity(value['meanMicIntensity'])
            # h.setStdMicIntensity(value['stdMicIntensity'])
            hole2Add_copy = Hole()
            hole2Add_copy.copy(h, copyId=False)
            self.SOH.append(hole2Add_copy)
            if self.hasAttribute('SetOfHoles'):
                self.SOH.write()
                outputAttr = getattr(self, 'SetOfHoles')
                outputAttr.copy(self.SOH, copyId=False)
        self._store(self.SOH)


        for hole in self.SOH.iterItems(orderBy='_goodParticles', direction='DESC', limit=NUMBER_HOLES_TO_VIEW):#
            hole2Add_copy = Hole()
            hole2Add_copy.copy(hole, copyId=False)
            self.SOBestH.append(hole2Add_copy)
            if self.hasAttribute('SetOfBestHoles'):
                self.SOBestH.write()
                outputAttr = getattr(self, 'SetOfBestHoles')
                outputAttr.copy(self.SOBestH, copyId=False)
        self._store(self.SOBestH)

        #self._store(self.SOH)
        time1 = time.time()
        self.info(f'Create output step Time: {round(time1 - time0, 0)} s')

    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response


    def saveInExtraFile(self, fileName, text):
        fileP = self._getExtraPath(f"{fileName}.txt")
        file = open(fileP, "w")
        file.write(text)

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