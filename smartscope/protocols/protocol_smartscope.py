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
This protocol connect with smartscope in streaming. Recive all information
from the API, collect it in Scipion objects and will be able to communicate
to Smartscope to take decission about the acquisition
"""
from pyworkflow.protocol import Protocol, params, Integer
from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from pwem.protocols.protocol_import.base import ProtImport
from pwem.protocols import EMProtocol
import pyworkflow.protocol.constants as cons
from pyworkflow.protocol import ProtStreamingBase
import pyworkflow.utils as pwutils

from ..objects.data import *
from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time

class smartscopeConnection(ProtImport, ProtStreamingBase):
    """
    This protocol will print hello world in the console
    IMPORTANT: Classes names should be unique, better prefix them
    """
    _label = 'smartscope connection'
    _devStatus = BETA
    _possibleOutputs = {'Squares': SetOfSquares,
                        'Atlas': SetOfAtlas,
                        'Grids': SetOfGrids,
                        'Holes': SetOfHoles,
                        'MoviesSS': SetOfMoviesSS}
    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL
        self.newSteps = []
        self.Squares = None
        self.Atlas = None
        self.Grids = None
        self.Holes = None
        self.MoviesSS = None
        self.stepsExecutionMode = STEPS_PARALLEL # Defining that the protocol contain parallel steps

    # -------------------------- DEFINE param functions ----------------------
    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)


        form.addParam('inputMovies', params.PointerParam, pointerClass='SetOfMovies',
                      important=True,
                      label=pwutils.Message.LABEL_INPUT_MOVS,
                      help='Select a set of previously imported movies.')

        form.addParam('dataPath', params.StringParam,
                      default='',
                      label='Smartscope data path', important=True,
                      help='Path assigned to the data in the Smartscope installation')

        #
        # form.addParam('SerialEMDataPath', params.StringParam,
        #               default='',
        #               label='SerialEM data path', important=True,
        #               help='Path to where Serialem will write files')

        form.addSection('Smartscope')
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

        form.addSection('Streaming')
        form.addParam('refreshTime', params.IntParam, default=120,
                      label="Time to refresh Smartscope data (secs)" )
        form.addParam('TotalTime', params.IntParam, default=86400,
                      label="Time to finish Smartscope (secs)",
                      help='Time from the begining ot the protocol to '
                           'the end of the acquisicion. By default 1 day (86400 secs)')

        form.addParallelSection(threads=3, mpi=1)


    # --------------------------- STEPS functions ------------------------------
    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        self._initialize()

        while True:
            delayInit = int(time.time() - self.startTime)
            self.info('TotalTime: {} delayInit: {}'.format(self.TotalTime,
                                                           delayInit))
            inputMovies = self.inputMovies.get()

            if self.TotalTime <= delayInit:  # End of the protocol
                break
            else:
                metadataCollection = self._insertFunctionStep(self.metadataCollection,
                                        prerequisites=[])
                screeningCollection = self._insertFunctionStep(self.screeningCollection,
                                          prerequisites=[metadataCollection])
                self._insertFunctionStep(self.importMoviesSS, inputMovies,
                                         prerequisites=[screeningCollection])

            if not inputMovies.isStreamOpen():
                self.info('Not more movies are expected; input setOfMovies closed')
                break

            time.sleep(self.refreshTime)


    def _initialize(self):
        #self.pyClient = MainPyClient(self.Authorization, self.endpoint)
        self.pyClient = MainPyClient(
            'Token 136737181feb270a1bc4120b19d5440b2f697c94',
            'http://localhost:48000/api/')
        self.connectionClient = dataCollection(self.pyClient)
        self.acquisition = Acquisition()
        self.microscopeList = [] #list of microscope Scipion object
        self.detectorList = [] #list of detector Scipion object
        self.sessionList = []#list of sessions Scipion object
        if self.Grids is None:
            self.SOG = SetOfGrids.create(outputPath=self._getPath())
        else:
            self.SOG = self.Grids
        if self.Atlas is None:
            self.SOA = SetOfAtlas.create(outputPath=self._getPath())
        else:
            self.SOA = self.Atlas
        if self.Squares is None:
            self.SOS = SetOfSquares.create(outputPath=self._getPath())
        else:
            self.SOA = self.Squares
        if self.Holes is None:
            self.SOH = SetOfHoles.create(outputPath=self._getPath())
        else:
            self.SOH = self.Holes

        self.startTime = time.time()
        self.reStartTime = time.time()
        self.ListMoviesImported = []

    #
    # def _insertAllSteps(self):
    #     # Insert processing steps
    #     self._insertFunctionStep(self._initialize)
    #     self._insertFunctionStep(self.metadataCollection)
    #     self.CloseStep_ID = self._insertFunctionStep('closeSet',
    #                                                  prerequisites=[],
    #                                                  wait=True)
    #     self.newSteps.append(self.CloseStep_ID)
    #
    # def closeSet(self):
    #     pass
    #
    # def _getFirstJoinStep(self):
    #     for s in self._steps:
    #         if s.funcName == self._getFirstJoinStepName():
    #             return s
    #     return None
    #
    # def _getFirstJoinStepName(self):
    #     # This function will be used for streaming, to check which is
    #     # the first function that need to wait for all micrographs
    #     # to have completed, this can be overwritten in subclasses
    #     # (eg in Xmipp 'sortPSDStep')
    #     return 'closeSet'
    #

    # def _stepsCheck(self):
    #     delayInit = int(time.time() - self.startTime)
    #     delay = int(time.time() - self.reStartTime)
    #
    #     if self.TotalTime <= delayInit: #End of the protocol
    #         output_step = self._getFirstJoinStep()
    #         if output_step and output_step.isWaiting():
    #             output_step.setStatus(cons.STATUS_NEW)
    #     else:
    #         new_step_id = self._insertFunctionStep('streamingScreaningAndImport',
    #                                     prerequisites=[], wait=False)
    #         self.newSteps.append(new_step_id)
    #         self.updateSteps()
    def metadataCollection(self):
        self.connectionClient.metadataCollection(self.microscopeList,
                                                 self.detectorList,
                                                 self.sessionList,
                                                 self.acquisition)

        MicroNames = ',  '.join([x.getName() for x in self.microscopeList])
        DetectorNames = ',  '.join([x.getName() for x in self.detectorList])
        SessionNames = ',  '.join([x.getSession() for x in self.sessionList])

        # SUMMARY INFO
        summaryF = self._getPath("summary.txt")
        summaryF = open(summaryF, "a")
        summaryF.write("Smartscope Screening\n\n" +
            "\t{} Microscopes: {}\n".format(len(self.microscopeList), MicroNames) +
            "\t{} Detectors: {}\n".format(len(self.detectorList), DetectorNames) +
            "\t{} Sessions: {}\n".format(len(self.sessionList), SessionNames))
        summaryF.close()

        # self.sessionId = '20230216pruebaguenaQHCyjsBSSMq'
        # self.sessionName = 'pruebaguena'
        self.sessionId = '2023060909-06-23_0qnYenlrA9mgn'
        self.sessionName = '09-06-23_0'

    def screeningCollection(self):
        self.outputsToDefine = {'Squares': self.SOS,
                                'Atlas': self.SOA,
                                'Grids': self.SOG,
                                'Holes': self.SOH}
        self._defineOutputs(**self.outputsToDefine)

        self.SOG.enableAppend()
        self.SOA.enableAppend()
        self.SOS.enableAppend()
        self.SOH.enableAppend()
        self._store(self.SOG)
        self._store(self.SOA)
        self._store(self.SOS)
        self._store(self.SOH)
        self.connectionClient.screeningCollection(self.dataPath,
                                                  self.sessionId,
                                                  self.sessionName,
                                                  self.SOG, self.SOA,
                                                  self.SOS, self.SOH)
        # STORE SQLITE
        self.SOG.write()
        self.SOA.write()
        self.SOS.write()
        self.SOH.write()
        self._store(self.SOG)
        self._store(self.SOA)
        self._store(self.SOS)
        self._store(self.SOH)
        # SUMMARY INFO
        summaryF2 = self._getPath("summary2.txt")
        summaryF2 = open(summaryF2, "w")
        summaryF2.write("\nSmartscope collecting\n\n" +
            "\t{}\tGrids \n".format(len(self.SOG)) +
            "\t{}\tAtlas \n".format(len(self.SOA)) +
            "\t{}\tSquares \n".format(len(self.SOS)) +
            "\t{}\tHoles \n".format(len(self.SOH)))
        summaryF2.close()


    def importMoviesSS(self, inputMovies):
        moviesToAdd = []
        moviesAPI = []

        # Match movies from the API and from the output of the protocol
        if self.MoviesSS == None:
            SOMSS = SetOfMoviesSS.create(outputPath=self._getPath())
            self.outputsToDefine = {'MoviesSS': SOMSS}
            self._defineOutputs(**self.outputsToDefine)
        else:
            SOMSS = self.MoviesSS

        for gr in self.Grids:
            self.info('GRID')
            dictMAPI = self.pyClient.getRouteFromID('highmag', 'grid', gr.getGridId())
            for m in dictMAPI:
                moviesAPI.append(m)
        if not SOMSS:
            moviesToAdd = moviesAPI
        else:
            for mAPI in moviesAPI:
                for mSS in SOMSS:
                    if not mAPI['frames'] in mSS.getFrames():
                        moviesToAdd.append(mAPI)

        #Match movies to add and movies from importMovies protocol
        self.info('\n\nmoviesAPI: {}\nmoviesToAdd: {}'.format(len(moviesAPI), len(moviesToAdd)))
        if moviesToAdd:
            if inputMovies is None:
                self.info('Set of movies from import movies protocol empty')
                return
            else:
                for mAPI in moviesToAdd:
                    for mImport in inputMovies:
                        if mAPI['frames'] == os.path.basename(mImport.getFileName()):
                            self.info('movie: {} will be added'.format(mAPI['frames']))
                            self.addMovieSS(SOMSS, mImport, mAPI)

            # SUMMARY INFO
            summaryF3 = self._getPath("summary3.txt")
            summaryF3 = open(summaryF3, "w")
            summaryF3.write("\nSmartscope importing movies\n\n" +
                            "\t{}\tMovies Smartscope\n\n".format(len(SOMSS)))
            summaryF3.close()
        else:
            self.info('All movies from the Smartscope Api were imported. '
                      'See the output of the protocol')


    def addMovieSS(self, SOMSS, movieImport, movieSS):
        SOMSS.setStreamState(SOMSS.STREAM_OPEN)
        SOMSS.enableAppend()
        self._store(SOMSS)

        movie2Add = MovieSS()
        movie2Add.copy(movieImport)

        movie2Add.setHmId(movieSS['hm_id'])
        movie2Add.setName(movieSS['name'])
        movie2Add.setNumber(movieSS['number'])
        movie2Add.setPixelSize(movieSS['pixel_size'])
        movie2Add.setShapeX(movieSS['shape_x'])
        movie2Add.setShapeY(movieSS['shape_y'])
        movie2Add.setSelected(movieSS['selected'])
        movie2Add.setStatus(movieSS['status'])
        movie2Add.setCompletionTime(movieSS['completion_time'])
        movie2Add.setIsX(movieSS['is_x'])
        movie2Add.setIsY(movieSS['is_y'])
        movie2Add.setOffset(movieSS['offset'])
        movie2Add.setFrames(movieSS['frames'])
        movie2Add.setDefocus(movieSS['defocus'])
        movie2Add.setAstig(movieSS['astig'])
        movie2Add.setAngast(movieSS['angast'])
        movie2Add.setCtffit(movieSS['ctffit'])
        movie2Add.setGridId(movieSS['grid_id'])
        movie2Add.setHoleId(movieSS['hole_id'])

        SOMSS.append(movie2Add)
        SOMSS.write()
        self._store(SOMSS)

        # STORE SQLITE
        SOMSS.setStreamState(SOMSS.STREAM_CLOSED)
        SOMSS.write()
        self._store(SOMSS)


    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []

        summaryF = self._getPath("summary.txt")
        summaryF2 = self._getPath("summary2.txt")
        summaryF3 = self._getPath("summary3.txt")

        if not os.path.exists(summaryF):
            summary.append("No summary file yet.")
        else:
            summaryF = open(summaryF, "r")
            for line in summaryF.readlines():
                summary.append(line.rstrip())
            summaryF.close()
        if os.path.exists(summaryF2):
            summaryF2 = open(summaryF2, "r")
            for line in summaryF2.readlines():
                summary.append(line.rstrip())
            summaryF2.close()
        if os.path.exists(summaryF3):
            summaryF3 = open(summaryF3, "r")
            for line in summaryF3.readlines():
                summary.append(line.rstrip())
            summaryF3.close()
        return summary


    def _validate(self):
        errors = []
        self._validateThreads(errors)

        return errors