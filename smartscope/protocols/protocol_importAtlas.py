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
#from ..objects.data_deprecated import *
from datetime import datetime
from pwem.emlib.image import ImageHandler
import numpy as np

LOW_MAG = 0
MED_MAG = 1

LOW_MAG_ID = 80
MED_MAG_ID = 1000

class ProtImportAtlas(ProtImport):
    """ Protocol to import Atlas. """

    """
        Imports cryo-EM atlas datasets from MRC and MDOC files, generating
        structured atlas objects and image slices for visualization and
        downstream screening workflows.

        AI Generated:

        Import Atlas (ProtImportAtlas) — User Manual
            Overview

            The Import Atlas protocol imports atlas datasets generated during
            cryo-EM acquisition sessions. Its main purpose is to organize atlas
            metadata and image slices from MRC and MDOC files into structured
            Scipion objects that can later be used for screening, navigation,
            and microscope workflow analysis.

            The protocol supports both low- and medium-magnification atlases,
            allowing users to reconstruct the acquisition layout and preserve
            important imaging metadata associated with each atlas slice.

            Inputs and Workflow

            The protocol requires an atlas MRC file containing the image stack.
            The associated MDOC metadata file is automatically detected and
            parsed using the same base filename. Users can select whether the
            imported atlas corresponds to low or medium magnification.

            During execution, the protocol reads the MDOC metadata, converts
            parameters into their appropriate internal data types, and extracts
            individual image slices from the MRC stack. Each slice is stored as
            an independent atlas image linked to the corresponding atlas object.

            Metadata Handling

            The protocol preserves a wide range of acquisition metadata,
            including magnification, pixel spacing, stage position, defocus,
            exposure conditions, image shifts, detector settings, and acquisition
            timestamps. This information allows the atlas to retain the original
            microscope acquisition context.

            For medium-magnification atlases, the protocol can also establish
            hierarchical links to previously imported low-magnification atlases,
            preserving spatial relationships between acquisition levels.

            Outputs

            After execution, the protocol generates an atlas object together
            with a corresponding set of atlas images. Each image contains both
            the extracted slice and its associated metadata parameters.

            The imported atlas can later be used for visualization, navigation,
            and automated cryo-EM screening workflows within Scipion.

            Final Perspective

            The Import Atlas protocol provides a structured mechanism for
            integrating microscope atlas acquisitions into Scipion workflows.
            By preserving both image data and acquisition metadata, the protocol
            facilitates reproducible screening, atlas visualization, and
            hierarchical cryo-EM data organization.
        """
    _label = 'import Atlas'
    _mdoc_file = ''
    _devStatus = BETA

    def _defineParams(self, form):
        """Define the input parameters for the protocol form.

        Adds controls for selecting atlas magnification level, the MRC file path,
        and an optional pointer to a low-mag atlas (visible only for medium-mag imports).
        """
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
        """Return the expected mdoc file path by appending '.mdoc' to the MRC file path."""
        return str(self.mrc_file.get() + '.mdoc')

    def _insertAllSteps(self):
        """Register the sequence of execution steps for the protocol."""
        self.initializeParams()
        self._insertFunctionStep('readParameters')
        self._insertFunctionStep('createOutputStep')

    def initializeParams(self):
        """Initialize instance variables before the main processing steps run."""
        self.mdoc_file = self.readMdocFile()
        self.headerDict = {}
        self.zvalueList = []

    def readParameters(self):
        """Parse the mdoc file and populate headerDict and zvalueList.

        Reads the mdoc metadata file associated with the MRC, converts all values
        to their appropriate Python types, extracts per-slice metadata into
        zvalueList, and calls createImagesSlices to write individual slice files.
        Also stores the magnification from the first slice entry.
        """
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
        """Build and register the atlas and its image set as protocol outputs.

        Creates either an AtlasLow or AtlasMed object depending on the selected
        magnification, populates all metadata fields from the parsed mdoc header
        and per-slice dictionaries, then defines both the atlas object and the
        corresponding set of images as named outputs.
        """
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
        """Return the object ID of the linked low-mag atlas (used for medium-mag imports)."""
        self.info(type(self.atlas2Link.get()))
        return self.atlas2Link.get().getObjId()


    def _validate(self):
        """Validate protocol inputs before execution. Returns a list of error strings."""
        pass

    def createImagesSlices(self):
        """Extract each Z-slice from the MRC stack and write it as an individual MRC file.

        Reads the full MRC volume, iterates over the first dimension (Z-slices),
        saves each slice to the extra path with a zero-padded name (e.g. 001_slice.mrc),
        and updates the corresponding entry in zvalueList with the new file path.
        """
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
        """Convert a raw string value from the mdoc file to its most specific Python type.

        Tries in order: datetime, space-separated list (converted to CSV string),
        integer, float, and falls back to the original string if none match.
        Returns None unchanged.
        """
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



