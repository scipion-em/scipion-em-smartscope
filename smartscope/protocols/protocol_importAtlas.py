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
import shutil

from ..objects import AtlasLow
import os
from pwem.protocols.protocol_import.base import ProtImportFiles, ProtImport
from pyworkflow.constants import BETA
from pyworkflow.protocol import params
from pyworkflow.utils import Message
from ..objects.data import *
from datetime import datetime
from pwem.emlib.image import ImageHandler
import numpy as np

LOW_MAG = 0
MED_MAG = 1

LOW_MAG_ID = 80
MED_MAG_ID = 1000

class ProtImportAtlas(ProtImport):
    """ Protocol to import Atlas. """
    _label = 'import Atlas'
    _mdoc_file = ''
    _devStatus = BETA

    def _defineParams(self, form):
        form.addSection(label=Message.LABEL_INPUT)
        form.addParam('atlasMag', params.EnumParam, default=0,
                      choices=['Low magnification', 'Medium magnification'],
                      label='Atlas magnification',
                      help='Select the magnificacion of the atlas to import')

        form.addParam('mrc_file', params.FileParam,
                  label='mrc file',
                  help="Select the Atlas mrc file that contain all the \n"
                           "slices of the Atlas. The protocol will import the"
                       " mdoc file (it has the same name that the mrc file)")

        form.addParam('atlas2Link', params.PointerParam,
                      pointerClass='AtlasLow',
                      condition="atlasMag==%d" % MED_MAG,
                      label="Atlas low magnification",
                      help='Atlas low magnification associated to the imported one'
                           '')


    def readMdocFile(self):
        return str(self.mrc_file.get() + '.mdoc')

    def _insertAllSteps(self):
        self.initializeParams()
        self._insertFunctionStep('readParameters')
        self._insertFunctionStep('createOutputStep')

    def initializeParams(self):
        self.mdoc_file = self.readMdocFile()
        self.headerDict = {}
        self.zvalueList = []

    def readParameters(self):
        mdoc = MDoc(self.mdoc_file)
        hDict, valueList = mdoc.parseMdoc()
        self.zvalueList = []
        self.headerDict = {}
        for k, v in hDict.items():
            self.headerDict[k] = self.getStringType(v)

        for l in valueList:
            dic = {}
            for k, v in l.items():
                dic[k] = self.getStringType(v)
            self.zvalueList.append(dic)

        self.createImagesSlices()
        shutil.copyfile(self.mdoc_file, self._getExtraPath(os.path.basename(self.mdoc_file)))
        self.magnification = int(self.zvalueList[0]['Magnification'])

    def createOutputStep(self):
        if self.atlasMag.get() == LOW_MAG:
            atlas = AtlasLow()
            atlas.setObjId(self.magnification)
            setOfAtlasIm = SetOfLowMagImages.create(outputPath=self._getPath())
            setOfAtlasIm.setAtlasLowID(atlas.getObjId())
        else:
            atlas = AtlasMed()
            atlas.setObjId(self.magnification)
            atlas.setAtlasLowID(self.getLinkingAtlasID())
            self.info(self.getLinkingAtlasID())
            setOfAtlasIm = SetOfMedMagImages.create(outputPath=self._getPath())
            setOfAtlasIm.setAtlasMedID(atlas.getObjId())


        atlas.setFileName(self.mrc_file.get())
        atlas.setVoltage(self.headerDict['Voltage'])
        atlas.setPixelSpacing(self.headerDict['PixelSpacing'])
        atlas.setImageFile(self.headerDict['ImageFile'])
        atlas.setImageSize(self.headerDict['ImageSize'])
        atlas.setMontage(self.headerDict['Montage'])
        atlas.setDataMode(self.headerDict['DataMode'])
        atlas.setMagnification(self.magnification)
        atlas.setBinning(self.zvalueList[0]['Binning'])

        for dict in self.zvalueList:
            if self.atlasMag.get() == LOW_MAG:
                image = AtlasLowImage()
            else:
                image = AtlasMedImage()

            image.setzValue(dict['zvalue'])
            image.setFileName(dict['imageName'])
            image.setAtlasID(atlas.getObjId())
            image.setPieceCoordinates(dict['PieceCoordinates'])
            image.setMinMaxMean(dict['MinMaxMean'])
            image.setTiltAngle(dict['TiltAngle'])
            image.setStagePosition(dict['StagePosition'])
            image.setStageZ(dict['StageZ'])
            image.setMagnification(dict['Magnification'])
            image.setIntensity(dict['Intensity'])
            image.setExposureDose(dict['ExposureDose'])
            image.setDoseRate(dict['DoseRate'])
            image.setPixelSpacing(dict['PixelSpacing'])
            image.setSpotSize(dict['SpotSize'])
            image.setDefocus(dict['Defocus'])
            image.setImageShift(dict['ImageShift'])
            image.setRotationAngle(dict['RotationAngle'])
            image.setExposureTime(dict['ExposureTime'])
            image.setBinning(dict['Binning'])
            image.setCameraIndex(dict['CameraIndex'])
            image.setDividedBy2(dict['DividedBy2'])
            image.setOperatingMode(dict['OperatingMode'])
            image.setUsingCDS(dict['UsingCDS'])
            image.setMagIndex(dict['MagIndex'])
            image.setLowDoseConSet(dict['LowDoseConSet'])
            image.setCountsPerElectron(dict['CountsPerElectron'])
            image.setTargetDefocus(dict['TargetDefocus'])
            image.setDateTime(dict['DateTime'])
            image.setFilterSlitAndLoss(dict['FilterSlitAndLoss'])
            image.setUncroppedSize(dict['UncroppedSize'])
            image.setRotationAndFlip(dict['RotationAndFlip'])
            image.setAlignedPieceCoords(dict['AlignedPieceCoords'])
            image.setXedgeDxy(dict['XedgeDxy'])
            image.setYedgeDxy(dict['YedgeDxy'])
            setOfAtlasIm.append(image)

        self.debug('Solo si esta activado modo debug')
        self.outputsToDefine = {'atlas': atlas, 'setOfAtlasImages': setOfAtlasIm}
        self._defineOutputs(**self.outputsToDefine)

    def getLinkingAtlasID(self):
        self.info(type(self.atlas2Link.get()))
        return self.atlas2Link.get().getObjId()


    def _validate(self):
        pass

    def createImagesSlices(self):
        if os.path.isfile(self.mrc_file.get()):
            atlasImages = ImageHandler().read(self.mrc_file.get())
            images = atlasImages.getData()
            for d in range(np.shape(images)[0]):
                slice_image = ImageHandler().createImage()
                sliceMatrix = images[d, :, :]
                slice_image.setData(sliceMatrix)
                numberDigit = str(d+1).rjust(3, '0')
                strName = '{}_slice.mrc'.format(numberDigit)
                strPath = os.path.join(self._getExtraPath(), strName)
                slice_image.write(os.path.join(self._getExtraPath(), strName))
                self.zvalueList[d]['imageName'] = strPath


    #UTILS
    def getStringType(self, string):
        if string == None or 'None':
            return string
        try:#date
            date = datetime.strptime(string, '%d-%b-%y %H:%M:%S')
            return date
        except ValueError or TypeError:
            pass
        if string.__contains__(' '): #list
            str2Csv = string.replace(' ', ',')
            return str2Csv
        try:#int
            return Integer(string)
        except ValueError:
            pass
        try:#float
            return Float(string)
        except ValueError:
            pass

        return string


