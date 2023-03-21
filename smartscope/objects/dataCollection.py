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
            micro.setLoaderSize(m['loader_size'])
            micro.setWorkerHostname(m['worker_hostname'])
            micro.setExecutable(m['executable'])
            micro.setSerialemIP(m['serialem_IP'])
            micro.setSerialemPORT(m['serialem_PORT'])
            micro.setWindowsPath(m['windows_path'])
            micro.setScopePath(m['scope_path'])

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


    def screeningCollection(self, dataPath, sessionId, sessionName, setOfGrids, setOfAtlas,
                            setOfSquares, setOfHoles, setOfMoviesSS):
        print('sessionName: {}'.format(sessionName))
        grid = self.pyClient.getRouteFromID('grids', 'session', sessionId)
        if grid != []:print('Number grid in the sesison: {}'.format(len(grid)))
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
            setOfGrids.append(gr)

            atlas = self.pyClient.getRouteFromID('atlas', 'grid', gr.getGridId())
            if atlas != []: print(
                '\tNmber atlas in the grid{}: {}'.format(gr.getName(), len(atlas)))

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
                at.setFileName(os.path.join(gr.getRawDir(),
                                            at.getAtlasName(),
                                            '.mrc'))
                at.setPngDir(os.path.join(str(gr.getPngDir()),
                                            at.getAtlasName(),
                                            '.png'))
                setOfAtlas.append(at)

                squares = self.pyClient.getRouteFromID('squares', 'atlas', at.getAtlasId())
                if squares != []: print(
                    '\t\tNumber squares in the atlas: {}'.format(len(squares)))

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
                    sq.setFileName(os.path.join(gr.getRawDir(),
                                                sq.getName(),
                                                '.mrc'))
                    sq.setPngDir(os.path.join(str(gr.getPngDir()),
                                              sq.getName(),
                                              '.png'))
                    setOfSquares.append(sq)
                    holes = self.pyClient.getRouteFromID('holes', 'square', sq.getSquareId())
                    if holes != []:
                        #print('square name: {}'.format(sq.getName()))
                        print('\t\t\tNumber holes in the square{}: {}'.format(
                            sq.getName(), len(holes)))

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
                        ho.setFileName(os.path.join(gr.getRawDir(),
                                                    ho.getName(),
                                                    '.mrc'))
                        ho.setPngDir(os.path.join(str(gr.getPngDir()),
                                                  ho.getName(),
                                                  '.png'))
                        setOfHoles.append(ho)
                        highMag = self.pyClient.getRouteFromID('highmag', 'hole', ho.getHoleId(), dev=False)
                        if highMag != []: print(
                            '\t\t\t\tNumber movies in the hole: {}'.format(len(highMag)))
                        # else: print('Empty Hole: {}'.format(ho.getName()))
                        for hm in highMag:
                            mSS = MovieSS()
                            mSS.setHmId(hm['hm_id'])
                            mSS.setName(hm['name'])
                            mSS.setNumber(hm['number'])
                            mSS.setPixelSize(hm['pixel_size'])
                            mSS.setShapeX(hm['shape_x'])
                            mSS.setShapeY(hm['shape_y'])
                            mSS.setSelected(hm['selected'])
                            mSS.setStatus(hm['status'])
                            mSS.setCompletionTime(hm['completion_time'])
                            mSS.setIsX(hm['is_x'])
                            mSS.setIsY(hm['is_y'])
                            mSS.setOffset(hm['offset'])
                            mSS.setFrames(hm['frames'])
                            mSS.setDefocus(hm['defocus'])
                            mSS.setAstig(hm['astig'])
                            mSS.setAngast(hm['angast'])
                            mSS.setCtffit(hm['ctffit'])
                            mSS.setGridId(hm['grid_id'])
                            mSS.setHoleId(hm['hole_id'])
                            mSS.setFileName(self.getSubFramePath(gr, mSS.getName()))
                            # la movie no esta en el raw, sino en la carpeta donde sreialEM escribe
                            setOfMoviesSS.append(mSS)


    def windowsPath(self, sessionId):
        session = self.pyClient.getRouteFromID('sessions', 'session', sessionId)
        microscopeId = session[0]['microscope_id']
        microscope = self.pyClient.getRouteFromID('microscopes', 'microscope', microscopeId)
        return microscope[0]['windows_path']


    def sessionWorkingDir(self, sessionName):
        session = self.pyClient.getRouteFromName('sessions', 'session', sessionName)
        return session[0]['working_dir']
    def getSubFramePath(self, grid, highMagID):
        highMag = self.pyClient.getRouteFromID('highmag', 'highmag',highMagID)
        mdocFile = os.path.join(grid.getRawDir(),
                                str(highMag[0]['name'] + '.mrc.mdoc'))
        mdoc = MDoc(mdocFile)
        hDict, valueList = mdoc.parseMdoc()
        return valueList[0]['SubFramePath']



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

