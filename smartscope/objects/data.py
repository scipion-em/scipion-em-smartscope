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
from pwem.objects import EMObject, Image, EMSet, Pointer
from pyworkflow.object import (Float, String, List, Integer, CsvList, Boolean)


## TODO: there is information of the .mdoc of all kinds of data (atlas, squares, holes and high mag) provided by SmartScope that could be useful

# -------ATLAS------------
class Atlas(Image):
    """Atlas low magnification information"""

    def __init__(self,  **kwargs):
        Image.__init__(self, location=None, **kwargs)
        self._atlas_id = String()
        self._atlas_name = String()
        self._filename = String()  # Where is the .PNG?
        self._pixel_size = Float()
        self._binning_factor = Integer()
        self._shape_x = Integer()
        self._shape_y = Integer()
        self._stage_z = Float()
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

    def setPixelSize(self, pixelSpacing):
        self._pixel_size.set(pixelSpacing)

    def setBinningFactor(self, factor):
        self._binning_factor.set(factor)

    def setShapeX(self, xDim):
        self._shape_x.set(xDim)

    def setShapeY(self, yDim):
        self._shape_y.set(yDim)

    def setStageZ(self, stageZ):
        self._stage_z.set(stageZ)

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

    def getPixelSize(self):
        return self._pixel_size.get()

    def getBinningFactor(self):
        return self._binning_factor.get()

    def getShapeX(self):
        return self._shape_x.get()

    def getShapeY(self):
        return self._shape_y.get()

    def getStageZ(self):
        return self._stage_z.get()

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
        self._filename = String()  # Where is the .PNG?
        self._pixel_size = Float()
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

    def setPixelSize(self, pixelSpacing):
        self._pixel_size.set(pixelSpacing)

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

    def getNumber(self):
        return self._number.get()

    def getPixelSize(self):
        return self._pixel_size.get()

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
    """ Represents an EM Square object """

    def __init__(self, location=None, **kwargs):
        Image.__init__(self, location, **kwargs)
        self._hole_id = String()
        self._name = String()
        self._number = Integer()
        self._filename = String()  # Where is the .PNG?
        self._pixel_size = Float()
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
        self._classifier_name = String()
        self._classifier_label = String()

    # Setters

    def setHoleId(self, id):
        self._hole_id.set(id)

    def setName(self, name):
        self._name.set(name)

    def setNumber(self, number):
        self._number.set(number)

    def setFileName(self, filename):
        self._filename.set(filename)

    def setPixelSize(self, pixelSpacing):
        self._pixel_size.set(pixelSpacing)

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

    def setClassifierName(self, name):
        self._classifier_name.set(name)

    def setClassifierLabel(self, label):
        self._classifier_label.set(label)

    # Getters

    def getHoleId(self):
        return self._square_id.get()

    def getName(self):
        return self._name.get()

    def getFileName(self):
        return self._filename.get()

    def getNumber(self):
        return self._number.get()

    def getPixelSize(self):
        return self._pixel_size.get()

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

    def getClassifierName(self):
        return self._classifier_name.get()

    def getClassifierLabel(self):
        return self._classifier_label.get()


# -------SETS------------
class SetOfAtlas(EMSet):
    ITEM_TYPE = Atlas
    def __init__(self,  **kwargs):
        EMSet.__init__(self,  **kwargs)
        self._pixel_size = Float()
        # MAYBE we need it-------
        # self._magnification = Float()
        # self._voltage = Float()

    # def setMagnification(self, _magnification):
    #     self._magnification = float(_magnification)
    #
    # def setVoltage(self, _voltage):
    #     self._voltage = float(_voltage)

    def setPixelSize(self, pixelSize):
        self._pixel_size = Float(pixelSize)

    # def getVoltage(self):
    #     return self._voltage.get()
    #
    # def getMagnification(self):
    #     return self._magnification

    def getPixelSize(self):
        return self._pixel_size.get()


class SetOfSquares(EMSet):
    ITEM_TYPE = Square

    def __init__(self,  **kwargs):
        EMSet.__init__(self,  **kwargs)
        self._pixel_size = Float()
        # MAYBE we need it-------
        # self._magnification = Float()
        # self._voltage = Float()

    # def setMagnification(self, _magnification):
    #     self._magnification = float(_magnification)
    #
    # def setVoltage(self, _voltage):
    #     self._voltage = float(_voltage)

    def setPixelSize(self, pixelSize):
        self._pixel_size = Float(pixelSize)

    # def getVoltage(self):
    #     return self._voltage.get()
    #
    # def getMagnification(self):
    #     return self._magnification

    def getPixelSize(self):
        return self._pixel_size.get()


class SetOfHoles(EMSet):
    ITEM_TYPE = Hole

    def __init__(self,  **kwargs):
        EMSet.__init__(self,  **kwargs)
        self._pixel_size = Float()


    def setPixelSize(self, pixelSize):
        self._pixel_size = Float(pixelSize)

    def getPixelSize(self):
        return self._pixel_size.get()
