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
import os.path

from ..objects.data import *
from ..pyclient.basic import *
from pwem.objects.data import Acquisition
import time

class dataCollection():
    def __init__(self, pyClient):
        self.pyClient = pyClient

    def sessionCollection(self):
        sessionList = []
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
        return sessionList

    def sessionOpen(self):
        grid = self.pyClient.getDetailsFromParameter('grids', status='started', sortByLast=True, dev=True)
        for g in grid:
            if g['status'] == 'started':
                return g['session_id']
    def metadataCollection(self, microscopeList, detectorList, sessionList, acquisition):
        microscopes = self.pyClient.getDetailsFromParameter('microscopes')
        for m in microscopes:
            micro = Microscope()
            micro.setMicroscopeId(m['microscope_id'])
            micro.setName(m['name'])
            micro.setLocation(m['location'])
            micro.setVoltage(m['voltage'])
            micro.setSphericalabberation(m['spherical_abberation'])
            micro.setVendor(m['vendor'])
            micro.setLoaderSize(m['loader_size'])
            micro.setWorkerHostname(m['worker_hostname'])
            micro.setExecutable(m['executable'])
            micro.setSerialemIP(m['serialem_IP'])
            micro.setSerialemPORT(m['serialem_PORT'])
            micro.setWindowsPath(m['windows_path'])
            micro.setScopePath(m['scope_path'])

            microscopeList.append(micro)
            acquisition.setVoltage(micro.getVoltage())
            acquisition.setSphericalAberration(micro.getSphericalabberation())


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



    def screeningCollection(self, dataPath, sessionId, sessionName, setOfGrids, setOfAtlas,
                            setOfSquares, setOfHoles):
        print('sessionName: {}'.format(sessionName))
        grid = self.pyClient.getRouteFromID('grids', 'session', sessionId, dev=False)
        if grid != []:print('Number grid in the sesison: {}'.format(len(grid)))
        objId = len(setOfGrids)
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
            gr.setRawDir(dataPath, self.sessionWorkingDir(sessionName))
            gr.setPNGDir(dataPath, self.sessionWorkingDir(sessionName))
            gr.setObjId(objId)
            objId += 1
            setOfGrids.append(gr)


            startAtlas = time.time()
            atlas = self.pyClient.getRouteFromID('atlas', 'grid', gr.getGridId())
            print('request Atlas time: {}s'.format(time.time() - startAtlas))
            if atlas != []: print(
                '\tNumber atlas in the grid{}: {}'.format(gr.getName(), len(atlas)))
            for a in atlas:
                at = Atlas()
                at.setAtlasId(a['atlas_id'])
                at.setAtlasName(a['name'])
                at.setSamplingRate(a['pixel_size'])
                if a['binning_factor'] == None:
                    at.setBinningFactor(1)
                else:
                    at.setBinningFactor(a['binning_factor'])
                at.setShapeX(a['shape_x'])
                at.setShapeY(a['shape_y'])
                at.setShapeZ(a['stage_z'])
                at.setStatus(a['status'])
                at.setCompletionTime(a['completion_time'])
                at.setGridId(a['grid_id'])
                # at.setFileName(os.path.join(str(gr.getRawDir()),
                #                             str(at.getAtlasName() + '.mrc')))
                at.setPngDir(os.path.join(str(gr.getPngDir()),
                                          str(at.getAtlasName() + '.png')))
                at.setFileName(os.path.join(str(gr.getPngDir()),
                                          str(at.getAtlasName() + '.png')))
                print('Atlas filename: {}'.format(at.getFileName()))
                setOfAtlas.append(at)
                setOfAtlas.update(at)
                setOfAtlas.write()

                startSquares = time.time()
                squares = self.pyClient.getRouteFromID('squares', 'atlas', at.getAtlasId())
                print('request Atlas time: {}s'.format(
                    time.time() - startSquares))

                if squares != []: print(
                    '\t\tNumber squares in the atlas: {}'.format(len(squares)))

                for s in squares:
                    sq = Square()
                    sq.setSquareId(s['square_id'])
                    sq.setName(s['name'])
                    sq.setNumber(s['number'])
                    sq.setSamplingRate(s['pixel_size'])
                    sq.setShapeX(s['shape_x'])
                    sq.setShapeY(s['shape_y'])
                    sq.setSelected(s['selected'])
                    sq.setStatus(s['status'])
                    sq.setCompletionTime(s['completion_time'])
                    sq.setArea(s['area'])
                    sq.setGridId(s['grid_id'])
                    sq.setAtlasId(s['atlas_id'])
                    sq.setFileName(os.path.join(str(gr.getRawDir()),
                                                str(sq.getName() + '.mrc')))
                    sq.setPngDir(os.path.join(str(gr.getPngDir()),
                                              str(sq.getName() + '.png')))

                    setOfSquares.append(sq)
                    setOfSquares.update(sq)
                    setOfSquares.write()

                    holes = self.pyClient.getRouteFromID('holes', 'square', sq.getSquareId(), endpoint='scipion_plugin')
                    if holes != []:
                        #print('square name: {}'.format(sq.getName()))
                        print('\t\t\tNumber holes in the square{}: {}'.format(
                            sq.getName(), len(holes)))

                    for h in holes:
                        ho = Hole()
                        ho.setHoleId(h['hole_id'])
                        ho.setName(h['name'])
                        ho.setNumber(h['number'])
                        ho.setSamplingRate(h['pixel_size'])
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
                        fileName = os.path.join(str(gr.getRawDir()),
                                                str(ho.getName() + '.mrc'))
                        ho.setFileName(fileName)
                        ho.setPngDir(os.path.join(str(gr.getPngDir()),
                                                  str(ho.getName() + '.png')))
                        #holeDetail = self.pyClient.getDetailFromItem('holes', h['hole_id'])
                        finder = h['finders'][0]
                        ho.setFinderName(finder['method_name'])
                        selectors = h['selectors'][0]
                        ho.setSelectorName(selectors['method_name'])
                        ho.setSelectorLabel(selectors['label'])
                        ho.setSelectorValue(selectors['value'])

                        #hm = self.pyClient.getRouteFromID('highmag', 'hole', h['hole_id'], detailed=False)#could be several hm for one hole

                        setOfHoles.append(ho)
                        setOfHoles.update(ho)
                        setOfHoles.write()

    def windowsPath(self, sessionId):
        session = self.pyClient.getRouteFromID('sessions', 'session', sessionId)
        microscopeId = session[0]['microscope_id']
        microscope = self.pyClient.getRouteFromID('microscopes', 'microscope', microscopeId)
        return microscope[0]['windows_path']


    def sessionWorkingDir(self, sessionName):
        session = self.pyClient.getRouteFromName('sessions', 'session', sessionName)
        return session[0]['working_dir']

    def getMdocFile(self, grid, highMagID):
        highMag = self.pyClient.getRouteFromID('highmag', 'hm', highMagID)
        mdocFile = os.path.join(str(grid.getRawDir()),
                                str(highMag[0]['name'] + '.mrc.mdoc'))
        if os.path.isfile(mdocFile):
            return MDoc(mdocFile)
        else:
            print('HM {} not adquired'.format(mdocFile))
            return False

    def getMagnification(self, grid, highMagID):
        mdoc = self.getMdocFile(grid, highMagID)
        if mdoc != False:
            hDict, valueList = mdoc.parseMdoc()
            return valueList[0]['Magnification']

    def getDoseRate(self, grid, highMagID):
        mdoc = self.getMdocFile(grid, highMagID)
        if mdoc != False:
            hDict, valueList = mdoc.parseMdoc()
            return valueList[0]['DoseRate']

    def getFramesNumber(self, grid, highMagID):
        mdoc = self.getMdocFile(grid, highMagID)
        if mdoc != False:
            hDict, valueList = mdoc.parseMdoc()
            return valueList[0]['NumSubFrames']

    def getSubFramePath(self, grid, highMagID):
        mdoc = self.getMdocFile(grid, highMagID)
        if mdoc != False:
            hDict, valueList = mdoc.parseMdoc()
            return valueList[0]['SubFramePath']
        else:
            return False



class MDoc:
    """class define mdoc files from SerialEM
    This format consists of keyword-value pairs organized into blocks
    called sections.
    A section begins with a bracketed key-value pair:
      [sectionType = name]
    where the section "name" or value will typically be unique.
    Lines below a section header of the form
      key = value
    provide data associated with that section.

    In addition, key-value pairs can occur at the beginning of the file,
    before any section header, and these are referred to as global values.
    Files with extension ".mdoc" provides data about an MRC file and has
    the same name as the image file, with the additional extension ".mdoc".
    In these files, the main section type is "ZValue" and the name
    for each section is the Z value of the image in the file, numbered from 0.
    A description of each key is available at URL:
    https://bio3d.colorado.edu/SerialEM/hlp/html/about_formats.htm

    Additional information may be stored in section headers of the type "T"
    (i.e. [T  a = b ]). In theory these information in also stored in the
    "titles" of the MRC files.
    """

    def __init__(self, fileName):
        self._mdocFileName = str(fileName)

    def createDictTem(self):
            return {
                'zvalue': None,
                'PieceCoordinates': None,
                'MinMaxMean': None,
                'TiltAngle': None,
                'StagePosition': None,
                'StageZ': None,
                'Magnification': None,
                'Intensity': None,
                'ExposureDose': None,
                'DoseRate': None,
                'PixelSpacing': None,
                'SpotSize': None,
                'Defocus': None,
                'ImageShift': None,
                'RotationAngle': None,
                'ExposureTime': None,
                'Binning': None,
                'CameraIndex': None,
                'DividedBy2': None,
                'OperatingMode': None,
                'UsingCDS': None,
                'MagIndex': None,
                'LowDoseConSet': None,
                'CountsPerElectron': None,
                'TargetDefocus': None,
                'DateTime': None,
                'FilterSlitAndLoss': None,
                'UncroppedSize': None,
                'RotationAndFlip': None,
                'AlignedPieceCoords': None,
                'XedgeDxy': None,
                'YedgeDxy': None}

    def parseMdoc(self):
        """
        Parse the mdoc file and return a list with a dict key=value for each
        of the [Zvalue = X] sections and a dictionary for the first lines
        global variables.

        :return: dictionary (header), list of dictionaries (Z slices)
        """
        headerDict = {}
        headerParsed = False
        zvalueList = []  # list of dictionaries with
        with open(self._mdocFileName) as f:
            for line in f:
                if line.startswith('[T'):  # auxiliary global information
                    strLine = line.strip().replace(' ', '').\
                                           replace(',', '').lower()
                    headerDict['auxiliary'] = strLine
                elif line.startswith('[ZValue'):  # each tilt movie
                    # We have found a new z value
                    headerParsed = True
                    zvalue = int(line.split(']')[0].split('=')[1])
                    if zvalue != len(zvalueList):
                        raise Exception("Unexpected ZValue = %d" % zvalue)
                    zvalueDict = self.createDictTem()
                    zvalueDict['zvalue'] = str(zvalue)
                    zvalueList.append(zvalueDict)

                elif line.strip():  # global variables no in [T sections]
                    key, value = line.split('=')
                    if not headerParsed:
                        headerDict[key.strip()] = value.strip()
                    if zvalueList:
                        zvalueDict[key.strip()] = value.strip()
                        #print('zvalue: {} key.strip(): {}'.format(zvalue, key.strip()))
                        #print('zvalueDict[key.strip()] {}'.format(zvalueDict[key.strip()]))

        # print(len(zvalueList))
        # print(zvalueDict)

        return headerDict, zvalueList

