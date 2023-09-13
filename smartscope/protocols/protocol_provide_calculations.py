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
from pwem.objects import SetOfCTF, SetOfMicrographs
from pwem.emlib.image import ImageHandler
import pyworkflow.utils as pwutils
from pwem.utils import runProgram

from pyworkflow.protocol import params, STEPS_PARALLEL
from ..objects.dataCollection import *
import time
from ..constants import *
import math

THUMBNAIL_FACTOR = 0.1
class smartscopeFeedback(ProtImport, ProtStreamingBase):
    """
    This protocol provide the CTF and or the alignment to Smartscope
    """
    _label = 'provide smartscope calculations'
    _devStatus = BETA
    _possibleOutputs = {'Micrographs': SetOfMicrographs,
                        'CTF': SetOfCTF}

    def __init__(self, **args):
        ProtImport.__init__(self, **args)
        self.stepsExecutionMode = STEPS_PARALLEL

        self.token = Plugin.getVar(SMARTSCOPE_TOKEN)
        self.endpoint = Plugin.getVar(SMARTSCOPE_LOCALHOST)
        self.dataPath = Plugin.getVar(SMARTSCOPE_DATA_SESSION_PATH)

        self.pyClient = MainPyClient(self.token, self.endpoint)
        self.connectionClient = dataCollection(self.pyClient)
        self.CTF = None
        self.Micrographs = None
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
                       label='Set of CTFs',
                       help='Set of CTFs calculated by any protocol')

        form.addParam('alignmentCalculated', params.PointerParam, allowsNull=True,
                       pointerClass='SetOfMicrographs',
                       label='Set of micrographs',
                       help='Set of micrographs aligned by any protocol')

        form.addParallelSection(threads=3, mpi=1)

    def stepsGeneratorStep(self):
        """
        This step should be implemented by any streaming protocol.
        It should check its input and when ready conditions are met
        call the self._insertFunctionStep method.
        """
        while True:
            if self.Micrographs == None:
                SOMic = SetOfMicrographs.create(outputPath=self._getPath())
                self.outputsToDefine = {'SetOfMicrographs': SOMic}
                self._defineOutputs(**self.outputsToDefine)
            else:
                SOMic = self.Micrographs

            if self.CTF == None:
                SOCTF = SetOfCTF.create(outputPath=self._getPath())
                self.outputsToDefine = {'SetOfCTF': SOCTF}
                self._defineOutputs(**self.outputsToDefine)
            else:
                SOCTF = self.CTF

            moviesSS = self.movieSmartscope.get()
            Microset = self.alignmentCalculated.get()
            if Microset:
                self.is_micro = True
                self.Mic_stream = Microset.isStreamOpen()
                if self.Micrographs:
                    self.MictoRead = [x for x in Microset if x not in self.Micrographs]
                else:
                    self.MictoRead = Microset
                if self.MictoRead == []:
                    self.info('No more Micrographs to read.')
                else:
                    self.info('Reading Micrographs...')
                    self.readMicrograph(SOMic, moviesSS)
            else:
                self.info('No Micrographs to read.')

            CTFset = self.CTFCalculated.get()
            if CTFset:
                self.is_CTF = True
                self.CTF_stream = CTFset.isStreamOpen()
                if self.CTF:
                    self.CTFtoRead = [x for x in CTFset if x not in self.CTF]#TODO comprobar que se rellena a medias si es el caso
                else:
                    self.CTFtoRead = CTFset

                if self.CTFtoRead == []:
                    self.info('No more CTFs to read.')
                else:
                    self.info('Reading CTFs...')
                    self.readCTF(SOCTF, moviesSS)
            else:
                self.info('No CTF to read.')


            if (self.is_CTF and not self.CTF_stream and self.is_micro and not self.Mic_stream) or \
                (self.is_CTF and not self.CTF_stream and not self.is_micro) or \
                (not self.is_CTF and self.is_micro and not self.Mic_stream) or \
                (not self.is_CTF and not self.is_Micro):
                print('Exiting protocol')
                break

    def readCTF(self, SOCTF, moviesSS):
        '''
        Get the movie of the CTF, and get the highmag id (hm_id)
        Run postCTF with the parameters to post, run setMoviesValues and uptade output
        :return:
        '''
        for CTF in self.CTFtoRead:
            CTF.getResolution()
            CTF.getPsdFile()
            CTF.getDefocusRatio()

            defocus = (CTF.getDefocusU() + CTF.getDefocusV()) / 2
            astig = abs(CTF.getDefocusU() - CTF.getDefocusV())
            MicName = CTF.getMicrograph().getMicName()
            for movie in moviesSS:
                if movie.getFrames() == MicName:
                    self.info('CTF to update: {}'.format(MicName))
                    thumbnail = self.createThumbnail(CTF.getPsdFile())
                    self.postCTF(movie.getHmId(),
                                 astig,
                                 CTF.getFitQuality(),
                                 defocus,
                                 '1.111111',
                                 CTF.getDefocusAngle())
                    self.setMoviesValues(movie,
                                 astig,
                                 CTF.getFitQuality(),
                                 defocus,
                                 '1.111111',
                                 CTF.getDefocusAngle())
                    self.updateOutputCTF(SOCTF, CTF)
                    break

    def postCTF(self, hmID, astig, ctffit, defocus, offset, angast):
        self.pyClient.postParameterFromID('highmag', hmID, data={"astig": astig})
        self.pyClient.postParameterFromID('highmag', hmID, data={"ctffit": ctffit})
        self.pyClient.postParameterFromID('highmag', hmID, data={"defocus": defocus})
        self.pyClient.postParameterFromID('highmag', hmID, data={"offset": offset})
        self.pyClient.postParameterFromID('highmag', hmID, data={"angast": angast})


        # pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
        #                              data={"astig": '100.00'})
        # pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
        #                          data={"ctffit": '100.00'})
        # pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
        #                          data={"defocus": '100.00'})
        # pyClient.postParameterFromID('highmag', 'long_square15_hole10eRoomMJvKy',
        #                          data={"offset": '100.00'})
        #set on the movieSS objects

    def setMoviesValues(self, movie,  astig, ctffit, defocus, offset, angast):
        movie.setAstig(astig)
        movie.setCtffit(ctffit)
        movie.setDefocus(defocus)
        #movie.setOffset(offset)
        movie.setAngast(angast)

    def updateOutputCTF(self, SOCTF, CTF2Add):
        SOCTF.setStreamState(SOCTF.STREAM_OPEN)

        SOCTF.append(CTF2Add)
        if self.hasAttribute('SetOfCTF'):
            SOCTF.write()
            outputAttr = getattr(self, 'SetOfCTF')
            outputAttr.copy(SOCTF, copyId=False)
            self._store(outputAttr)
        # STORE SQLITE
        SOCTF.setStreamState(SOCTF.STREAM_CLOSED)
        self._store(SOCTF)


    def readMicrograph(self, SOMic, moviesSS):
        '''
        Get the movie of the CTF, and get the highmag id (hm_id)
        Run postCTF with the parameters to post, run setMoviesValues and uptade output
        :return:
        '''
        for m in self.MictoRead:
            MicName = m.getMicName()
            for movie in moviesSS:
                if movie.getFrames() == MicName:
                    self.info('Micrograph to update: {}'.format(MicName))
                    thumbnail = self.createThumbnail(m.getFileName())
                    # self.postMicrograph(movie.getHmId(), m.getFileName(), thumbnail)
                    # self.setMicrographValues(m,  m.getFileName(), thumbnail)
                    # self.updateOutputCTF(SOMic, m)


    def postMicrograph(self, hmID, MicPath, MicThum):
        self.pyClient.postParameterFromID('highmag', hmID, data={"MicPath": MicPath})
        self.pyClient.postParameterFromID('highmag', hmID, data={"MicThumbnail": MicThum})

    def setMicrographValues(self, m, MicPath, MicThum):
        m.setPath(MicPath)

    def updateOutputMic(self):
        pass

    # UTILS
    def createThumbnail(self, pathOriginal):
        currentDir = os.getcwd()
        relativePath = os.path.join(currentDir, pathOriginal)
        path = os.path.splitext(os.path.basename(pathOriginal))[0] +  "_THUMB.jpg"
        outPath = os.path.join(self._getExtraPath(), path)
        outPath = os.path.join(currentDir, outPath)

        args = '-i "%s" ' % self._getExtraPath(relativePath)
        args += '-o "%s" ' % outPath
        args += '--factor {} '.format(THUMBNAIL_FACTOR)
        args += '-v 0 '

        runProgram('xmipp_image_resize', args)


    def checkSmartscopeConnection(self):
        response = self.pyClient.getDetailsFromParameter('users')
        return response

    def _summary(self):
        summary = []


        return summary


    def _validate(self):
        errors = []
        self._validateThreads(errors)
        response = self.checkSmartscopeConnection()
        try:
            response[0]['username']
        except Exception as e:
            try:
                errors.append('Error Smartscope connection:\n{}'.format(response['detail']))
            except Exception:
                errors.append('Error Smartscope connection. Maybe launch Smartscope container...\n\n{}'.format(response))
        return errors