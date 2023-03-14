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

'''In this script will be collected all the data from the smartscope API
Will be created by the protocol and it will call the functions each time required
Divided by metadata collection (user, group, hooletype, meshsize,
 meshmaterial, microscope, detectors,  sessions) and screening collection
 (grid, atlas, squares, holes, highmag)
'''

from pwem.objects import EMObject, Image, EMSet, Movie, Pointer, SetOfMovies
from pyworkflow.object import (Float, String, List, Integer, CsvList, Boolean)
from ..objects.data import *
from ..pyclient.basic import *

class dataCollection():
    def __init__(self, Authorization, endpoint):
        self._authorization = Authorization #'Token 136737181feb270a1bc4120b19d5440b2f697c94'
        self._main_endpoint = endpoint #'http://localhost:48000/api/'
        self.pyClient = MainPyClient(
            'Token 136737181feb270a1bc4120b19d5440b2f697c94',
            'http://localhost:48000/api/')

        self.microscopeList = [] #list of microscope Scipion object
        self.detectorList = [] #list of detector Scipion object
        self.sesionList = [] #list of sessions Scipion object
    def metadataCollection(self):
        microscopes = pyClient.getDetailsFromParameter('microscopes')
        for m in microscopes:
            micro = Microscope()
            micro.setMicroscopeId(m['micoscope_id'])
            micro.setName(m['name'])
            micro.setLocation(m['location'])
            micro.setVoltage(m['voltage'])
            micro.setSphericalabberation(m['spherical_abberation'])
            micro.setVendor(m['vendor'])
            self.microscopeList.append(micro)

        detector = pyClient.getDetailsFromParameter('detectors')
        for d in detector:
            det = Detector()
            det.set_Id(d['_id'])
            det.setName(d['name'])
            det.setDetectorModel(d['detector_model'])
            det.setAtlasMag(d['atlas_mag'])
            det.setAtlasMaxTilesX(d['atlas_max_tiles_X'])
            det.setAtlasMaxTilesY(d['atlas_max_tiles_Y'])
            det.setSpotSize(d['spot_size'])
            det.setC2Perc(d['c2_perc'])
            det.setAtlasToSearchOffsetX(d['atlas_to_search_offset_x'])
            det.setAtlasToSearchOffsetY(d['atlas_to_search_offset_y'])
            det.setFrameAlignCmd(d['frame_align_cmd'])
            det.setGainRot(d['gain_rot'])
            det.setGainFlip(d['gain_flip'])
            det.setEnergyFilter(d['energy_filter'])
            self.detectorList.append(det)

        Sessions = pyClient.getDetailsFromParameter('Sessions')
        for s in Sessions:
            ses = Detector()
            ses.setSessionId(s['session_id'])
            ses.setSession(s['session'])
            ses.setDate(s['date'])
            ses.setVersion(s['version'])
            ses.setWorkingDir(s['working_dir'])
            ses.setGroup(s['group'])
            ses.setMicroscopeId(s['microscope_id'])
            ses.setDetectorId(s['detector_id'])
            self.sesionList.append(det)


    def screeningCollection(self):
        pass