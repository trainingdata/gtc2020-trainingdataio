import os, unittest, vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

class SegmentEditorTDIO(ScriptedLoadableModule):
    """
    'Uses ScriptedLoadableModule base class, available at:\n    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py\n    '"""
    __module__ = __name__
    __qualname__ = 'SegmentEditorTDIO'

    def __init__(self, parent):
        import string
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = 'SegmentEditorTDIO'
        self.parent.categories = ['Segmentation']
        self.parent.dependencies = ['Segmentations']
        self.parent.contributors = ['Gaurav Gupta (TrainingData.io)']
        self.parent.hidden = True
        self.parent.helpText = 'This hidden module registers TrainingData.io AI-Assisted segment editor effect'
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = 'Supported by NA-MIC, NAC, BIRN, NCIGT, and the Slicer Community. See http://www.slicer.org for details.'
        self.instance = None
        slicer.app.connect('startupCompleted()', self.initializeAfterStartup)

    def initializeAfterStartup(self):
        import shutil
        pluginDir = os.path.dirname(__file__)
        logging.info('This plugin dir: {}'.format(pluginDir))
        if os.path.exists(pluginDir + '/client_api.py'):
            os.remove(pluginDir + '/TDIOClientAPI/client_api.py')
        if os.path.exists(pluginDir + '/client_api.pyc'):
            os.remove(pluginDir + '/TDIOClientAPI/client_api.pyc')
        if os.path.exists(pluginDir + '/TDIOClientAPI/__pycache__/client_api.cpython-36.pyc'):
            os.remove(pluginDir + '/TDIOClientAPI/__pycache__/client_api.cpython-36.pyc')
        import qSlicerSegmentationsEditorEffectsPythonQt as qSlicerSegmentationsEditorEffects
        self.instance = qSlicerSegmentationsEditorEffects.qSlicerSegmentEditorScriptedEffect(None)
        effectFilename = os.path.join(os.path.dirname(__file__), self.__class__.__name__ + 'Lib/SegmentEditorEffect.py')
        self.instance.setPythonSource(effectFilename.replace('\\', '/'))
        self.instance.self().register()
        if not slicer.app.commandOptions().noMainWindow:
            self.settingsPanel = SegmentEditorTDIOSettingsPanel()
            slicer.app.settingsDialog().addPanel('TrainingData.io', self.settingsPanel)


class _ui_SegmentEditorTDIOSettingsPanel(object):
    __module__ = __name__
    __qualname__ = '_ui_SegmentEditorTDIOSettingsPanel'

    def __init__(self, parent):
        vBoxLayout = qt.QVBoxLayout(parent)
        aiaaGroupBox = ctk.ctkCollapsibleGroupBox()
        aiaaGroupBox.title = 'AI-Assisted Annotation Server'
        aiaaGroupLayout = qt.QFormLayout(aiaaGroupBox)
        serverUrl = qt.QLineEdit()
        aiaaGroupLayout.addRow('Server address:', serverUrl)
        parent.registerProperty('NVIDIA-AIAA/serverUrl', serverUrl, 'text', str(qt.SIGNAL('textChanged(QString)')))
        serverUrlHistory = qt.QLineEdit()
        aiaaGroupLayout.addRow('Server address history:', serverUrlHistory)
        parent.registerProperty('NVIDIA-AIAA/serverUrlHistory', serverUrlHistory, 'text', str(qt.SIGNAL('textChanged(QString)')))
        compressDataCheckBox = qt.QCheckBox()
        compressDataCheckBox.checked = True
        compressDataCheckBox.toolTip = 'Enable this option on computer with slow network upload speed. Data compression reduces network transfer time but increases preprocessing time.'
        aiaaGroupLayout.addRow('Compress data:', compressDataCheckBox)
        compressDataMapper = ctk.ctkBooleanMapper(compressDataCheckBox, 'checked', str(qt.SIGNAL('toggled(bool)')))
        parent.registerProperty('NVIDIA-AIAA/compressData', compressDataMapper, 'valueAsInt', str(qt.SIGNAL('valueAsIntChanged(int)')))
        vBoxLayout.addWidget(aiaaGroupBox)
        vBoxLayout.addStretch(1)


class SegmentEditorTDIOSettingsPanel(ctk.ctkSettingsPanel):
    __module__ = __name__
    __qualname__ = 'SegmentEditorTDIOSettingsPanel'

    def __init__(self, *args, **kwargs):
        (ctk.ctkSettingsPanel.__init__)(self, *args, **kwargs)
        self.ui = _ui_SegmentEditorTDIOSettingsPanel(self)


class SegmentEditorTDIOTest(ScriptedLoadableModuleTest):
    r"""'\n    This is the test case for your scripted module.\n    Uses ScriptedLoadableModuleTest base class, available at:\n    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py\n    '"""
    __module__ = __name__
    __qualname__ = 'SegmentEditorTDIOTest'

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_TDIO1()

    def test_TDIO1(self):
        """
        Basic automated test of the segmentation method:
        - Create segmentation by placing sphere-shaped seeds
        - Run segmentation
        - Verify results using segment statistics
        The test can be executed from SelfTests module (test name: SegmentEditorTDIO)
        """
        self.delayDisplay('Starting test_TDIO1')
        import vtkSegmentationCorePython as vtkSegmentationCore, vtkSlicerSegmentationsModuleLogicPython as vtkSlicerSegmentationsModuleLogic, SampleData
        from SegmentStatistics import SegmentStatisticsLogic
        self.delayDisplay('Load master volume')
        masterVolumeNode = SampleData.downloadSample('MRBrainTumor1')
        self.delayDisplay('Create segmentation containing a few spheres')
        segmentationNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLSegmentationNode')
        segmentationNode.CreateDefaultDisplayNodes()
        segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
        segmentGeometries = [
         [
          'Tumor', [[10, -6, 30, 28]]],
         [
          'Background',
          [
           [
            10, 0, 65, 22], [15, 1, -14, 30], [12, 0, 28, -7], [5, 0, 30, 54], [12, 31, 33, 27], [17, -42, 30, 27],
           [
            6, -2, -17, 71]]],
         [
          'Air', [[10, 76, 73, 0], [15, -70, 74, 0]]]]
        for segmentGeometry in segmentGeometries:
            segmentName = segmentGeometry[0]
            appender = vtk.vtkAppendPolyData()
            for sphere in segmentGeometry[1]:
                sphereSource = vtk.vtkSphereSource()
                sphereSource.SetRadius(sphere[0])
                sphereSource.SetCenter(sphere[1], sphere[2], sphere[3])
                appender.AddInputConnection(sphereSource.GetOutputPort())

            segment = vtkSegmentationCore.vtkSegment()
            segment.SetName(segmentationNode.GetSegmentation().GenerateUniqueSegmentID(segmentName))
            appender.Update()
            segment.AddRepresentation(vtkSegmentationCore.vtkSegmentationConverter.GetSegmentationClosedSurfaceRepresentationName(), appender.GetOutput())
            segmentationNode.GetSegmentation().AddSegment(segment)

        self.delayDisplay('Create segment editor')
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
        segmentEditorWidget.show()
        segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
        segmentEditorNode = slicer.vtkMRMLSegmentEditorNode()
        slicer.mrmlScene.AddNode(segmentEditorNode)
        segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
        segmentEditorWidget.setSegmentationNode(segmentationNode)
        segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)
        self.delayDisplay('Run segmentation')
        segmentEditorWidget.setActiveEffectByName('TDIO')
        effect = segmentEditorWidget.activeEffect()
        effect.setParameter('ObjectScaleMm', 3.0)
        effect.self().onApply()
        self.delayDisplay('Make segmentation results nicely visible in 3D')
        segmentationDisplayNode = segmentationNode.GetDisplayNode()
        segmentationDisplayNode.SetSegmentVisibility('Air', False)
        segmentationDisplayNode.SetSegmentOpacity3D('Background', 0.5)
        self.delayDisplay('Compute statistics')
        segStatLogic = SegmentStatisticsLogic()
        segStatLogic.computeStatistics(segmentationNode, masterVolumeNode)
        resultsTableNode = slicer.vtkMRMLTableNode()
        slicer.mrmlScene.AddNode(resultsTableNode)
        segStatLogic.exportToTable(resultsTableNode)
        segStatLogic.showTable(resultsTableNode)
        self.delayDisplay('Check a few numerical results')
        self.assertEqual(round(segStatLogic.statistics[('Tumor', 'LM volume cc')]), 16)
        self.assertEqual(round(segStatLogic.statistics[('Background', 'LM volume cc')]), 3010)
        self.delayDisplay('test_TDIO1 passed')
