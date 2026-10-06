# **************************************************************************
# *
# * Authors: Alberto Garcia Mena   (alberto.garcia@cnb.csic.es)# *
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


class smartscopeFeedback(ProtImport, ProtStreamingBase):
    """
    This protocol will provide a weight distribution for the intensity ranges (ice tickness ranges)
    based on the processing pipeline. If only is provided the micrographs filtered, it will provide a weight distribution
    based on the percent of good holes (holes with micrographs whis pass the threshold - mainly resolution threshold)
    If the 2D class distribution and good class distribution is provided, it will provide a weight distribution based on
    the percent of good particles of each range of intensity and for each good class, will be inversely proportional to the
    population of each class. If both sets are provided the weight will be calculated taking in to acount both statistics.
    """
    _label = 'Feedback'
    _devStatus = BETA
    _possibleOutputs = {'SetOfHoles': SetOfHoles,
                        'SetOfHolesRejected': SetOfHoles,
                         'SetOfHolesPassFilter': SetOfHoles}
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
        # --------------------------- INPUT section ---------------------------
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('inputProtocol', params.PointerParam,
                      pointerClass='EMProtocol', label="Input Smartscope connection", important=True,
                      help="Smartscope connection protocol")

        form.addParam('MicrographsFilter', params.BooleanParam, default=True,
                      label="Enable microgrpahs feedback",
                      help='Allow to calculate feedback based on a set of micrographs that pass an specific threshold as resolution threshold')
        form.addParam('ParticlesFilter', params.BooleanParam, default=True,
                      label="Enable particle feedback",
                      help='Allow to calculate feedback based on a set of particles')
        form.addParam('Classes2DFilter', params.BooleanParam, default=True,
                      label="Enable 2DClasses feedback",
                      help='Allow to calculate feedback based on a set of 2DClasses')


        form.addParam('micrographs', params.PointerParam,
                       pointerClass='SetOfMicrographs',
                       label="Microgaphs",
                       help='Micrographs')

        # --------------------------- Filter feedback section -----------------
        form.addParam('micsPassFilter', params.PointerParam, pointerClass='SetOfMicrographs',
                      important=True, allowsNull=False,
                      condition='MicrographsFilter',
                      label='Filtered micrographs',
                      help='Select a set of micrographs filtered by any protocol.')
        form.addParam('triggerMicrograph', params.IntParam, default=200,
                      condition='MicrographsFilter',
                      label="Micrographs to launch the protocol",
                      help='Number of micrographs that pass the filters to launch the statistics')
        form.addParam('emptyBinsPercent', params.EnumParam,
                      choices=self.percentBins, default=2, display=params.EnumParam.DISPLAY_COMBO,
                      condition='MicrographsFilter',
                      label="Percent empty bins in the histogram",
                      help="In the histogram of number of holes acquired (with movies), this parameter represent the"
                            " percent of empty bins allowed to feedback Smartscope (20% by default). Higher less restrictive")
        form.addParam('simulator', params.BooleanParam, default=False,
                      expertLevel=params.LEVEL_ADVANCED,
                      condition='MicrographsFilter',
                      label="Enable to simulate the screening",
                      help='If True the number of movies available will be the ones related to the micrographs. If False the number of movies will be the number reported by SmartscopeConnection')
        form.addParam('micsAll', params.PointerParam, pointerClass='SetOfMicrographs',
                      condition='MicrographsFilter',
                      expertLevel=params.LEVEL_ADVANCED, allowsNull=True,
                      label='Micrographs Simulated',
                      help='Select a set of micrographs from any protocol if you are simulating')

        # ---------------------------Particles feedback section ---------------------
        form.addParam('inputParticles', params.PointerParam,
                      condition='ParticlesFilter',
                      label="Input particles",
                      important=True, pointerClass='SetOfParticles',
                      help='Select the input particles (images)')

        # --------------------------- 2D feedback section ---------------------
        form.addParam('totalClasses2D', params.PointerParam, allowsNull=False,
                      condition='Classes2DFilter',
                      pointerClass='SetOfClasses2D',
                      important=True,
                      label="Classes2D",
                      help='Set of Classes2D calculated by a classifier')
        form.addParam('goodClassesOrigin', params.EnumParam, default=0,
                      condition='Classes2DFilter',
                      choices=['Relion', 'Cryoasses'],
                      display=params.EnumParam.DISPLAY_HLIST,
                      label='Select the protocol that generate the good2Dclasses ranked',
                      help='Relion generates setOf2DClasses and Cryoasses SetOfAverages, select the protocol the good classes come from.')
        form.addParam('goodClasses2DRelion', params.PointerParam,
                       condition='goodClassesOrigin==0 and Classes2DFilter',
                       pointerClass='SetOfClasses2D',
                       label="Good Classes2D from Relion",
                       help='Set of good Classes2D calculated by Relion ranker')
        form.addParam('goodClasses2DCryoasses', params.PointerParam,
                       condition='goodClassesOrigin==1 and Classes2DFilter',
                       pointerClass='SetOfAverages',
                       label="Good Classes2D from Cryoasses",
                       help='Set of good Classes2D calculated by Cryoasses ranker')
        form.addParam('percentGoodPartcilesHole', params.EnumParam,
                      condition='Classes2DFilter',
                      choices=self.percentBins, default=5, display=params.EnumParam.DISPLAY_COMBO,
                      label="Percent good particles to consider good Hole",
                      help="Percent of good particles in a Hole to consider that the hole is a good Hole or a Hole to consider. Default 50%")

        # --------------------------- Streaming section -----------------------
        form.addSection('Streaming')
        form.addParam('refreshTime', params.IntParam, default=240,
                      label="Time to refresh protocol",
                      help="Time to refresh data collected (minimum 240 secs) and update the feedback if neccesary")

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



    def _initialize(self):
        # Streaming state (from feedback filter)
        self.intensityRangeSet = False
        self.initialNumMics = 0
        self.finish = False
        self.zeroTime = time.time()
        self.rTime = self.refreshTime.get()
        if self.rTime < 240:
            self.rTime = 240
        self.launchFirstIteration = False
        self.micsNoProcesed = 0

        # Load Smartscope outputs and session info
        self.updateProtocolInputs()
        updatedProt = getUpdatedProtocol(self.getInputProtocol())
        self.saveInExtraFile('urlSmartscope', open(os.path.join(updatedProt._getExtraPath(), 'URLsmartscopeSession.txt')).read())
        self.saveInExtraFile('sessionDetails', open(os.path.join(updatedProt._getExtraPath(), 'summary.txt')).read())

        # Output sets (from feedback 2D)
        self.SOH = SetOfHoles.create(outputPath=self._getPath())
        self.SOBestH = SetOfHoles.create(outputPath=self._getPath(), suffix='Best')
        self.outputsToDefine = {'SetOfHoles': self.SOH, 'SetOfBestHoles': self.SOBestH}
        self._defineOutputs(**self.outputsToDefine)

        # protocol parameters steps
        self.info(f'MicrographsFilter: {self.MicrographsFilter.get()}\n'
                  f'ParticlesFilter: {self.ParticlesFilter.get()}\n'
                  f' Classes2DFilter: {self.Classes2DFilter.get()}\n')


        if self.Classes2DFilter.get():
            # 2D classes setup (from feedback 2D) — only if 2D inputs are provided
            if self.totalClasses2D.get() is not None:
                self.totalC = self.totalClasses2D.get()
                if self.goodClassesOrigin.get() == 0:
                    self.goodC = self.goodClasses2DRelion.get()
                else:
                    self.goodC = SetOfClasses2D.create(outputPath=self._getPath(), prefix='_goodC')
                    self.goodC.copyInfo(self.totalC)
                    listGood = [c.getIndex() for c in self.goodClasses2DCryoasses.get().iterItems()]
                    enableFunc = lambda cls: cls.getObjId() in listGood
                    self.goodC.appendFromClasses(self.totalC, filterClassFunc=enableFunc)

                self.badC = []
                for t in self.totalC:
                    flag = any(t.getObjId() == g.getObjId() for g in self.goodC)
                    if not flag:
                        self.badC.append(t)



    def saveInExtraFile(self, fileName, text):
        fileP = self._getExtraPath(f"{fileName}.txt")
        with open(fileP, "w") as f:
            f.write(text)



    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        self.time0 = time.time()
        self._initialize()
        self.collectHoles()



    def collectHoles(self):
        sessionshots = self.collectSessionShots()
        self.dictHoles = {}

        # HOLE COLLECTION----------
        for hole in self.holes:
            H_ID = hole.getHoleId()
            holeC = hole.clone()
            intensity = hole.getSelectorValue()
            try:
                if self.movies.getItem("_hole_id", H_ID):
                    self.dictHoles[H_ID] = {'Hole': holeC, 'GridID': hole.getGridId(), 'Shots': sessionshots, 'Acquired': 0, 'Pass': 0, 'Rejected': 0, 'particles': 0, 'goodParticles': 0, 'badParticles': 0, 'intensity': intensity, 'ClassDistribution': {}}
            except UnboundLocalError:
                self.dictHoles[H_ID] = {'Hole': holeC, 'GridID': hole.getGridId(), 'Shots': sessionshots, 'Acquired': 0, 'Pass': 0, 'Rejected': 0, 'particles': 0, 'goodParticles': 0, 'badParticles': 0, 'intensity': intensity, 'ClassDistribution': {}}

            if not self.holePixelSize and hole.getPixelSize():
                self.holePixelSize = hole.getPixelSize()

        for m in self.movies:
            self.dictHoles[m.getHoleId()]['Acquired'] += 1

        # MICROGRAPHS COLLECTION----------
        if self.MicrographsFilter.get():
            fMics = self.micsPassFilter.get()
            for mic in fMics:
                H_ID = self.dictMovies[mic.getMicName()].getHoleId()
                self.dictHoles[H_ID]['Pass'] += 1
                self.dictHoles[H_ID]['Rejected'] = self.dictHoles[H_ID]['Acquired'] - self.dictHoles[H_ID]['Pass']

            for key, value in self.dictHoles.items():
                #self.debug(f'{key} {value}')
                hole = self.holes.getItem('_hole_id', key)
                totalParts = int(value['particles'])
                hole.setTotalParticles(totalParts)

            print(self.dictHoles)


        # 2DCLASSES COLLECTION----------
        if self.Classes2DFilter.get():
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

            movie_cache = {}
            self.info('\nCollecting particles from good classes...')
            good_ids = set(p.getObjId() for p in self.goodC.iterClassItems())
            self.goodClasses = set(c.getObjId() for c in self.goodC.iterItems(orderBy='id', direction='ASC'))
            self.particlesCoords = {'Good': {}, 'Bad': {}}
            dictClassParticles = {}

            for c in self.goodC.iterItems(orderBy='id', direction='ASC'):
                dictClassParticles[c.getObjId()] = c
            for p in self.totalC.iterClassItems():  # iterRows
                mic_name = p.getCoordinate().getMicName()
                if mic_name in movie_cache:
                    movie = movie_cache[mic_name]
                else:
                    movie = self.movies.getItem("_micName", mic_name)
                    movie_cache[mic_name] = movie
                if not self.moviePixelSize and movie.getSamplingRate():
                    self.moviePixelSize = movie.getSamplingRate()
                if not self.movieShapeX and movie.getDimensions():
                    self.movieShapeX = movie.getDimensions()[0]
                    self.movieShapeY = movie.getDimensions()[1]

                H_ID = movie.getHoleId()
                partClassID = p.getClassId()
                # self.debug(f"micName: {p.getCoordinate().getMicName()} | H_ID: {H_ID}")

                if p.getObjId() in good_ids:
                    self.dictHoles[H_ID]['goodParticles'] += 1
                    self.dictHoles[H_ID]['particles'] += 1

                    if self.dictHoles[H_ID]['ClassDistribution'].get(partClassID):
                        self.dictHoles[H_ID]['ClassDistribution'][partClassID] += 1
                    else:
                        self.dictHoles[H_ID]['ClassDistribution'][partClassID] = 1
                # self.debug('H_ID: {}  resolution: {}'.format(H_ID, p.getCTF().getResolution()))
                else:
                    self.dictHoles[H_ID]['badParticles'] += 1
                    self.dictHoles[H_ID]['particles'] += 1
                    # self.debug('hole: {} \t- movie: {}'.format(H_ID, os.path.basename(movie.getMicName())))

            for key, value in self.dictHoles.items():
                #self.debug(f'{key} {value}')
                hole = self.holes.getItem('_hole_id', key)
                good = int(value['goodParticles'])
                bad = int(value['badParticles'])
                hole.setGoodParticles(good)
                hole.setBadParticles(good)
                hole.setTotalParticles(good + bad)

            print(self.dictHoles)


        # PARTICLES COLLECTION----------
        elif self.ParticlesFilter.get():
            movie_cache = {}
            for p in self.inputParticles.get():
                mic_name = p.getCoordinate().getMicName()
                if mic_name in movie_cache:
                    movie = movie_cache[mic_name]
                else:
                    movie = self.movies.getItem("_micName", mic_name)
                    movie_cache[mic_name] = movie
                H_ID = movie.getHoleId()
                self.dictHoles[H_ID]['particles'] += 1
            print(self.dictHoles)




    # --------------------------- VALIDATION functions -----------------------------------
    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response

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


