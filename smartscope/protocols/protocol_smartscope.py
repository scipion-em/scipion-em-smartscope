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

from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from pwem.protocols.protocol_import.base import ProtImport
from pyworkflow.protocol import ProtStreamingBase
import pyworkflow.utils as pwutils
from smartscope import Plugin
from pyworkflow.object import Set

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *

class smartscopeConnection(ProtImport, ProtStreamingBase):
    """
    This protocol will import all the metadata from the screenning managed by
    Smartscope. As input require the movies from Import Movies protocol,
    as output all the metadata as objects and the movies enrich with the metadatada
    """
    _label = 'Smartscope connection'
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

        self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
        self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
        self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)
        self.pyClient = MainPyClient(self.token, self.endpoint)
        self.connectionClient = dataCollection(self.pyClient)

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
        form.addParam('sessionName', params.StringParam,
                      important=True,
                      label='Session name of Smartscope',
                      help='Select a session to import the metadata. '
                           'The wizard provide a list of all sessions sorted by date.')

        form.addSection('Streaming')
        form.addParam('refreshTime', params.IntParam, default=120,
                      label="Time to refresh Smartscope data (secs)")
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
        listS = self.connectionClient.sessionCollection()
        for s in listS:
            if s.getSession() == self.sessionName.get():
                self.sessionId = s.getSessionId()

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
            self.SOS = self.Squares
        if self.Holes is None:
            self.SOH = SetOfHoles.create(outputPath=self._getPath())
        else:
            self.SOH = self.Holes

        self.startTime = time.time()
        self.reStartTime = time.time()
        self.ListMoviesImported = []


    def sessionListCollection(self):
        return self.connectionClient.sessionCollection()

    def sessionOpen(self):
        return self.connectionClient.sessionOpen()

    def metadataCollection(self):
        self.connectionClient.metadataCollection(self.microscopeList,
                                                 self.detectorList,
                                                 self.sessionList,
                                                 self.acquisition)
        MicroNames = ',  '.join([x.getName() for x in self.microscopeList])
        DetectorNames = ',  '.join([x.getName() for x in self.detectorList])
        SessionNames = ',  '.join([x.getSession() for x in self.sessionList])
        # SUMMARY INFO
        summaryF = self._getExtraPath("summary.txt")
        summaryF = open(summaryF, "w")
        summaryF.write("Smartscope Screening\n\n" +
            "\t{} Microscopes: {}\n".format(len(self.microscopeList), MicroNames) +
            "\t{} Detectors: {}\n".format(len(self.detectorList), DetectorNames) +
            "\t{} Sessions: {}\n".format(len(self.sessionList), SessionNames))
        summaryF.close()


    def screeningCollection(self):
        self.outputsToDefine = {'Grids': self.SOG,
                                'Atlas': self.SOA,
                                'Squares': self.SOS,
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
        summaryF2 = self._getExtraPath("summary2.txt")
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
            SOMSS.copyInfo(inputMovies)
            SOMSS.setSamplingRate(0)
            self.outputsToDefine = {'MoviesSS': SOMSS}
            self._defineOutputs(**self.outputsToDefine)
        else:
            SOMSS = self.MoviesSS


        for gr in self.Grids:
            dictMAPI = self.pyClient.getRouteFromID('highmag', 'grid', gr.getGridId())
            for m in dictMAPI:
                moviesAPI.append(m)

        ImportM = [m.getFrames() for m in SOMSS]
        for mAPI in moviesAPI:
            if mAPI['frames'] not in ImportM:
                moviesToAdd.append(mAPI)

        #Match movies to add and movies from importMovies protocol
        self.info('\n\nmoviesAPI: {}\nmoviesToAdd: {}'.format(len(moviesAPI), len(moviesToAdd)))
        notImportedMovies = []
        if moviesToAdd:
            if inputMovies is None:
                self.info('Set of movies from import movies protocol empty')
                return
            else:
                for mImport in inputMovies:
                    imported = False
                    for mAPI in moviesToAdd:
                        if mAPI['frames'] == os.path.basename(mImport.getFileName()):
                            imported = True
                            self.addMovieSS(SOMSS, mImport, mAPI, inputMovies)
                            break
                    if imported == False:
                        notImportedMovies.append(mImport)
                        self.info('Movie not imported: {}\n'.format(os.path.basename(mImport.getFileName())))

            # STORE SQLITE
            SOMSS.setStreamState(SOMSS.STREAM_CLOSED)
            self._store(SOMSS)

            # SUMMARY INFO
            summaryF3 = self._getExtraPath("summary3.txt")
            summaryF3 = open(summaryF3, "w")
            summaryF3.write("\nSmartscope importing movies\n\n" +
                            "\t{}\tMovies Smartscope\n".format(len(SOMSS)))
            summaryF3.write("\t{}\tMovies not imported\n".format(len(notImportedMovies)))
            summaryF3.close()
        else:
            self.info('All movies from the Smartscope API were imported. '
                      'See the output of the protocol')


    def addMovieSS(self, SOMSS, movieImport, movieSS, inputMovies):
        SOMSS.setStreamState(SOMSS.STREAM_OPEN)
        movieImport.setSamplingRate(movieSS['pixel_size'])
        movie2Add = MovieSS()
        movie2Add.copy(movieImport)

        movie2Add.setHmId(movieSS['hm_id'])
        movie2Add.setName(movieSS['name'])
        movie2Add.setNumber(movieSS['number'])
        if movieSS['pixel_size'] == None or movieSS['pixel_size'] == 'null':
            movie2Add.setSamplingRate(movieImport.getSamplingRate())
        else:
            movie2Add.setSamplingRate(movieSS['pixel_size'])
        if SOMSS.getSamplingRate() == 0:
            SOMSS.setSamplingRate(movie2Add.getSamplingRate())

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
        SOMSS.write()#persist on sqlite


    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response


    # --------------------------- INFO functions -----------------------------------
    def _summary(self):
        summary = []
        summaryF = self._getExtraPath("summary.txt")
        summaryF2 = self._getExtraPath("summary2.txt")
        summaryF3 = self._getExtraPath("summary3.txt")

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
        if Plugin.getVar(SMARTSCOPE_TOKEN) == 'Read Smartscope documentation to get the token...':
            errors.append('SMARTSCOPE_TOKEN has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration')
        if Plugin.getVar(SMARTSCOPE_LOCALHOST) == None:
            errors.append(
                'SMARTSCOPE_LOCALHOST has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration')
        if Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH) == 'Path assigned to the data in the Smartscope installation':
            errors.append(
                'SMARTSCOPE_DATA_SESSION_PATH has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration')

        response = self.checkSmartscopeConnection()
        try:
            response[0]['username']
        except Exception as e:
            try:
                errors.append('Error Smartscope connection:\n{}'.format(response['detail']))
            except Exception:
                errors.append('Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(response))

        return errors