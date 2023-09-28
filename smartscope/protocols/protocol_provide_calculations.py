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

from pyworkflow.utils import Message
from pyworkflow import BETA, UPDATED, NEW, PROD
from pwem.protocols.protocol_import.base import ProtImport
from pyworkflow.protocol import ProtStreamingBase
from smartscope import Plugin
from pwem.objects import SetOfCTF, SetOfMicrographs, CTFModel, Micrograph
from pwem.emlib.image import ImageHandler
import pyworkflow.utils as pwutils
from pwem.utils import runProgram

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *
import math
import base64
import json

THUMBNAIL_FACTOR = 0.5
class provideCalculations(ProtImport, ProtStreamingBase):
    """
    This protocol provide the CTF and or the alignment to Smartscope
    """
    _label = 'Provide calculations'
    _devStatus = BETA

    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL

        self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
        self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
        self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)

        self.pyClient = MainPyClient(self.token, self.endpoint)
        self.connectionClient = dataCollection(self.pyClient)
        self.is_micro = False
        self.is_CTF = False
        self.CTF_stream = False
        self.Mic_stream = False


    def _defineParams(self, form):
        """ Define the input parameters that will be used.
        Params:
            form: this is the form to be populated with sections and params.
        """
        # You need a params to belong to a section:
        form.addSection(label=Message.LABEL_INPUT)
        #sesion de Smartscope -> para cada hole pregunto de que sesion viene su grid
        form.addParam('movieSmartscope', params.PointerParam, allowsNull=False,
                       pointerClass='SetOfMoviesSS',
                       label='Set of Movies',
                       help='Set of Movies imported by Smartscope connection protocol')

        form.addParam('CTFCalculated', params.PointerParam, allowsNull=True,
                       pointerClass='SetOfCTF',
                       label=pwutils.Message.LABEL_CTF_ESTI,
                       help='Set of CTFs calculated by any protocol')

        form.addParam('alignmentCalculated', params.PointerParam, allowsNull=True,
                       pointerClass='SetOfMicrographs',
                       label=pwutils.Message.LABEL_INPUT_MIC,
                       help='Set of micrographs aligned by any protocol')

        form.addParallelSection(threads=3, mpi=1)

    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        while True:
            #---MICROGRAPH----------
            moviesSS = self.movieSmartscope.get()
            Microset = self.alignmentCalculated.get()
            Micrographs_local = self.readAsList('Micro')
            MictoRead = []
            if Microset:
                self.is_micro = True
                self.Mic_stream = Microset.isStreamOpen()
                if Micrographs_local:
                    MicroLocalList = [os.path.basename(m.getFileName()) for m in Micrographs_local]
                    for m in Microset:
                        if os.path.basename(
                                m.getFileName()) not in MicroLocalList:
                            MictoRead.append(m)
                else:
                    MictoRead = Microset
                if MictoRead == []:
                    self.debug('No more Micrographs to read.')
                else:
                    self.info('Reading Micrographs...')
                    self.readMicrograph(moviesSS, MictoRead)
                    self.info('Micrographs read')
            else:
                self.info('No Micrographs to read.')

            #---CTF----------
            CTFset = self.CTFCalculated.get()
            SetOfCTFLocal = self.readAsList('CTF')
            CTFtoRead = []
            if CTFset:
                self.is_CTF = True
                self.CTF_stream = CTFset.isStreamOpen()
                if SetOfCTFLocal:
                    CTFLocalList = [os.path.basename(c.getPsdFile()) for c in SetOfCTFLocal]
                    for c in CTFset:
                        if os.path.basename(c.getPsdFile()) not in CTFLocalList:
                            print(os.path.basename(c.getPsdFile()))
                            CTFtoRead.append(c)
                else:
                    CTFtoRead = CTFset

                if CTFtoRead == []:
                    self.debug('No more CTFs to read.')
                else:
                    self.info('Reading CTFs...')
                    self.readCTF(moviesSS, CTFtoRead)
                    self.info('CTFs read')
            else:
                self.info('No CTF to read.')


            # SUMMARY INFO
            summary = self._getExtraPath("summary.txt")
            summary = open(summary, "w")
            summary.write('{} CTFs provided to Smartscope\n{} Micrographs provided to Smartscope'.format(
                len(self.readAsList('CTF')), len(self.readAsList('Micro'))))

            if (self.is_CTF and not self.CTF_stream and self.is_micro and not self.Mic_stream) or \
                (self.is_CTF and not self.CTF_stream and not self.is_micro) or \
                (not self.is_CTF and self.is_micro and not self.Mic_stream) or \
                (not self.is_CTF and not self.is_micro):
                self.info('Exiting protocol')
                break

            time.sleep(10)

    def readCTF(self, moviesSS, CTFtoRead):
        '''
        Get the movie of the CTF, and get the highmag id (hm_id)
        Run postCTF with the parameters to post, run setMoviesValues and uptade output
        :return:
        '''
        for CTF in CTFtoRead:
            CTF.getResolution()
            CTF.getPsdFile()
            CTF.getDefocusRatio()

            defocus = (CTF.getDefocusU() + CTF.getDefocusV()) / 2
            astig = abs(CTF.getDefocusU() - CTF.getDefocusV())
            MicName = CTF.getMicrograph().getMicName()
            movieLinked = False
            for movie in moviesSS:
                if movie.getFrames() == MicName:
                    movieLinked = True
                    self.debug('CTF to update: {}'.format(MicName))
                    image2Post = '/home/agarcia/Downloads/BPV_1387.mrc'
                    self.postCTF(movie.getHmId(),
                                 astig,
                                 CTF.getFitQuality(),
                                 defocus,
                                 '1.111111',
                                 CTF.getDefocusAngle(),
                                 #CTF.getPsdFile(),
                                 image2Post,
                                 movie.getHmId())
                    break
            if movieLinked == False:
                self.error('{} has not a movie associated. CTF not provided to Smartscope'.format(MicName))

    def postCTF(self, hmID, astig, ctffit, defocus, offset, angast, psdFile, HmID):
        self.pyClient.postParameterFromID('highmag', hmID, data={"astig": astig})
        self.pyClient.postParameterFromID('highmag', hmID, data={"ctffit": ctffit})
        self.pyClient.postParameterFromID('highmag', hmID, data={"defocus": defocus})
        self.pyClient.postParameterFromID('highmag', hmID, data={"offset": offset})
        self.pyClient.postParameterFromID('highmag', hmID, data={"angast": angast})

        payload = self.createJsonPath(self.createThumbnail(
            os.path.abspath(psdFile), 1, ext='png'))
        self.pyClient.postImages(HmID, {"ctf_img": payload}, devel=True)
        self.saveItemRead(psdFile, 'CTF')


        # pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
        #                              data={"astig": '100.00'})
        #set on the movieSS objects


    def readMicrograph(self, moviesSS, MictoRead):
        '''
        Get the movie of the CTF, and get the highmag id (hm_id)
        Run postCTF with the parameters to post, run setMoviesValues and uptade output
        :return:
        '''
        for m in MictoRead:
            MicName = m.getMicName()
            for movie in moviesSS:
                if movie.getFrames() == MicName:
                    self.debug('Micrograph to update: {}'.format(MicName))
                    #thumbnail = self.createThumbnail(m.getFileName())
                    # self.postMicrograph(movie.getHmId(), m.getFileName(), thumbnail)
                    # self.setMicrographValues(m,  m.getFileName(), thumbnail)
                    self.saveItemRead(MicName, 'Micro')

    def postMicrograph(self, hmID, MicPath, MicThum):
        self.pyClient.postParameterFromID('highmag', hmID, data={"MicPath": MicPath})
        self.pyClient.postParameterFromID('highmag', hmID, data={"MicThumbnail": MicThum})

        payload = self.createJsonPath(self.createThumbnail(
            os.path.abspath(MicPath), ext='png'))
        self.pyClient.postImages(hmID, {"png": payload}, devel=True)
        payload = self.createJsonPath(self.createThumbnail(
            os.path.abspath(MicPath), 1, ext='mrc'))
        self.pyClient.postImages(hmID, {"mrc": payload}, devel=True)


    # UTILS
    def createThumbnail(self, pathOriginal, FACTOR=THUMBNAIL_FACTOR, ext='jpg'):
        currentDir = os.getcwd()
        relativePath = os.path.join(currentDir, pathOriginal)
        path = os.path.splitext(os.path.basename(pathOriginal))[0] +  "_THUMB." + ext
        outPath = os.path.join(self._getExtraPath(), path)
        outPath = os.path.join(currentDir, outPath)

        args = '-i "%s" ' % self._getExtraPath(relativePath)
        args += '-o "%s" ' % outPath
        args += '--factor {} '.format(FACTOR)
        args += '-v 0 '

        runProgram('xmipp_image_resize', args)
        return outPath

    def createJsonPath(self, path):
        with open(path, "rb") as f:
            image = f.read()
            encoded_image = base64.b64encode(image).decode(encoding='ascii')
            payload = json.dumps({'png': encoded_image})
            return payload

    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users', dev=False)
        return response

    def saveItemRead(self, item2Write, item):
        if item == 'CTF':
            file = self._getExtraPath("CTfsRead.txt")
        else:
            file = self._getExtraPath("MicrosRead.txt")
        summaryF = open(file, "a")
        summaryF.write(item2Write + '\n')
        summaryF.close()

    def readAsList(self, item):
        list = []
        if item == 'CTF':
            file = self._getExtraPath("CTfsRead.txt")
        else:
            file = self._getExtraPath("MicrosRead.txt")
        try:
            file = open(file, "r")
        except FileNotFoundError: #First iteration
            return list
        for line in file.readlines():
            line = line.replace('\n', '')
            list.append(line.rstrip())
        file.close()
        return list

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
        self._validateThreads(errors)
        response = self.checkSmartscopeConnection()
        try:
            response[0]['username']
        except Exception as e:
            self.error(e)
            try:
                errors.append('Error Smartscope connection:\n{}'.format(response['detail']))
            except Exception:
                errors.append('Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(response))
        return errors