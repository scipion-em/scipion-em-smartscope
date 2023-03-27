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
import pyworkflow.protocol.constants as cons
from ..objects.data import *
from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time

class smartscopeConnection(ProtImport, Protocol):
    """
    This protocol will print hello world in the console
    IMPORTANT: Classes names should be unique, better prefix them
    """
    _label = 'smartscope connection'
    _devStatus = BETA
    def __init__(self, **args):
        ProtImport.__init__(self, **args)
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

        form.addParam('dataPath', params.StringParam,
                      default='',
                      label='Smartscope data path', important=True,
                      help='Path assigned to the data in the Smartscope installation')

        form.addSection('Streaming')
        form.addParam('refreshTime', params.IntParam, default=60,
                      label="Time to refresh Smartscope data (secs)" )
        form.addParam('TotalTime', params.IntParam, default=86400,
                      label="Time to finish Smartscope (secs)",
                      help='Time from the begining ot the protocol to '
                           'the end of the acquisicion. By default 1 day (86400 secs)')


    # --------------------------- STEPS functions ------------------------------
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
        self.setOfGrids = SetOfGrids.create(outputPath=self._getPath())
        self.setOfAtlas = SetOfAtlas.create(outputPath=self._getPath())
        self.setOfSquares = SetOfSquares.create(outputPath=self._getPath())
        self.setOfHoles = SetOfHoles.create(outputPath=self._getPath())
        self.startTime = time.time()
        self.reStartTime = time.time()


    def _insertAllSteps(self):
        # Insert processing steps
        self._insertFunctionStep(self._initialize)
        self._insertFunctionStep(self.metadataCollection)
        self.CloseStep_ID = self._insertFunctionStep('closeSet',
                                                     prerequisites=[],
                                                     wait=True)
        self.newSteps.append(self.CloseStep_ID)

    def closeSet(self):
        pass

    def _getFirstJoinStep(self):
        for s in self._steps:
            if s.funcName == self._getFirstJoinStepName():
                return s
        return None

    def _getFirstJoinStepName(self):
        # This function will be used for streaming, to check which is
        # the first function that need to wait for all micrographs
        # to have completed, this can be overwritten in subclasses
        # (eg in Xmipp 'sortPSDStep')
        return 'closeSet'


    def _stepsCheck(self):
        delayInit = int(time.time() - self.startTime)
        delay = int(time.time() - self.reStartTime)

        if self.TotalTime <= delayInit: #End of the protocol
            output_step = self._getFirstJoinStep()
            if output_step and output_step.isWaiting():
                output_step.setStatus(cons.STATUS_NEW)
        else:
            new_step_id = self._insertFunctionStep('streamingScreaningAndImport',
                                        prerequisites=[], wait=False)
            self.newSteps.append(new_step_id)
            self.updateSteps()



    def metadataCollection(self):
        self.connectionClient.metadataCollection(self.microscopeList,
                                                 self.detectorList,
                                                 self.sessionList,
                                                 self.acquisition)

        MicroNames = [x.getName() for x in self.microscopeList]
        DetectorNames = [x.getName() for x in self.detectorList]
        SessionNames = [x.getSession() for x in self.sessionList]

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
        self.sessionId = '20230327streamingMoviestrIiUAG'
        self.sessionName = 'streamingMovies'

    def streamingScreaningAndImport(self):
        delayInit = int(time.time() - self.startTime)
        while self.TotalTime > delayInit:
            delayInit = int(time.time() - self.startTime)
            delay = int(time.time() - self.reStartTime)
            if self.refreshTime <= delay:
                self.screeningCollection()
                self.reStartTime = time.time()
                print('\n----Lets import----\n')

                self.importMoviesSS()

    def screeningCollection(self):
        SOG = SetOfGrids.create(outputPath=self._getPath())
        SOA = SetOfAtlas.create(outputPath=self._getPath())
        SOS = SetOfSquares.create(outputPath=self._getPath())
        SOH = SetOfHoles.create(outputPath=self._getPath())
        self.outputsToDefine = {'Squares': SOS,
                                'Atlas': SOA,
                                'Grids': SOG,
                                'Holes': SOH}
        self._defineOutputs(**self.outputsToDefine)

        SOG.enableAppend()
        SOA.enableAppend()
        SOS.enableAppend()
        SOH.enableAppend()
        self._store(SOG)
        self._store(SOA)
        self._store(SOS)
        self._store(SOH)
        self.connectionClient.screeningCollection(self.dataPath,
                                                  self.sessionId,
                                                  self.sessionName,
                                                  SOG, SOA, SOS, SOH)
        # STORE SQLITE
        SOG.write()
        SOA.write()
        SOS.write()
        SOH.write()
        self._store(SOG)
        self._store(SOA)
        self._store(SOS)
        self._store(SOH)
        # SUMMARY INFO
        summaryF2 = self._getPath("summary2.txt")
        summaryF2 = open(summaryF2, "w")
        summaryF2.write("\nSmartscope collecting\n\n" +
            "\t{}\tGrids \n".format(len(SOG)) +
            "\t{}\tAtlas \n".format(len(SOA)) +
            "\t{}\tSquares \n".format(len(SOS)) +
            "\t{}\tHoles \n".format(len(SOH)))
        summaryF2.close()


    def importMoviesSS(self):
        if self.MoviesSS == None:
            SOMSS = SetOfMoviesSS.create(outputPath=self._getPath())
            self.outputsToDefine = {'MoviesSS': SOMSS}
            self._defineOutputs(**self.outputsToDefine)
        else:
            SOMSS = self.MoviesSS
        SOMSS.setStreamState(SOMSS.STREAM_OPEN)
        SOMSS.enableAppend()
        self._store(SOMSS)

        pathMoviesRaw = '/home/agarcia/Documents/Facility_work/smartscope_Data/smartscope_testfiles/movies'
        allHM = self.pyClient.getDetailsFromParameter('highmag')#TODO para todas las sesiones! ACOTAR A LA SESION
        print('\n----HOLA----\n')
        print('len(allHM) {} != len(self.MoviesSS) {}'.format(
            len(allHM), len(self.MoviesSS)))
        if len(allHM) != len(self.MoviesSS):
            for hm in allHM:
                mSS = MovieSS()
                mSS.setHmId(hm['hm_id'])
                mSS.setName(hm['name'])
                mSS.setNumber(hm['number'])
                mSS.setPixelSize(hm['pixel_size'])
                mSS.setShapeX(hm['shape_x'])
                mSS.setShapeY(hm['shape_y'])
                mSS.setSelected(hm['selected'])
                mSS.setStatus(hm['status'])
                mSS.setCompletionTime(hm['completion_time'])
                mSS.setIsX(hm['is_x'])
                mSS.setIsY(hm['is_y'])
                mSS.setOffset(hm['offset'])
                # mSS.setFrames(hm['frames'])
                mSS.setDefocus(hm['defocus'])
                mSS.setAstig(hm['astig'])
                mSS.setAngast(hm['angast'])
                mSS.setCtffit(hm['ctffit'])
                mSS.setGridId(hm['grid_id'])
                mSS.setHoleId(hm['hole_id'])
                # mSS.setFrames(self.getFramesNumber(gr, mSS.getName()))
                # fileName = self.getSubFramePath(gr, mSS.getName())
                # st = time.time()
                # if not os.path.isfile(str(fileName)):#parche para visualizar movies fake
                # print(mSS.getName())
                fileName = os.path.join(pathMoviesRaw,
                                        str(mSS.getName() + '.mrcs'))
                # print('time filename: {}s'.format(time.time() - st))
                mSS.setFileName(fileName)
                # acquisition.setMagnification(
                #     self.getMagnification(gr, mSS.getName()))
                # acquisition.setDosePerFrame(
                #     self.getDoseRate(gr, mSS.getName()))
                mSS.setAcquisition(self.acquisition)
                # la movie no esta en el raw, sino en la carpeta donde sreialEM escribe
                SOMSS.append(mSS)

                SOMSS.write()
                self._store(SOMSS)

            # STORE SQLITE
            SOMSS.setStreamState(SOMSS.STREAM_CLOSED)
            SOMSS.write()
            self._store(SOMSS)

            # SUMMARY INFO
            summaryF3 = self._getPath("summary3.txt")
            summaryF3 = open(summaryF3, "w")
            summaryF3.write("\nSmartscope importing movies\n\n" +
                "\t{}\tMovies Smartscope\n".format(len(SOMSS)))
            summaryF3.write("len(allHM) {} != len(self.MoviesSS) {}".format(
            len(allHM), len(self.MoviesSS)))
            summaryF3.close()

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
