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


    def metadataCollection(self, microscopeList, detectorList, sessionList):
        microscopes = self.pyClient.getDetailsFromParameter('microscopes')
        for m in microscopes:
            micro = Microscope()
            micro.setMicroscopeId(m['microscope_id'])
            micro.setName(m['name'])
            micro.setLocation(m['location'])
            micro.setVoltage(m['voltage'])
            micro.setSphericalabberation(m['spherical_abberation'])
            micro.setVendor(m['vendor'])
            microscopeList.append(micro)

        detector = self.pyClient.getDetailsFromParameter('detectors')
        for d in detector:
            det = Detector()
            det.set_Id(d['id'])
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
            detectorList.append(det)

        Sessions = self.pyClient.getDetailsFromParameter('sessions')
        for s in Sessions:
            ses = Session()
            ses.setSessionId(s['session_id'])
            ses.setSession(s['session'])
            ses.setDate(s['date'])
            ses.setVersion(s['version'])
            ses.setWorkingDir(s['working_dir'])
            ses.setGroup(s['group'])
            ses.setMicroscopeId(s['microscope_id'])
            ses.setDetectorId(s['detector_id'])
            sessionList.append(ses)


    def screeningCollection(self, sessionId, setOfGrids, setOfAtlas, setOfSquares, setOfHoles):
        print('sessionID: {}'.format(sessionId))
        grid = self.pyClient.getRouteFromID('grids', 'session', sessionId)
        for g in grid:
            gr = Grid()
            gr.setGridId(g['grid_id'])
            gr.setPosition(g['position'])
            gr.setName(g['name'])
            gr.setHoleAngle(g['hole_angle'])
            gr.setMeshAngle(g['mesh_angle'])
            gr.setQuality(g['quality'])
            gr.setNotes(g['notes'])
            gr.setStatus(g['status'])
            gr.setStartTime(g['start_time'])
            gr.setLastUpdate(g['last_update'])
            gr.setSessionId(g['session_id'])
            gr.setHoleType(g['holeType'])
            gr.setMeshSize(g['meshSize'])
            gr.setMeshMaterial(g['meshMaterial'])
            gr.setParamsId(g['params_id'])
            setOfGrids.append(gr)

            atlas = self.pyClient.getRouteFromID('atlas', 'grid', gr.getGridId())
            for a in atlas:
                at = Atlas()
                at.setAtlasId(a['atlas_id'])
                at.setAtlasName(a['name'])
                at.setPixelSize(a['pixel_size'])
                at.setBinningFactor(a['binning_factor'])
                at.setShapeX(a['shape_x'])
                at.setShapeY(a['shape_y'])
                at.setShapeZ(a['stage_z'])
                at.setStatus(a['status'])
                at.setCompletionTime(a['completion_time'])
                at.setGridId(a['grid_id'])
                setOfAtlas.append(at)

                squares = self.pyClient.getRouteFromID('squares', 'atlas', at.getAtlasId())
                for s in squares:
                    sq = Square()
                    sq.setSquareId(s['square_id'])
                    sq.setName(s['name'])
                    sq.setNumber(s['number'])
                    sq.setPixelSize(s['pixel_size'])
                    sq.setShapeX(s['shape_x'])
                    sq.setShapeY(s['shape_y'])
                    sq.setSelected(s['selected'])
                    sq.setStatus(s['status'])
                    sq.setCompletionTime(s['completion_time'])
                    sq.setArea(s['area'])
                    sq.setGridId(s['grid_id'])
                    sq.setAtlasId(s['atlas_id'])
                    setOfSquares.append(sq)

                    holes = self.pyClient.getRouteFromID('holes', 'square', sq.getSquareId())
                    for h in holes:
                        ho = Hole()
                        ho.setHoleId(h['hole_id'])
                        ho.setName(h['name'])
                        ho.setNumber(h['number'])
                        ho.setPixelSize(h['pixel_size'])
                        ho.setShapeX(h['shape_x'])
                        ho.setShapeY(h['shape_y'])
                        ho.setSelected(h['selected'])
                        ho.setStatus(h['status'])
                        ho.setCompletionTime(h['completion_time'])
                        ho.setRadius(h['radius'])
                        ho.setArea(h['area'])
                        ho.setBisGroup(h['bis_group'])
                        ho.setBisType(h['bis_type'])
                        ho.setGridId(h['grid_id'])
                        ho.setSquareId(h['square_id'])
                        setOfHoles.append(ho)









