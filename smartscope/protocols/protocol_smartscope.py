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
from sqlite3 import OperationalError

from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from pwem.protocols.protocol_import.base import ProtImport
from pyworkflow.protocol import ProtStreamingBase
import pyworkflow.utils as pwutils
from smartscope import Plugin
from pyworkflow.object import Set

from pyworkflow.protocol import params
from ..objects.dataCollection import *
import time
from ..constants import *


class smartscopeConnection(ProtImport, ProtStreamingBase):
    """
    This protocol will import all the metadata from the screenning managed by
    Smartscope. As input require the movies from Import Movies protocol,
    as output all the metadata as objects and the movies enrich with the metadatada
    """
    _label = 'Connection'
    _devStatus = BETA
    _possibleOutputs = {'Squares': SetOfSquares,
                        'Atlas': SetOfAtlas,
                        'Grids': SetOfGrids,
                        'Holes': SetOfHoles,
                        'MoviesSS': SetOfMoviesSS}
    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        self.newSteps = []
        self.Squares = None
        self.Atlas = None
        self.Grids = None
        self.Holes = None
        self.MoviesSS = None

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
        form.addParam('refreshMethod', params.EnumParam, default=0,
                      choices=['Input movies', 'Time'],
                      display=params.EnumParam.DISPLAY_HLIST,
                      label='Select input to refresh the protocol',
                      help='Select the parameter which triger the launch or refresh of the protocol.')
        form.addParam('refreshTime', params.IntParam, default=420,
                      condition='refreshMethod==1',
                      label="Time to refresh protocol",
                      help = "Time to launch or  refresh Smartscope connection. By default 420s (7mins)")
        form.addParam('refreshMovies', params.IntParam, default=200,
                      condition='refreshMethod==0',
                      label = 'Input movies to refresh protocol',
                      help="Number of new movies to launch or refresh Smartscope connection")
        form.addParam('TotalTime', params.IntParam, default=86400,
                      label="Time to finish Smartscope (secs)",
                      help='Time from the begining ot the protocol to '
                           'the end of the acquisicion. By default 1 day (86400 secs)')

    # --------------------------- STEPS functions ------------------------------
    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        self._initialize()
        while True:
            # DEBUGALBERTO START
            import os
            fname = "/home/agarcia/Documents/attachActionDebug.txt"
            if os.path.exists(fname):
                os.remove(fname)
            fjj = open(fname, "a+")
            fjj.write('ALBERTO--------->onDebugMode PID {}'.format(os.getpid()))
            fjj.close()
            print('ALBERTO--------->onDebugMode PID {}'.format(os.getpid()))
            time.sleep(10)
            # DEBUGALBERTO END
            delayInit = int(time.time() - self.startTime)
            #self.info('Time to Finish Smartscope: {} delayInit: {}s'.format(self.TotalTime, delayInit))
            inputMovies = self.inputMovies.get()
            if self.TotalTime <= delayInit:  # End of the protocol
                break
            if self.conditionRefresh(len(inputMovies)):
                startTime = time.time()
                if not self.metadataCollected:
                    self.metadataCollection()
                metaTime = time.time()
                self.screeningCollection()
                screenTime = time.time()
                self.importMoviesSS(inputMovies)
                moviesTime = time.time()
                timeCrop0 = time.time()
                self.cropHolePNG()
                timeCrop1 = time.time()
                self.info(f'Metadata Time: {round((metaTime - startTime), 1)}s')
                self.info(f'Screening Time: {round((screenTime - metaTime), 1)}s')
                self.info(f'ImportMovies Time: {round((moviesTime - screenTime), 1)}s')
                self.info(f'Crop Holes Time: {round((timeCrop1 - timeCrop0), 1)}s')
                self.info(f'Total Time: {round((timeCrop1 - startTime), 1)}s')
            if not inputMovies.isStreamOpen():
                self.info('Not more movies are expected; input setOfMovies closed')
                break

            time.sleep(self.refreshTime)

    def _initialize(self):
        self.metadataCollected = False
        self.acquisition = Acquisition()
        self.microscopeDict = {}
        self.detectorDict = {}
        self.sessionDict = {}
        self.initialNumMovies = 0
        self.listHoleCropedID = []
        self.zeroTime = time.time()
        self.rTime = self.refreshTime.get()
        if self.rTime < 240:
            self.rTime = 1240
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

    def conditionRefresh(self, lenInputMovies):
        if self.refreshMethod == 0:
            if lenInputMovies - self.initialNumMovies >= self.refreshMovies.get():
                self.initialNumMovies = lenInputMovies
                return True
            else:
                return False
        else:
            rTime = time.time() - self.zeroTime
            if rTime >= self.rTime:
                self.zeroTime = time.time()
                return True
            else:
                return False

    def sessionListCollection(self):
        return self.connectionClient.sessionCollection()

    def sessionOpen(self):
        return self.connectionClient.sessionOpen()

    def metadataCollection(self):
        self.info('Metadata collection...')
        self.connectionClient.metadataCollection(self.microscopeDict,
                                                 self.detectorDict,
                                                 self.sessionDict,
                                                 self.acquisition)
        microscopeName= ''
        detectorName = ''
        group = ''
        for key, session in self.sessionDict.items():
            if session.getSession() == self.sessionName.get():
                self.sessionId = session.getSessionId()
                self.sessionDate = session.getDate()
                self.groupName = session.getGroup()
                microscopeName = self.microscopeDict[session.getMicroscopeId()].getName()
                detectorName = self.detectorDict[session.getDetectorId()].getName()
                group = session.getGroup()

        # SUMMARY INFO
        summaryF = self._getExtraPath("summary.txt")
        summaryF = open(summaryF, "w")
        summaryF.write("Smartscope Screening\n\n" +
            "\tMicroscope: {}\n".format(microscopeName) +
            "\tDetectors: {}\n".format(detectorName) +
            "\tGroup: {}\n".format(group) +
            "\tSession: {}\n".format( self.sessionName.get()))
        summaryF.close()
        self.metadataCollected = True
        self.setSessionURL()

    def screeningCollection(self):
        self.info('Screening collection...')
        if len(self.SOG) == 0:
            self.outputsToDefine = {'Grids': self.SOG,
                                    'Atlas': self.SOA,
                                    'Squares': self.SOS,
                                    'Holes': self.SOH}
            self._defineOutputs(**self.outputsToDefine)
            self.SOG.enableAppend()
            self.SOA.enableAppend()
            self.SOS.enableAppend()
            self.SOH.enableAppend()
            # self._store(self.SOG)
            # self._store(self.SOA)
            # self._store(self.SOS)
            # self._store(self.SOH)

        self.gridsToCollect = self.checkNewGrid()
        self.atlasToCollect = self.checkNewAtlas()
        if self.gridsToCollect != []:self.info('Number grid in the session: {}'.format(len(self.gridsToCollect)))
        self.connectionClient.screeningCollection(self.dataPath,
                                                  self.sessionName,
                                                  self.SOG, self.SOA,
                                                  self.SOS, self.SOH,
                                                  self.groupName,
                                                  self.sessionDate,
                                                  self.gridsToCollect)
        # STORE SQLITE
        self.SOG.write()
        self.SOA.write()
        self.SOS.write()
        self.SOH.write()
        # self.SOH.setStreamState(self.SOH.STREAM_CLOSED)
        # self.SOA.setStreamState(self.SOA.STREAM_CLOSED)
        # self.SOS.setStreamState(self.SOS.STREAM_CLOSED)
        # self.SOH.setStreamState(self.SOH.STREAM_CLOSED)

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

    def cropHolePNG(self):
        self.info('Cropping hole image...')
        pathcrop = os.path.join(self._getExtraPath(), 'cropedHoles')
        if not os.path.exists(pathcrop):
            os.makedirs(pathcrop)
        import re
        counter = 0
        for m in self.MoviesSS:
            movieHoleId = m.getHoleId()
            hole = self.SOH.getItem("_hole_id", m.getHoleId())
            movieName = m.getName()
            matchHole = re.search(r'hole(\d+)', movieName)
            holeNum = int(matchHole.group(1))
            rawDir = hole.getRawDir()
            # shapeX = hole.getShapeX()
            # shapeY = hole.getShapeY()
            baseNameRaw = os.path.basename(rawDir)
            rawCroped = re.sub(r'(hole)\d+', 'hole{}'.format(holeNum), baseNameRaw)
            pathRawCroped = os.path.join(pathcrop, os.path.splitext(rawCroped)[0] + '.mrc')
            if baseNameRaw.find('133_hole47') != -1:
                pass
            if not movieHoleId in self.listHoleCropedID:
                fileName  = os.path.splitext(os.path.basename(rawDir))[0]
                if not fileName.startswith('holeUnacquired'):
                    if self.cropImage(hole, m.getX(), m.getY(), pathRawCroped,rawDir):
                        counter += 1
                        self.info(f'Croped {counter} hole images')
                        hole.setRawDir(pathRawCroped)
                        #self.SOH.update(hole)
                        # self.info(f'holeID append: {movieHoleId} movieName: {movieName}')
                self.listHoleCropedID.append(movieHoleId)
            #else:
                #self.info(f'movie: {movieName} with hole croped: {baseNameRaw}')
                #hole.setRawDir(pathRawCroped)
            self.SOH.update(hole)

        self.SOH.write()
        self._store(self.SOH)


    def cropImage(self, hole, X, Y, pathRawCroped, rawDir):
        '''Split the png image based on the position of the hole (x,y) and a boxSize'''
        from PIL import Image
        import numpy as np
        import mrcfile

        if os.path.isfile(rawDir):
            try:
                with mrcfile.open(rawDir, permissive=True) as mrc:
                    arr = mrc.data
                    if arr is None or arr.size == 0:
                        self.error("MRC data is empty or unreadable.")
                        return False
                height, width = arr.shape[:2]#TODO smartscope shape_X / Y provide 383803710 size 2 more pixels
                #print(f'[x - y]: [{X} - {Y}]      [width - height]: [{width} - {height}] ')
                try:
                    Range = int((hole.getHoleDiam() / 2) + (hole.getHoleSeparation() / 2) )# radius + (separation / 2)
                except Exception:
                    print(f'rawDir: {rawDir}\nhole: {hole.getName()}\n')
                    return False
                if Y - Range < 0:
                    arr_y = 0, Range
                elif Y + Range > height:
                    arr_y = height - Range, height
                else:
                    arr_y = Y - Range, Y + Range
                if X - Range < 0:
                    arr_x = 0, Range
                elif X + Range > width:
                    arr_x = width - Range, width
                else:
                    arr_x = X - Range, X + Range

                rawCrop = arr[arr_y[0]:arr_y[1], arr_x[0]:arr_x[1]]
                with mrcfile.new(pathRawCroped, overwrite=True) as mrc:
                    mrc.set_data(rawCrop.astype(np.float32))
                return True
            except Exception as e:
                print(e)
                return False

    def checkNewGrid(self):
        listInSessionGrids = []
        listCollectedGrids = []

        grid = self.pyClient.getRouteFromID('grids', 'session', self.sessionId, dev=False)
        if self.SOG:
            for gr in grid:
                listInSessionGrids.append(gr['grid_id'])
            for gridCollected in self.SOG.iterItems():
                listCollectedGrids.append(gridCollected.getGridId())

            gridsToCollect = list(set(listInSessionGrids) - set(listCollectedGrids))
            gridsToCollect.append(list(set(listCollectedGrids) - set(listInSessionGrids)))
            return gridsToCollect
        # for gr in grid:
        #     atlas = self.pyClient.getRouteFromID('atlas', 'grid', gridCollected.getGridId())
        else:
            return grid

    def checkNewAtlas(self):
        listInSessionAtlas = []
        listCollectedAtlas = []

        atlas = self.pyClient.getRouteFromID('atlas', 'session', self.sessionId, dev=False)
        if self.SOG:
            for at in atlas:
                listInSessionAtlas.append(at['atlas_id'])
            for atlasCollected in self.SOG.iterItems():
                listCollectedAtlas.append(atlasCollected.getAtlasId())

            atlasToCollect = list(set(listInSessionAtlas) - set(listInSessionAtlas))
            atlasToCollect.append(list(set(listCollectedAtlas) - set(listCollectedAtlas)))
            return atlasToCollect
        else:
            return atlas


    def importMoviesSS(self, inputMovies):
        self.info('importMoviesSS collection...')
        if self.MoviesSS == None:
            SOMSS = SetOfMoviesSS.create(outputPath=self._getPath())
            SOMSS.copyInfo(inputMovies)
            SOMSS.setSamplingRate(0)
            self.outputsToDefine = {'MoviesSS': SOMSS}
            self._defineOutputs(**self.outputsToDefine)
        else:
            SOMSS = self.MoviesSS

        if inputMovies is None:
            self.info('Set of movies from import movies protocol empty')
            return
        sizeMoviesInput = len(inputMovies)
        counterMoviesChecked = 1
        for gr in self.SOG:
            dictMAPI = self.pyClient.getRouteFromID('highmag', 'grid', gr.getGridId(), pageSize=500, endpoint='detailed')
            for m in dictMAPI:
                try:
                    inputMovies.getItem("_micName", m['frames'])
                    try:
                        SOMSS.getItem("_micName", m['frames'])#highMag movie from Smartscope imported previously
                    except OperationalError:
                        self.info(f"Collectiong ({counterMoviesChecked}/{sizeMoviesInput}) movie: {m['frames']}")
                        counterMoviesChecked += 1
                        #time0= time.time()
                        self.addMovieSS(SOMSS, inputMovies.getItem("_micName", m['frames']), m)
                        #print(f'time movie {counterMoviesChecked}: {time.time() - time0} s')
                except UnboundLocalError:
                    pass #highMag movie from Smartscope not in the inputMoviesSet

            # STORE SQLITE
            SOMSS.write()  # persist on sqlite
            SOMSS.setStreamState(SOMSS.STREAM_CLOSED)
            self._store(SOMSS)

            # SUMMARY INFO
            summaryF3 = self._getExtraPath("summary3.txt")
            summaryF3 = open(summaryF3, "w")
            summaryF3.write("\nSmartscope importing movies\n\n" +
                            "\t{}\tMovies Smartscope\n".format(len(SOMSS)))
            #summaryF3.write("\t{}\tMovies not imported\n".format(len(notImportedMovies)))
            summaryF3.close()

            self.info('All movies from the Smartscope API were imported. '
                      'See the output of the protocol')

    def addMovieSS(self, SOMSS, movieImport, movieSS):
        SOMSS.setStreamState(SOMSS.STREAM_OPEN)
        movie2Add = MovieSS()
        movie2Add.copy(movieImport)

        movie2Add.setHmId(movieSS['hm_id'])
        movie2Add.setName(movieSS['name'])
        movie2Add.setNumber(movieSS['number'])
        if 'finders' in movie2Add and movieSS['finders']:
            finder = movieSS['finders'][0]
            movie2Add.setX(finder['x'])
            movie2Add.setY(finder['y'])


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


    def setSessionURL(self):
        gridId = self.pyClient.getRouteFromID('grids', 'session', self.sessionId, dev=False)[0]['grid_id']
        URLSmartscopeGrid = self.pyClient.getURLFromGrid(gridId)
        with open(os.path.join(self._getExtraPath(),'URLsmartscopeSession.txt'), 'w') as fi:
            fi.write(URLSmartscopeGrid)

    # --------------------------- VALIDATION functions -----------------------------------
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
        if Plugin.getVar(SMARTSCOPE_TOKEN) == 'Read Smartscope documentation to get the token...':
            errors.append('SMARTSCOPE_TOKEN has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration')
        if Plugin.getVar(SMARTSCOPE_LOCALHOST) == None:
            errors.append(
                'SMARTSCOPE_LOCALHOST has not been configured, please visit https://github.com/scipion-em/scipion-em-smartscope#configuration')
        dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)
        if dataPath == 'Path assigned to the data in the Smartscope installation':
            errors.append(
        	    'SMARTSCOPE_DATA_SESSION_PATH has not been configured, '
        	    'please visit https://github.com/scipion-em/scipion-em-smartscope#configuration \n')
        if not os.path.isdir(dataPath):
            errors.append(
        	    f'SMARTSCOPE_DATA_SESSION_PATH: {dataPath} has wrong configuration, '
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