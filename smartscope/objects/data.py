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
import os.path
from pwem.objects import EMObject, Image, EMSet, Movie, Pointer, SetOfMovies, SetOfImages
from pyworkflow.object import (Float, String, List, Integer, CsvList, Boolean)


## TODO: there is information of the .mdoc of all kinds of data (atlas, squares, holes and high mag) provided by SmartScope that could be useful



#-----METADATA
class Microscope(EMObject):
    """Microscope information"""
    def __init__(self,  **kwargs):
        EMObject.__init__(self, location=None, **kwargs)
        self._microscope_id = String()
        self._name = String()
        self._location = String()
        self._voltage = String()
        self._spherical_abberation = String()
        self._vendor = String()
        self._loader_size = String()
        self._worker_hostname = String()
        self._executable = String()
        self._serialem_IP = String()
        self._serialem_PORT = String()
        self._windows_path = String()
        self._scope_path = String()
        
    
    def setMicroscopeId(self, MicroscopeId):
        self._microscope_id.set(MicroscopeId)
    def setName(self, Name):
        self._name.set(Name)
    def setLocation(self, Location):
        self._location.set(Location)
    def setVoltage(self, Voltage):
        self._voltage.set(Voltage)
    def setSphericalabberation(self, Sphericalabberation):
        self._spherical_abberation.set(Sphericalabberation)
    def setVendor(self, Vendor):
        self._vendor.set(Vendor)
    def setLoaderSize(self, loader_size):
        self._loader_size.set(loader_size)
    def setWorkerHostname(self, worker_hostname):
        self._worker_hostname.set(worker_hostname)
    def setExecutable(self, executable):
        self._executable.set(executable)
    def setSerialemIP(self, serialem_IP):
        self._serialem_IP.set(serialem_IP)
    def setSerialemPORT(self, serialem_PORT):
        self._serialem_PORT.set(serialem_PORT)
    def setWindowsPath(self, windows_path):
        self._windows_path.set(windows_path)    
    def setScopePath(self, scope_path):
        self._scope_path.set(scope_path)

    def getMicroscopeId(self):
        return self._microscope_id.get()
    def getName(self):
        return self._name.get()
    def getLocation(self):
        return self._location.get()
    def getVoltage(self):
        return self._voltage.get()
    def getSphericalabberation(self):
        return self._spherical_abberation.get()
    def getVendor(self):
        return self._vendor.get()
    def getWorkerHostname(self):
        return self._worker_hostname.get()
    def getExecutable(self):
        return self._executable.get()
    def getSerialemIP(self):
        return self._serialem_IP.get()
    def getSerialemPORT(self):
        return self._serialem_PORT.get()
    def getWindowsPath(self):
        return self._windows_path.get()
    def getScopePath(self):
        return self._scope_path.get()

class Detector(EMObject):
    """Detector information"""
    def __init__(self,  **kwargs):
        EMObject.__init__(self, location=None, **kwargs)
        self._Id = String()
        self._name = String()
        self._detector_model = String()
        self._atlas_mag = Integer()
        self._atlas_max_tiles_X = Integer()
        self._atlas_max_tiles_Y = Integer()
        self._spot_size = Integer()
        self._c2_perc = Integer()
        self._atlas_to_search_offset_x = Integer()
        self._atlas_to_search_offset_y = Integer()
        self._frame_align_cmd = String()
        self._gain_rot = Integer()
        self._gain_flip = String()
        self._energy_filter = String()

    def set_Id(self, id):
        self._Id.set(id)
    def setName(self, _name):
        self._name.set(_name)
    def setDetectorModel(self, _detector_model):
        self._detector_model.set(_detector_model)
    def setAtlasMag(self, _atlas_mag):
        self._atlas_mag.set(_atlas_mag)
    def setAtlasMaxTilesX(self, _atlas_max_tiles_X):
        self._atlas_max_tiles_X.set(_atlas_max_tiles_X)
    def setAtlasMaxTilesY(self, _atlas_max_tiles_Y):
        self._atlas_max_tiles_Y.set(_atlas_max_tiles_Y)
    def setSpotSize(self, _spot_size):
        self._spot_size.set(_spot_size)
    def setC2Perc(self, _c2_perc):
        self._c2_perc.set(_c2_perc)
    def setAtlasToSearchOffsetX(self, _atlas_to_search_offset_x):
        self._atlas_to_search_offset_x.set(_atlas_to_search_offset_x)
    def setAtlasToSearchOffsetY(self, _atlas_to_search_offset_Y):
        self._atlas_to_search_offset_y.set(_atlas_to_search_offset_Y)
    def setFrameAlignCmd(self, _frame_align_cmd):
        self._frame_align_cmd.set(_frame_align_cmd)
    def setGainRot(self, _gain_rot):
        self._gain_rot.set(_gain_rot)
    def setGainFlip(self, _gain_flip):
        self._gain_flip.set(_gain_flip)
    def setEnergyFilter(self, _energy_filter):
        self._energy_filter.set(_energy_filter)
        
    def get_Id(self):
        return self._Id.get()
    def getName(self):
        return self._name.get()
    def getDetectorModel(self):
        return self._detector_model.get()
    def getAtlasMag(self):
        return self._atlas_mag.get()
    def getAtlasMaxTilesX(self):
        return self._atlas_max_tiles_X.get()
    def getAtlasMaxTilesY(self):
        return self._atlas_max_tiles_Y.get()
    def getSpotSize(self):
        return self._spot_size.get()
    def getC2Perc(self):
        return self._c2_perc.get()
    def getAtlasToSearchOffgetX(self):
        return self._atlas_to_search_offget_x.get()
    def getAtlasToSearchOffgetY(self):
        return self._atlas_to_search_offget_y.get()
    def getFrameAlignCmd(self):
        return self._frame_align_cmd.get()
    def getGainRot(self):
        return self._gain_rot.get()
    def getGainFlip(self):
        return self._gain_flip.get()
    def getEnergyFilter(self):
        return self._energy_filter.get()

class Session(EMObject):
    """Sessions information"""
    def __init__(self,  **kwargs):
        EMObject.__init__(self, location=None, **kwargs)
        self._session_id = String()
        self._session = String()
        self._date = String()
        self._version = String()
        self._working_dir = String()
        self._group = String()
        self._microscope_id = String()
        self._detector_id = Integer()
        
    def setSessionId(self, id):
        self._session_id.set(id)
    def setSession(self, session):
        self._session.set(session)
    def setDate(self, date):
        self._date.set(date)
    def setVersion(self, Version):
        self._version.set(Version)
    def setWorkingDir(self, WorkingDir):
        self._working_dir.set(WorkingDir)
    def setGroup(self, Group):
        self._group.set(Group)
    def setMicroscopeId(self, MicroscopeId):
        self._microscope_id.set(MicroscopeId)
    def setDetectorId(self, DetectorId):
        self._detector_id.set(DetectorId)
        
    def getSessionId(self):
        return self._session_id.get()
    def getSession(self):
        return self._session.get()
    def getDate(self):
        return self._date.get()
    def getVersion(self):
        return self._version.get()
    def getWorkingDir(self):
        return self._working_dir.get()
    def getGroup(self):
        return self._group.get()
    def getMicroscopeId(self):
        return self._microscope_id.get()
    def getDetectorId(self):
        return self._detector_id.get()


#-----SCREENING
class Grid(EMObject):
    """Grid information"""
    def __init__(self,  **kwargs):
        EMObject.__init__(self, location=None, **kwargs)
        self._grid_id = String()
        self._position = String()
        self._name = String()
        self._hole_angle = String()
        self._mesh_angle = String()
        self._quality = String()
        self._notes = String()
        self._status = String()
        self._start_time = String()
        self._last_update = String()
        self._session_id = String()
        self._holeType = String()
        self._meshSize = String()
        self._meshMaterial = String()
        self._params_id = String()
        self._rawDir = String()
        self._pngDir = String()

        
    def setGridId(self, id):
        self._grid_id.set(id)
    def setPosition(self, position):
        self._position.set(position)
    def setName(self, name):
        self._name.set(name)
    def setHoleAngle(self, holeAngle):
        self._hole_angle.set(holeAngle)
    def setMeshAngle(self, mesh_angle):
        self._mesh_angle.set(mesh_angle)
    def setQuality(self, Quality):
        self._quality.set(Quality)
    def setNotes(self, Notes):
        self._notes.set(Notes)
    def setStatus(self, Status):
        self._status.set(Status)
    def setStartTime(self, StartTime):
        self._start_time.set(StartTime)
    def setLastUpdate(self, LastUpdate):
        self._last_update.set(LastUpdate)
    def setSessionId(self, SessionId):
        self._session_id.set(SessionId)
    def setHoleType(self, HoleType):
        self._holeType.set(HoleType)
    def setMeshSize(self, MeshSize):
        self._meshSize.set(MeshSize)
    def setMeshMaterial(self, MeshMaterial):
        self._meshMaterial.set(MeshMaterial)
    def setParamsId(self, ParamsId):
        self._params_id.set(ParamsId)

    def setRawDir(self, dataPath, sessionDir):
        gridRelativePath = str(self._position) + '_' + str(self._name)
        self._rawDir.set(os.path.join(str(dataPath),
                                    str(sessionDir),
                                    gridRelativePath,
                                    'raw'))
    def setPNGDir(self, dataPath, sessionDir):
        gridRelativePath = str(self._position) + '_' + str(self._name)
        self._pngDir.set(os.path.join(str(dataPath),
                                    str(sessionDir),
                                    gridRelativePath,
                                    'pngs'))

    def getGridId(self):
        return self._grid_id.get()
    def getPosition(self):
        return self._position.get()
    def getName(self):
        return self._name.get()
    def getHoleAngle(self):
        return self._hole_angle.get()
    def getMeshAngle(self):
        return self._mesh_angle.get()
    def getQuality(self):
        return self._quality.get()
    def getNotes(self):
        return self._notes.get()
    def getStatus(self):
        return self._status.get()
    def getStartTime(self):
        return self._start_time.get()
    def getLastUpdate(self):
        return self._last_update.get()
    def getSessionId(self):
        return self._session_id.get()
    def getHoleType(self):
        return self._holeType.get()
    def getMeshSize(self):
        return self._meshSize.get()
    def getMeshMaterial(self):
        return self._meshMaterial.get()
    def getParamsId(self):
        return self._params_id.get()

    def getRawDir(self):
        return self._rawDir
    def getPngDir(self):
        return self._pngDir

class Atlas(Image):
    """Atlas low magnification information"""

    def __init__(self,  **kwargs):
        Image.__init__(self, location=None, **kwargs)
        self._atlas_id = String()
        self._atlas_name = String()
        self._filename = String()
        self._pngDir = String()
        self._binning_factor = Integer()
        self._shape_x = Integer()
        self._shape_y = Integer()
        self._shape_z = Float()
        self._status = String()
        self._completion_time = String()
        self._grid_id = String()
        # MAYBE we need it-------
        # self._mdoc = String()
        # self._magnification = Integer()
        # self._voltage = Float()
        # --------------------

    def setAtlasId(self, id):
        self._atlas_id.set(id)

    def setAtlasName(self, name):
        self._atlas_name.set(name)

    def setFileName(self, filename):
        self._filename.set(filename)

    def setPngDir(self, pngDir):
        self._pngDir.set(pngDir)

    def setBinningFactor(self, factor):
        self._binning_factor.set(factor)

    def setShapeX(self, xDim):
        self._shape_x.set(xDim)

    def setShapeY(self, yDim):
        self._shape_y.set(yDim)

    def setShapeZ(self, shapeZ):
        self._shape_z.set(shapeZ)

    def setStatus(self, status):
        self._status.set(status)

    def setCompletionTime(self, time):
        self._completion_time.set(time)

    def setGridId(self, id):
        self._grid_id.set(id)

    # def setmDoc(self, filename):
    #     """ Use the _objValue attribute to store filename. """
    #     self._mdoc.set(filename)

    # def setMagnification(self, _magnification):
    #     self._magnification = float(_magnification)
    #
    # def setVoltage(self, _voltage):
    #     self._voltage = float(_voltage)

    def getAtlasId(self):
        return self._atlas_id.get()

    def getAtlasName(self):
        return self._atlas_name.get()

    def getFileName(self):
        return self._filename.get()

    def getPngDir(self):
        return self._pngDir.get()

    def getBinningFactor(self):
        return self._binning_factor.get()

    def getShapeX(self):
        return self._shape_x.get()

    def getShapeY(self):
        return self._shape_y.get()

    def getShapeZ(self):
        return self._shape_z.get()

    def getStatus(self):
        return self._status.get()

    def getCompletionTime(self):
        return self._completion_time.get()

    def getGridId(self):
        return self._grid_id.get()

    # def getmDoc(self):
    #     return self._mdoc.get()
    #
    # def getVoltage(self):
    #     return self._voltage.get()
    #
    # def getMagnification(self):
    #     return self._magnification

class Square(Image):
    """ Represents an EM Square object """

    def __init__(self, location=None, **kwargs):
        Image.__init__(self, location, **kwargs)
        self._square_id = String()
        self._has_queued = Boolean()
        self._has_completed = Boolean()
        self._has_active = Boolean()
        self._name = String()
        self._number = Integer()
        self._filename = String()
        self._pngDir = String()

        self._shape_x = Integer()
        self._shape_y = Integer()
        self._selected = Boolean()
        self._status = String()
        self._completion_time = String()
        self._area = Float()
        self._grid_id = String()
        self._atlas_id = String()
        # DETAILED
        self._finder_name = String()
        self._stage_x = Float()
        self._stage_y = Float()
        self._stage_z = Float()
        self._content_type = Integer()
        self._selector_name = String()
        self._selector_label = String()
        self._classifier_name = String()
        self._classifier_label = String()

    # Setters

    def setSquareId(self, id):
        self._square_id.set(id)

    def setHasQueued(self, queued):
        self._has_queued.set(queued)

    def setHasCompleted(self, completed):
        self._has_completed.set(completed)

    def setHasActive(self, active):
        self._has_active.set(active)

    def setName(self, name):
        self._name.set(name)

    def setNumber(self, number):
        self._number.set(number)

    def setFileName(self, filename):
        self._filename.set(filename)

    def setPngDir(self, pngDir):
        self._pngDir.set(pngDir)


    def setShapeX(self, xDim):
        self._shape_x.set(xDim)

    def setShapeY(self, yDim):
        self._shape_y.set(yDim)

    def setSelected(self, selected):
        self._selected.set(selected)

    def setStatus(self, status):
        self._status.set(status)

    def setCompletionTime(self, time):
        self._completion_time.set(time)

    def setArea(self, area):
        self._area.set(area)

    def setGridId(self, id):
        self._grid_id.set(id)

    def setAtlasId(self, id):
        self._atlas_id.set(id)

    # DETAILED
    def setFinderName(self, finder):
        self._finder_name.set(finder)

    def setStageX(self, stageX):
        self._stage_x.set(stageX)

    def setStageY(self, stageY):
        self._stage_y.set(stageY)

    def setStageZ(self, stageZ):
        self._stage_z.set(stageZ)

    def setContentType(self, ctype):
        self._content_type.set(ctype)

    def setSelectorName(self, name):
        self._selector_name.set(name)

    def setSelectorLabel(self, label):
        self._selector_label.set(label)

    def setClassifierName(self, name):
        self._classifier_name.set(name)

    def setClassifierLabel(self, label):
        self._classifier_label.set(label)

    # Getters

    def getSquareId(self):
        return self._square_id.get()

    def getHasQueued(self):
        return self._has_queued.get()

    def getHasCompleted(self):
        return self._has_completed.get()

    def getHasActive(self):
        return self._has_active.get()

    def getName(self):
        return self._name.get()

    def getFileName(self):
        return self._filename.get()

    def getPngDir(self):
        return self._pngDir.get()

    def getNumber(self):
        return self._number.get()


    def getShapeX(self):
        return self._shape_x.get()

    def getShapeY(self):
        return self._shape_y.get()

    def getSelected(self):
        return self._selected.get()

    def getStatus(self):
        return self._status.get()

    def getCompletionTime(self):
        return self._completion_time.get()

    def getArea(self):
        return self._area.get()

    def getGridId(self):
        return self._grid_id.get()

    def getAtlasId(self):
        return self._atlas_id.get()

    # DETAILED
    def getFinderName(self):
        return self._finder_name.get()

    def getStageX(self):
        return self._stage_x.get()

    def getStageY(self):
        return self._stage_y.get()

    def getStageZ(self):
        return self._stage_z.get()

    def getContentType(self):
        return self._content_type.get()

    def getSelectorName(self):
        return self._selector_name.get()

    def getSelectorLabel(self):
        return self._selector_label.get()

    def getClassifierName(self):
        return self._classifier_name.get()

    def getClassifierLabel(self):
        return self._classifier_label.get()

class Hole(Image):
    """ Represents an EM Hole object """

    def __init__(self, location=None, **kwargs):
        Image.__init__(self, location, **kwargs)
        self._hole_id = String()
        self._name = String()
        self._number = Integer()
        self._pngDir = String()
        self._shape_x = Integer()
        self._shape_y = Integer()
        self._selected = Boolean()
        self._status = String()
        self._completion_time = String()
        self._radius = Integer()
        self._area = Float()
        self._bis_group = String()
        self._bis_type = String()
        self._grid_id = String()
        self._square_id = String()
        # DETAILED
        self._finder_name = String()
        self._x = Integer()
        self._y = Integer()
        self._stage_x = Float()
        self._stage_y = Float()
        self._stage_z = Float()
        self._content_type = Integer()
        self._selector_name = String()
        self._selector_label = String()
        self._selector_value = Float()
        self._classifier_name = String()
        self._classifier_label = String()
        #QUALITY
        self._goodParticles = Integer(0)
        self._badParticles = Integer(0)

    # Setters

    def setHoleId(self, id):
        self._hole_id.set(id)

    def setName(self, name):
        self._name.set(name)

    def setNumber(self, number):
        self._number.set(number)

    def setPngDir(self, pngDir):
        self._pngDir.set(pngDir)


    def setShapeX(self, xDim):
        self._shape_x.set(xDim)

    def setShapeY(self, yDim):
        self._shape_y.set(yDim)

    def setSelected(self, selected):
        self._selected.set(selected)

    def setStatus(self, status):
        self._status.set(status)

    def setCompletionTime(self, time):
        self._completion_time.set(time)

    def setArea(self, area):
        self._area.set(area)

    def setRadius(self, radius):
        self._radius.set(radius)

    def setBisGroup(self, group):
        self._bis_group.set(group)

    def setBisType(self, typed):
        self._bis_type.set(typed)

    def setGridId(self, id):
        self._grid_id.set(id)

    def setSquareId(self, id):
        self._square_id.set(id)

    # DETAILED
    def setFinderName(self, finder):
        self._finder_name.set(finder)

    def setX(self, x):
        self._x.set(x)

    def setY(self, y):
        self._y.set(y)

    def setStageX(self, stageX):
        self._stage_x.set(stageX)

    def setStageY(self, stageY):
        self._stage_y.set(stageY)

    def setStageZ(self, stageZ):
        self._stage_z.set(stageZ)

    def setContentType(self, ctype):
        self._content_type.set(ctype)

    def setSelectorName(self, name):
        self._selector_name.set(name)

    def setSelectorLabel(self, label):
        self._selector_label.set(label)

    def setSelectorValue(self, value):
        self._selector_value.set(value)

    def setClassifierName(self, name):
        self._classifier_name.set(name)

    def setClassifierLabel(self, label):
        self._classifier_label.set(label)

    def setGoodParticles(self, value):
        self._goodParticles.set(value)

    def setBadParticles(self, value):
        self._badParticles.set(value)



    # Getters

    def getHoleId(self):
        return self._hole_id.get()

    def getName(self):
        return self._name.get()

    def getPngDir(self):
        return self._pngDir.get()

    def getNumber(self):
        return self._number.get()


    def getShapeX(self):
        return self._shape_x.get()

    def getShapeY(self):
        return self._shape_y.get()

    def getSelected(self):
        return self._selected.get()

    def getStatus(self):
        return self._status.get()

    def getCompletionTime(self):
        return self._completion_time.get()

    def getRadius(self):
        return self._radius.get()

    def getArea(self):
        return self._area.get()

    def getBisGroup(self):
        return self._bis_group.get()

    def getBisType(self):
        return self._bis_type.get()

    def getGridId(self):
        return self._grid_id.get()

    def getSquareId(self):
        return self._square_id.get()

    # DETAILED
    def getFinderName(self):
        return self._finder_name.get()

    def getX(self):
        return self._x.get()

    def getY(self):
        return self._y.get()

    def getStageX(self):
        return self._stage_x.get()

    def getStageY(self):
        return self._stage_y.get()

    def getStageZ(self):
        return self._stage_z.get()

    def getContentType(self):
        return self._content_type.get()

    def getSelectorName(self):
        return self._selector_name.get()

    def getSelectorLabel(self):
        return self._selector_label.get()

    def getSelectorValue(self):
        return self._selector_value.get()

    def getClassifierName(self):
        return self._classifier_name.get()

    def getClassifierLabel(self):
        return self._classifier_label.get()

    def getBadParticles(self):
        return self._badParticles

    def getGoodParticles(self):
        return self._goodParticles

class MovieSS(Movie):
    """ Represents an EM Movie object """
    def __init__(self, location=None, **kwargs):
        Movie.__init__(self, location, **kwargs)
        self._hm_id = String()
        self._png_path = String()
        self._png_url = String()
        self._ctf_img = String()
        self._name = String()
        self._number = Integer()
        self._shape_x = Integer()
        self._shape_y = Integer()
        self._selected = String()
        self._status = String()
        self._is_x = Float()
        self._is_y = Float()
        self._offset = Float()
        self._frames = String()
        self._defocus = Float()
        self._astig = Float()
        self._angast = Float()
        self._ctffit = Float()
        self._completion_time = String()
        self._hole_id = String()
        self._grid_id = String()


    # Setters
    def setHmId(self, id):
        self._hm_id.set(id)

    def setPngPath(self, path):
        self._png_path.set(path)

    def setPngUrl(self, url):
        self._png_url.set(url)

    def setCtfImg(self, ctf):
        self._ctf_img.set(ctf)

    def setName(self, name):
        self._name.set(name)

    def setNumber(self, number):
        self._number.set(number)


    def setShapeX(self, xDim):
        self._shape_x.set(xDim)

    def setShapeY(self, yDim):
        self._shape_y.set(yDim)

    def setSelected(self, selected):
        self._status.set(selected)

    def setStatus(self, status):
        self._status.set(status)

    def setIsX(self, x):
        self._is_x.set(x)

    def setIsY(self, y):
        self._is_y.set(y)

    def setOffset(self, offset):
        self._offset.set(offset)

    def setFrames(self, frames):
        self._frames.set(frames)

    def setDefocus(self, defocus):
        self._defocus.set(defocus)

    def setAstig(self, astig):
        self._astig.set(astig)

    def setAngast(self, angast):
        self._angast.set(angast)

    def setCtffit(self, fit):
        self._ctffit.set(fit)

    def setCompletionTime(self, time):
        self._completion_time.set(time)

    def setHoleId(self, id):
        self._hole_id.set(id)

    def setGridId(self, id):
        self._grid_id.set(id)


    # Getter
    def getHmId(self):
        return self._hm_id.get()

    def getPngPath(self):
        return self._png_path.get()

    def getPngUrl(self):
        return self._png_url.get()

    def getCtfImg(self):
        return self._ctf_img.get()

    def getName(self):
        return self._name.get()

    def getNumber(self):
        return self._number.get()

    def getShapeX(self):
        return self._shape_x.get()

    def getShapeY(self):
        return self._shape_y.get()

    def getStatus(self):
        return self._status.get()
    def getSelected(self):
        return self._selected.get()

    def getIsX(self):
        return self._is_x.get()

    def getIsY(self):
        return self._is_y.get()

    def getOffset(self):
        return self._offset.get()

    def getFrames(self):
        return self._frames.get()

    def getDefocus(self):
        return self._defocus.get()

    def getAstig(self):
        return self._astig.get()

    def getAngast(self):
        return self._angast.get()

    def getCtffit(self):
        return self._ctffit.get()

    def getCompletionTime(self):
        return self._completion_time.get()

    def getHoleId(self):
        return self._hole_id.get()

    def getGridId(self):
        return self._grid_id.get()


# -------SETS------------
class SetOfGrids(EMSet):
    ITEM_TYPE = Grid
    def __init__(self,  **kwargs):
        EMSet.__init__(self,  **kwargs)

class SetOfAtlas(EMSet):
    ITEM_TYPE = Atlas
    def __init__(self,  **kwargs):
        EMSet.__init__(self,  **kwargs)
        self._filename = String()


class SetOfSquares(EMSet):
    ITEM_TYPE = Square

    def __init__(self,  **kwargs):
        EMSet.__init__(self,  **kwargs)


class SetOfHoles(EMSet):
    ITEM_TYPE = Hole

    def __init__(self,  **kwargs):
        EMSet.__init__(self,  **kwargs)


class SetOfMoviesSS(SetOfMovies):
    ITEM_TYPE = MovieSS

    def __init__(self,  **kwargs):
        SetOfMovies.__init__(self,  **kwargs)

