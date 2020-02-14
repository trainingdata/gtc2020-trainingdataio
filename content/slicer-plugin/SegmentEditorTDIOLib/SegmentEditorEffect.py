import json, logging, os, shutil, tempfile, time
from collections import OrderedDict
import SimpleITK as sitk, qt, sitkUtils, slicer, vtk
from SegmentEditorEffects import *
from TDIOClientAPI.client_api import TDIOClientAPI, TDIOUtils, printable
from TDIONvidiaAIAAClientAPI.client_api import AIAAClient
import numpy as np
import vtkSegmentationCorePython as vtkSegmentationCore

def getPointsFromPolygon(polygon):
    retvalpoints = []
    for handle in polygon['handles']:
        retvalpoints.append([handle['y'], handle['x']])
    return retvalpoints

class SegmentEditorEffect(AbstractScriptedSegmentEditorEffect):
    """'This effect allows edits on TrainingData.io Segmentation input volume'"""
    __module__ = __name__
    __qualname__ = 'SegmentEditorEffect'

    def __init__(self, scriptedEffect):
        print('SegmentEditorEffect::__init__()')
        scriptedEffect.name = 'TrainingData.io Segmentation'
        scriptedEffect.perSegment = False
        if slicer.app.majorVersion >= 5 or slicer.app.majorVersion >= 4 and slicer.app.minorVersion >= 11:
            scriptedEffect.requireSegments = False
        AbstractScriptedSegmentEditorEffect.__init__(self, scriptedEffect)
        self.models = OrderedDict()
        self.connectedToEditorForSegmentChange = False
        self.isActivated = False
        self.tdioConnection = None
        self.tdioConnection = TDIOServerConnection(cloud_server_url='https://app.trainingdata.io')
        self.nvidiaConnection = NvidiaClientAPI()
        self.observedSegmentation = None
        self.segmentationNodeObserverTags = []
        self.tdiodata = None

    def __del__(self):
        AbstractScriptedSegmentEditorEffect.__del__(self)
        if self.progressBar:
            self.progressBar.close()

    def clone(self):
        import qSlicerSegmentationsEditorEffectsPythonQt as effects
        clonedEffect = effects.qSlicerSegmentEditorScriptedEffect(None)
        clonedEffect.setPythonSource(__file__.replace('\\', '/'))
        return clonedEffect

    def icon(self, name='SegmentEditorEffect.png'):
        iconPath = os.path.join(os.path.dirname(__file__), name)
        if os.path.exists(iconPath):
            return qt.QIcon(iconPath)
        else:
            return qt.QIcon()

    def helpText(self):
        return 'TrainingData.io Segmentation'

    def setupOptionsFrame(self):
        print('setupOptionsFrame()')
        uiWidget = slicer.util.loadUI(os.path.join(os.path.dirname(__file__), 'SegmentEditorTDIO.ui'))
        self.scriptedEffect.addOptionsWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        self.ui.saveSegmentationButton.setIcon(self.icon('nvidia-icon.png'))
        self.ui.saveSegmentationButton.connect('clicked(bool)', self.onClickSaveSegmentation)

    def onClickSaveSegmentation(self):
        print('onClickSaveSegmentation()')
        self.tdiodata = slicer.trainingdataiodata
        pnode = self.scriptedEffect.parameterSetNode()
        masterVolumeNode = pnode.GetMasterVolumeNode()
        segmentationNode = pnode.GetSegmentationNode()
        # iterate over each
        segmentationids = vtk.vtkStringArray() 
        segmentationColors = vtk.vtkStringArray() 
        segmentationNode.GetSegmentation().GetSegmentIDs(segmentationids)
        numberofsegments = segmentationNode.GetSegmentation().GetNumberOfSegments()
        for i in range(0, numberofsegments):
            segmentationid = segmentationids.GetValue(i)
            tempsegmentationids = vtk.vtkStringArray()
            tempsegmentationids.InsertValue(0, segmentationid)
            labelmapVolumeNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
            slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, labelmapVolumeNode, masterVolumeNode)
            # labelmapVolumeNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode) #I tried with and without this line
            # slicer.modules.segmentations.logic().ExportSegmentsToLabelmapNode(segmentationNode, tempsegmentationids, labelmapVolumeNode)
            tmpFile = tempfile.NamedTemporaryFile(suffix=self.tdioConnection.inputFileExtension(), dir=self.tdioConnection.tmpdir).name
            slicer.util.saveNode(labelmapVolumeNode, tmpFile)
            print(segmentationid, tmpFile)
            polygons = self.nvidiaConnection.mask2polygon(tmpFile, 1)
            print(segmentationid, polygons)
            segmentationcolor = TDIOUtils.rgb_to_hex(segmentationNode.GetSegmentation().GetSegment(segmentationid).GetColor())
            cornerstoneannotation = self.tdioConnection.convertToCornerstoneAnnotations(self.tdiodata['authtoken'], self.tdiodata['projectjson']['images']['seriesList'][0], polygons, segmentationid, segmentationcolor, self.tdiodata['jobid'], self.tdiodata['useremail'])

    def activate(self):
        print('activate()')
        logging.debug('TrainingData.io Segmentation effect activated')
        self.isActivated = True
        self.scriptedEffect.showEffectCursorInSliceView = False
        self.observeSegmentation(True)

    def deactivate(self):
        logging.debug('TrainingData.io Segmentation effect deactivated')
        self.isActivated = False
        self.observeSegmentation(False)
        self.reset()

    def reset(self):
        print('reset()')

    def createCursor(self, widget):
        print('createCursor()')
        return slicer.util.mainWindow().cursor

    def observeSegmentation(self, observationEnabled):
        print('observeSegmentation()')
        segmentationNode = self.scriptedEffect.parameterSetNode().GetSegmentationNode()
        segmentation = segmentationNode.GetSegmentation() if segmentationNode else None
        if observationEnabled:
            if self.observedSegmentation == segmentation:
                return
        if not observationEnabled:
            if not self.observedSegmentation:
                return
        if self.observedSegmentation:
            for tag in self.segmentationNodeObserverTags:
                self.observedSegmentation.RemoveObserver(tag)

            self.segmentationNodeObserverTags = []
            self.observedSegmentation = None
        if observationEnabled:
            if segmentation is not None:
                self.observedSegmentation = segmentation
                observedEvents = [
                 slicer.vtkSegmentation.SegmentModified]
                for eventId in observedEvents:
                    self.segmentationNodeObserverTags.append(self.observedSegmentation.AddObserver(eventId, self.onSegmentationModified))

    def onSegmentationModified(self, caller, event):
        print('onSegmentationModified')

    def currentSegment(self):
        print('currentSegment()')
        pnode = self.scriptedEffect.parameterSetNode()
        segmentationNode = pnode.GetSegmentationNode()
        segmentation = segmentationNode.GetSegmentation() if segmentationNode else None
        if not pnode or not segmentation or not pnode.GetSelectedSegmentID():
            return
        else:
            return segmentation.GetSegment(pnode.GetSelectedSegmentID())

    def currentSegmentID(self):
        print('currentSegmentID')
        pnode = self.scriptedEffect.parameterSetNode()
        if pnode:
            return pnode.GetSelectedSegmentID()

    def updateSegmentationMask(self, extreme_points, in_file, modelInfo, overwriteCurrentSegment=False):
        print('updateSegmentationMask()')
        start = time.time()
        logging.debug('Update Segmentation Mask from: {}'.format(in_file))
        if in_file is None or os.path.exists(in_file) is False:
            return False
        else:
            segmentationNode = self.scriptedEffect.parameterSetNode().GetSegmentationNode()
            segmentation = segmentationNode.GetSegmentation()
            currentSegment = self.currentSegment()
            labelImage = sitk.ReadImage(in_file)
            labelmapVolumeNode = sitkUtils.PushVolumeToSlicer(labelImage, None, className='vtkMRMLLabelMapVolumeNode')
            numberOfExistingSegments = segmentation.GetNumberOfSegments()
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmapVolumeNode, segmentationNode)
            slicer.mrmlScene.RemoveNode(labelmapVolumeNode)
            modelLabels = modelInfo['labels']
            numberOfAddedSegments = segmentation.GetNumberOfSegments() - numberOfExistingSegments
            logging.debug('Adding {} segments'.format(numberOfAddedSegments))
            addedSegmentIds = [segmentation.GetNthSegmentID(numberOfExistingSegments + i) for i in range(numberOfAddedSegments)]
            for i, segmentId in enumerate(addedSegmentIds):
                segment = segmentation.GetSegment(segmentId)
                if i == 0:
                    if overwriteCurrentSegment:
                        if currentSegment:
                            logging.debug('Update current segment with id: {} => {}'.format(segmentId, segment.GetName()))
                            labelmap = slicer.vtkOrientedImageData()
                            segmentationNode.GetBinaryLabelmapRepresentation(segmentId, labelmap)
                            self.scriptedEffect.modifySelectedSegmentByLabelmap(labelmap, slicer.qSlicerSegmentEditorAbstractEffect.ModificationModeSet)
                            segmentationNode.RemoveSegment(segmentId)
                    logging.debug('Setting new segmentation with id: {} => {}'.format(segmentId, segment.GetName()))
                    if i < len(modelLabels):
                        segment.SetName(modelLabels[i])
                    else:
                        segment.SetName('unknown {}'.format(i))

            if extreme_points:
                logging.debug('Extreme Points: {}'.format(extreme_points))
                if overwriteCurrentSegment:
                    if currentSegment:
                        segment = currentSegment
                else:
                    segment = segmentation.GetNthSegment(numberOfExistingSegments)
                if segment:
                    segment.SetTag('AIAA.DExtr3DExtremePoints', json.dumps(extreme_points))
            os.unlink(in_file)
            logging.info('Time consumed by updateSegmentationMask: {0:3.1f}'.format(time.time() - start))
            return True

    def loadMasterVolume(self, mastervolumefilepath):
        print('loadMasterVolume():', mastervolumefilepath)
        masterVolumeName = os.path.basename(mastervolumefilepath).split('.')[0]
        masterVolume = slicer.util.getNode(masterVolumeName)
        self.tdiodata = slicer.trainingdataiodata
        # print(self.tdiodata)
        if self.tdiodata:
            try:
                self.cornerstoneannotationsToSlicerSegments(masterVolume, self.tdiodata['authtoken'], self.tdiodata['jobid'], self.tdiodata['projectjson'], self.tdiodata['useremail'])
            except Exception as ex:
                print(ex)
        return    

    def ijkToRas(self, ijkToRasMatrix, transformVolumeRasToRas, i, j, k):
        position_ijk = [i, j ,k, 1]
        point_VolumeRas = [0, 0, 0, 1]
        ijkToRasMatrix.MultiplyPoint(np.array(position_ijk), point_VolumeRas)
        # If volume node is transformed, apply that transform to get volume's RAS coordinates
        point_Ras = transformVolumeRasToRas.TransformPoint(point_VolumeRas[0:3])
        # print(point_Ras)
        return point_Ras
                    
    def cornerstoneannotationsToSlicerSegments(self, masterVolume, auth_token, jobid, projectjson, useremail):
        print('cornerstoneannotationsToSlicerSegments()', flush=True)
        # voxels = slicer.util.arrayFromVolume(masterVolume)
        ijkToRasMatrix = vtk.vtkMatrix4x4()
        masterVolume.GetIJKToRASMatrix(ijkToRasMatrix)
        imageData = masterVolume.GetImageData()
        transformVolumeRasToRas = vtk.vtkGeneralTransform()
        slicer.vtkMRMLTransformNode.GetTransformBetweenNodes(masterVolume.GetParentTransformNode(), None, transformVolumeRasToRas)
        tdioClientAPI = TDIOClientAPI()
        instanceindex = -1
        contoursmap = {}
        colorsmap = {}
        segmentsmap = {}
        
        seriesjson = projectjson['images']['seriesList'][0]
        for instance in seriesjson['instanceList']:
            instanceindex = instanceindex + 1
            instanceid = instance['instanceId']
            response = tdioClientAPI.getcornerstoneannotation('https://app.trainingdata.io', auth_token, jobid, seriesjson['seriesId'], instanceid, useremail)
            cannotations = []
            cannotations = response
            if len(cannotations) == 0:
                continue
            jsonobj = json.loads(cannotations[0]['jsonstring'])
            annotations = jsonobj['annotations']
            print('instanceid1', instanceid, len(annotations))
            for annotation in annotations:
                # print(annotation)
                toolData = annotation['toolData']
                toolType = annotation['toolName']
                color = annotation['selectedColor']
                color = TDIOUtils.hex_to_rgb(annotation['selectedColor'])
                aclass = annotation['annotationClass']
                label = ''.join(filter(lambda x: x in printable, aclass))
                for data in toolData:
                    if not not data['color']:
                        if len(data['color']) == 0:
                            continue
                        color = TDIOUtils.hex_to_rgb(data['color'])
                        if toolType == 'freehand':
                            if label not in contoursmap:
                                contoursmap[label] = []
                            points = getPointsFromPolygon(data)
                            # points = [[10,10], [110,10], [110,110], [10, 110]]
                            contour = []
                            for p in points:
                                try:
                                    ras = self.ijkToRas(ijkToRasMatrix, transformVolumeRasToRas, p[0], p[1], instanceindex)
                                    # print('ras:', ras)
                                    contour.append(np.array([p[0], p[1], instanceindex], dtype=(np.int)))
                                except Exception as ex:
                                    print(ex)
                            contoursmap[label].append(contour)
                            colorsmap[label] = color

        segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        segmentationNode.CreateDefaultDisplayNodes()
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolume) #I tried with and without this line

        labelinginterface = projectjson['labelinginterface']
        if 'tools' in labelinginterface and len(labelinginterface['tools']) > 0:
            for tool in labelinginterface['tools']:
                name = tool['name']
                color = TDIOUtils.hex_to_rgb(tool['color'])
                print(color)
                segment = slicer.vtkSegment()
                segment.SetName(name)
                segment.SetColor(color)
                segmentsmap[name] = segment
 
        # print(colorsmap, contoursmap)
        for key in contoursmap:
            segmentName = key
            segment = segmentsmap[key]
            contours = contoursmap[key]
            self.addContoursToSegment(ijkToRasMatrix, transformVolumeRasToRas, segment, contours, segmentName)

        for key in segmentsmap:
            segment = segmentsmap[key]
            segmentationNode.GetSegmentation().AddSegment(segment)

    def addContoursToSegment(self, ijkToRasMatrix, transformVolumeRasToRas, segment, contours, name):
     contoursPolyData = vtk.vtkPolyData()
     contourPoints = vtk.vtkPoints()
     contourLines = vtk.vtkCellArray()
     contoursPolyData.SetLines(contourLines)
     contoursPolyData.SetPoints(contourPoints)
     for contour in contours:
         startPointIndex = contourPoints.GetNumberOfPoints()
         contourLine = vtk.vtkPolyLine()
         linePointIds = contourLine.GetPointIds()
         for point in contour:
            raspoint = self.ijkToRas(ijkToRasMatrix, transformVolumeRasToRas, point[1], point[0], point[2])
            linePointIds.InsertNextId(contourPoints.InsertNextPoint(raspoint))
         linePointIds.InsertNextId(startPointIndex)
         contourLines.InsertNextCell(contourLine)
     segment.AddRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName(), contoursPolyData)


class TDIOServerConnection:
    __module__ = __name__
    __qualname__ = 'TDIOServerConnection'

    def __init__(self, cloud_server_url=None, local_server_url=None, api_version=None):
        self.tmpdir = slicer.util.tempDirectory('tdio')
        self.volumeToImageFiles = dict()
        self.useCompression = True
        self.tdioClientAPI = TDIOClientAPI()
        self.setServer(cloud_server_url, api_version)

    def setServer(self, cloud_server_url=None, local_server_url=None, api_version=None):
        if not cloud_server_url:
            cloud_server_url = 'https://app.trainingdata.io'
        if not api_version:
            api_version = 'v1'
        self.tdioClientAPI.api_version = api_version

    def setUseCompression(self, useCompression):
        self.useCompression = useCompression

    def nodeCacheKey(self, mrmlNode):
        return mrmlNode.GetID() + '*' + str(mrmlNode.GetMTime())

    def saveVolumeToFile(self, volume):
        print('saveVolumeToFile()')
        in_file = tempfile.NamedTemporaryFile(suffix=(self.inputFileExtension()), dir=(self.tmpdir)).name
        print(in_file, volume)
        slicer.util.saveNode(volume, in_file)

    def inputFileExtension(self):
        if self.useCompression:
            return '.nii.gz'
        else:
            return '.nii'

    def outputFileExtension(self):
        return '.nii.gz'
        
    def convertToCornerstoneAnnotations(self, authtoken, seriesjson, listimagelistpolygons, segmentationid, segmentationcolor, jobid, useremail):
        self.tdioClientAPI.convertToCornerstoneAnnotations('https://app.trainingdata.io', authtoken, seriesjson, listimagelistpolygons, segmentationid, segmentationcolor, jobid, useremail)
        self.tdioClientAPI.convertToCornerstoneAnnotations('http://localhost:8090', authtoken, seriesjson, listimagelistpolygons, segmentationid, segmentationcolor, jobid, useremail)

class NvidiaClientAPI:
    __module__ = __name__
    __qualname__ = 'NvidiaClientAPI'

    def __init__(self, server_url=None, server_version=None, progress_callback=None):
        self.aiaa_tmpdir = slicer.util.tempDirectory('slicer-aiaa')
        self.volumeToImageFiles = dict()
        self.progress_callback = progress_callback
        self.useCompression = True
        self.aiaaClient = AIAAClient()
        self.setServer(server_url, server_version)

    def __del__(self):
        shutil.rmtree((self.aiaa_tmpdir), ignore_errors=True)

    def inputFileExtension(self):
        if self.useCompression:
            return '.nii.gz'
        else:
            return '.nii'

    def outputFileExtension(self):
        return '.nii.gz'

    def setServer(self, server_url=None, server_version=None):
        if not server_url:
            server_url = 'http://skull.cs.queensu.ca:8123'
        if not server_version:
            server_version = 'v1'
        logging.debug('Using AIAA server {}: {}'.format(server_version, server_url))
        self.aiaaClient.server_url = server_url
        self.aiaaClient.api_version = server_version

    def setUseCompression(self, useCompression):
        self.useCompression = useCompression

    def setProgressCallback(self, progress_callback=None):
        self.progress_callback = progress_callback

    def reportProgress(self, progress):
        if self.progress_callback:
            self.progress_callback(progress)

    def list_models(self, authtoken, jobid, seriesid, instanceid, annotatoremail):
        logging.info('Fetching List of Models for label: ')
        result = self.aiaaClient.model_list(authtoken, jobid, seriesid, instanceid, annotatoremail)
        return result

    def nodeCacheKey(self, mrmlNode):
        return mrmlNode.GetID() + '*' + str(mrmlNode.GetMTime())

    def segmentation(self, model, inputVolume):
        logging.debug('Preparing input data for segmentation')
        self.reportProgress(0)
        in_file = self.volumeToImageFiles.get(self.nodeCacheKey(inputVolume))
        if in_file is None:
            in_file = tempfile.NamedTemporaryFile(suffix=(self.inputFileExtension()), dir=(self.aiaa_tmpdir)).name
            self.reportProgress(5)
            start = time.time()
            slicer.util.saveNode(inputVolume, in_file)
            logging.info('Saved Input Node into {0} in {1:3.1f}s'.format(in_file, time.time() - start))
            self.volumeToImageFiles[self.nodeCacheKey(inputVolume)] = in_file
        else:
            logging.debug('Using cached image file: {}'.format(in_file))
        self.reportProgress(30)
        result_file = tempfile.NamedTemporaryFile(suffix=(self.outputFileExtension()), dir=(self.aiaa_tmpdir)).name
        params = self.aiaaClient.segmentation(model, in_file, result_file, save_doc=True)
        extreme_points = params.get('points', params.get('extreme_points'))
        logging.debug('Extreme Points: {}'.format(extreme_points))
        self.reportProgress(100)
        return (
         extreme_points, result_file)

    def dextr3d(self, model, pointset, inputVolume, modelInfo):
        self.reportProgress(0)
        logging.debug('Preparing for Annotation/Dextr3D Action')
        node_id = inputVolume.GetID()
        in_file = self.volumeToImageFiles.get(self.nodeCacheKey(inputVolume))
        logging.debug('Node Id: {} => {}'.format(node_id, in_file))
        if in_file is None:
            in_file = tempfile.NamedTemporaryFile(suffix=(self.inputFileExtension()), dir=(self.aiaa_tmpdir)).name
            self.reportProgress(5)
            start = time.time()
            slicer.util.saveNode(inputVolume, in_file)
            logging.info('Saved Input Node into {0} in {1:3.1f}s'.format(in_file, time.time() - start))
            self.volumeToImageFiles[self.nodeCacheKey(inputVolume)] = in_file
        else:
            logging.debug('Using Saved Node from: {}'.format(in_file))
        self.reportProgress(30)
        pad = 20
        roi_size = '128x128x128'
        if modelInfo is not None:
            if 'padding' in modelInfo:
                pad = modelInfo['padding']
                roi_size = 'x'.join(map(str, modelInfo['roi']))
        result_file = tempfile.NamedTemporaryFile(suffix=(self.outputFileExtension()), dir=(self.aiaa_tmpdir)).name
        self.aiaaClient.dextr3dmodelpointsetin_fileresult_filepadroi_size
        self.reportProgress(100)
        return result_file

    def mask2polygon(self, niftiimagefilepath, params):
        logging.debug('Mask2Polygon: ')
        jsonarray = self.aiaaClient.mask2polygon(niftiimagefilepath, params)
        return jsonarray
