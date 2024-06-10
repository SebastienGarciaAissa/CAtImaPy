# -*- coding: utf-8 -*- 

# CAtImaPy : Cold Atom Imaging with Python GUI 
# Python program for absorption and fluo imaging of atoms
# Sebastien Garcia 2019 

import os, shutil
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Import the Qt Pakages
from PyQt5 import QtCore, QtWidgets
# Import the file system packages
import builtins
import sys
import time
import glob
import shelve

# Import the sientific stuff
import numpy as np
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

# Import code modules
# import GUI
import UI
# Import Cameras module file
import Cameras
# Imagings module
import Imagings


'''
#####------------------------------------------------ Main Window code ---------
'''

class MainWindow(QtWidgets.QMainWindow):
    """MainWindow class that hold the ui and the main code"""
    
    def __init__(self):
        """Initialize MainWindow object that hold the ui and the main code
        
        Return: 
            MainWindow object
        """
        super().__init__()
        self.ui = UI.Ui_MainWindow()
        self.ui.setupUi(self)
        
        builtins.mainWin = self

        try:
            os.chdir(self.dirname)
        except:
            self.dirname = scriptDirPath

        self.logPersistent_load()
        self.setEnabledAcquisitionUIbuttons(False)
        #connect ui response to value changes of buttons and variables 
        #automatic
        self.connectUiVariables()
        #not automatic sutff
        self.ui.imaging_averages.valueChanged.connect(self.on_imaging_averages_valueChanged) 
        self.ui.imaging_scans.valueChanged.connect(self.on_imaging_scans_valueChanged)
        self.ui.imaging_T_averages.valueChanged.connect(self.on_imaging_T_averages_valueChanged)
        self.ui.imaging_T_TOFscans.valueChanged.connect(self.on_imaging_T_TOFscans_valueChanged)
        self.ui.imaging_T_scans.valueChanged.connect(self.on_imaging_T_scans_valueChanged)
        self.ui.imaging_LT_averages.valueChanged.connect(self.on_imaging_LT_averages_valueChanged)
        self.ui.imaging_LT_Tscans.valueChanged.connect(self.on_imaging_LT_Tscans_valueChanged)
        self.ui.imaging_LT_scans.valueChanged.connect(self.on_imaging_LT_scans_valueChanged)
        self.ui.imaging_ROIblackNumber.valueChanged.connect(self.on_imaging_ROIblackNumber_valueChanged)
        self.ui.imaging_ROIredNumber.valueChanged.connect(self.on_imaging_ROIredNumber_valueChanged)
        self.ui.imaging_ROIgreenNumber.valueChanged.connect(self.on_imaging_ROIgreenNumber_valueChanged)
        self.ui.saveload_autoSaveMeas.stateChanged.connect(self.on_saveload_autoSaveMeas_stateChanged)
        self.on_saveload_autoSaveMeas_stateChanged()

        self.camerasConfigs = Cameras.Config.camerasConfigs
        self.display_configured_cameras_list()
        self.ui.camera_cameraNumber.setValue(0)
        #initialize camera object and connect to camera : here no camera connected initialy 
        # =>base Camera et Imaging object initialized
        self.camera_connector() 
        self.nextfile()# find the next file for saving 
        self.connectUiVariables(objectsToConnect=['Imaging']) #connect buttons for Imaging object
        #not auto stuff
        self.Imaging.averages = self.ui.imaging_averages.value()
        self.Imaging.scans = self.ui.imaging_scans.value()
        self.Imaging.cycles = self.Imaging.averages*self.Imaging.scans
        self.ui.lcdNumber_imaging_cycles.display(self.Imaging.cycles)
        self.Imaging.T_averages = self.ui.imaging_T_averages.value()
        self.Imaging.T_TOFscans = self.ui.imaging_T_TOFscans.value()
        self.Imaging.T_scans = self.ui.imaging_T_scans.value()
        self.Imaging.T_cycles = self.Imaging.T_averages*self.Imaging.T_TOFscans*self.Imaging.T_scans
        self.ui.lcdNumber_imaging_T_cycles.display(self.Imaging.T_cycles)
        self.Imaging.LT_averages = self.ui.imaging_LT_averages.value()
        self.Imaging.LT_Tscans = self.ui.imaging_LT_Tscans.value()
        self.Imaging.LT_scans = self.ui.imaging_LT_scans.value()
        self.Imaging.LT_cycles = self.Imaging.LT_averages*self.Imaging.LT_Tscans*self.Imaging.LT_scans
        self.ui.lcdNumber_imaging_LT_cycles.display(self.Imaging.LT_cycles)
        
        # for plots toolbars
        self.naviToolbarImage = NavigationToolbar(self.ui.mplwidgetImage, self)
        self.naviToolbarAnalysisGraph = NavigationToolbar(self.ui.mplwidgetAnalysisGraph, self)
        self.ui.toolBar.addWidget(self.naviToolbarImage)
        self.ui.toolBar.addWidget(self.naviToolbarAnalysisGraph)



    def closeEvent(self,event):  
        """Handle close event by deleting MainWindow object. """
        # reply = QtWidgets.QMessageBox.question(self, 'Exit',
        #     "Are you sure to quit?", QtWidgets.QMessageBox.Yes | 
        #     QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        # if reply == QtWidgets.QMessageBox.Yes:
        #   event.accept()
        #   self.__del__()
        # else:
        #     event.ignore()       
        self.__del__()

    
    def __del__(self):
        """Delete MainWindow object : first save persistent then delete  """
        if hasattr(self, 'Imaging') and not(self.Imaging.loaded) :
            self.logPersistent_save()
            self.persistentData.close()
        try:
            del(self.Imaging)
            del(self.Camera)
        except:
            print('No hardware to close..')


    def connectUiVariables(self, objectsToConnect=['mainWin']):
        """Connect automatically UI variables : (Double)SpinBoxes, CheckBoxes, ComboBoxes
        to object variables or functions (if ui name ends by 'Func')
        
        Keyword Args:
            objectsToConnect (list[str]) : list of objects (variables of mainWin) to load the variables in.
                The ui objectName should be of the form '<object name>__<object variable name>' . 
                If 'mainWin' is passed, then load all variables without '__' as variables of mainWin.
                Default is ['mainWin'].
        """
        findstring = '__'
        if not (np.array(objectsToConnect) == 'mainWin').any():
            findstring = '' # to load only variables as variables a specifc object
        for i,val in enumerate(self.ui.__dict__):
        ## this is to connect the buttons with their variable name automaticallly
        # with their function 
            Qobject = str(self.ui.__dict__[val])[17:31]
            Qcmd=False
            if Qobject == 'QDoubleSpinBox' or Qobject == 'QSpinBox objec' :
                Qcmd = ['.setValue', '.value', '.valueChanged']
            elif Qobject == 'QCheckBox obje':
                Qcmd = ['.setChecked', '.isChecked', '.stateChanged']
            elif Qobject == 'QComboBox obje':
                Qcmd = ['.setCurrentIndex', '.currentIndex', '.currentIndexChanged']
            if (val.find(findstring) == -1 \
                    or (val.split('__')[0] == np.array(objectsToConnect)).any()) \
                    and Qcmd:
                if val[-4:] == 'Func':
                    # define the function that name of Qobject is the function
                    exec("""import builtins
def changeValue(value):
    self = builtins.mainWin
    """ + ('.'.join(('self.'+val[:-4]).split('__'))) \
                            + '(self.ui.' + val + Qcmd[1] + '())')
                else:
                    # define the function that variable gets updated
                    exec("""import builtins
def changeValue(value):
    self = builtins.mainWin
    """ + ('.'.join(('self__'+val).split('__'))) \
                            + ' = self.ui.' + val + Qcmd[1] + '()')
                    # write the value of persistentData into the variable
                    try:
                        vars(eval('.'.join(('self__'+val).split('__')[:-1]))
                            )[val.split('__')[-1]] = self.persistentData[val]
                    except:
                        print( ' New Button "' + val + '" integrated.')
                        vars(eval('.'.join(('self__'+val).split('__')[:-1]))
                            )[val.split('__')[-1]] = eval('self.ui.' + val + Qcmd[1] + '()')
                # connect the defined function with your Qobject
                eval('self.ui.'+val+Qcmd[2]+'.connect('\
                            + 'changeValue'
                            +')')
    
    
    def loadUiValues(self, objectsToConnect=['mainWin']):
        """Load automatically values to UI variables : (Double)SpinBoxes, CheckBoxes, ComboBoxes
        
        Keyword Args:
            objectsToConnect=['mainWin'] (list of str) : list of objects to load the variables from.
                The ui objectName should be of the form '<object name>__<object variable name>' . 
                If 'mainWin' is passed, then load all variables from mainWin to matching ui variables without '__'.
        """
        findstring = '__'
        if not (np.array(objectsToConnect) == 'mainWin').any():
            findstring = ''
        for i,val in enumerate(self.ui.__dict__):
        ## this is to load the values of the ui into the variable of a class to which they are connected 
            Qobject = str(self.ui.__dict__[val])[17:31]
            Qcmd=False
            if Qobject == 'QDoubleSpinBox' or Qobject == 'QSpinBox objec' :
                Qcmd = ['.setValue', '.value', '.valueChanged']
            elif Qobject == 'QCheckBox obje':
                Qcmd = ['.setChecked', '.isChecked', '.stateChanged']
            elif Qobject == 'QComboBox obje':
                Qcmd = ['.setCurrentIndex', '.currentIndex', '.currentIndexChanged']
            if (val.find(findstring) == -1 \
                    or (val.split('__')[0] == np.array(objectsToConnect)).any()) \
                    and Qcmd:
                        vars(eval('.'.join(('self__'+val).split('__')[:-1]))
                            )[val.split('__')[-1]] = eval('self.ui.' + val + Qcmd[1] + '()')
                
    
    def setEnabledAcquisitionUIbuttons(self, enabled):
        """Enabling or disabling UI buttons related to acquisition. 
            Button are enabled only when a camera is connected.
        
        Args:
            enabled (bool) : Set enabled state of buttons
        """
        self.ui.pushButton_take_image.setEnabled(enabled)
        self.ui.pushButton_save_image.setEnabled(enabled)
        self.ui.pushButton_exposure_gain_set.setEnabled(enabled)
        self.ui.pushButton_exposure_auto_av.setEnabled(enabled)
        self.ui.pushButton_exposure_auto_max.setEnabled(enabled)
        self.ui.Camera__setTriggerModeFunc.setEnabled(enabled)
        self.ui.pushButton_ROI_set.setEnabled(enabled)
        self.ui.pushButton_ROI_delete.setEnabled(enabled)
        self.ui.pushButton_ROI_add.setEnabled(enabled)
        self.ui.Imaging__imagingType.setEnabled(enabled)
        self.ui.pushButton_imaging_start_measurement.setEnabled(enabled)
        self.ui.pushButton_start_temp_measurement.setEnabled(enabled)
        self.ui.pushButton_start_LT_measurement.setEnabled(enabled)
        self.ui.pushButton_save_imagingObject.setEnabled(enabled)
    
    
    
    
    '''   
#####--------------------------------------------- Persitent data and ROI array management ---
'''


    def logPersistent_load(self):
        """Load automatically values to UI variables from previous session.
            Values are saved in persistentData file."""
        self.persistentData = shelve.open(os.path.join(scriptDirPath,'persistentData'))
        for i,val in enumerate(self.persistentData):
            if val in self.ui.__dict__:
                Qobject = str(self.ui.__dict__[val])[17:31]
                if Qobject == 'QDoubleSpinBox' or Qobject == 'QSpinBox objec':
                    Qcmd = ['.setValue', '.value', '.valueChanged']
                elif Qobject == 'QCheckBox obje':
                    Qcmd = ['.setChecked', '.isChecked', '.stateChanged']
                elif Qobject == 'QComboBox obje':
                    Qcmd = ['.setCurrentIndex', '.currentIndex', '.currentIndexChanged']
                eval('self.ui.'+val+'.blockSignals(True)')
                eval('self.ui.'+val+Qcmd[0]+'('+str(self.persistentData[val])+')')
                eval('self.ui.'+val+'.blockSignals(False)')
            else:
                try:
                    toLoad = self.persistentData[val][0]
                    if not toLoad :
                        vars(eval('.'.join(('self.'+val).split('.')[:-1]))
                            )[val.split('.')[-1]] = self.persistentData[val][1]
                except:
                    None
        self.logUIROIarray_start()
        try:
            os.chdir(self.dirname)
            self.nextfile()
        except:
            self.dirname = scriptDirPath
            os.chdir(scriptDirPath)
            self.nextfile()
            
        
    def logPersistent_save(self):
        """Save values of UI variables from future sessions.
            Values are saved in persistentData file."""
        for i,val in enumerate(self.ui.__dict__):
            Qobject = str(self.ui.__dict__[val])[17:31]
            Qcmd = False
            if Qobject == 'QDoubleSpinBox' or Qobject == 'QSpinBox objec':
                Qcmd = ['.setValue', '.value', '.valueChanged']
            elif Qobject == 'QCheckBox obje':
                Qcmd = ['.setChecked', '.isChecked', '.stateChanged']
            elif Qobject == 'QComboBox obje':
                Qcmd = ['.setCurrentIndex', '.currentIndex', '.currentIndexChanged']
            if Qcmd:
                self.persistentData[val] = \
                    eval('self.ui.'+val+Qcmd[1]+'()')
        self.persistentData['dirname'] = [False, self.dirname]
        self.persistentData['ROIarray'] = [False, self.ROIarray]

    
    def logROIarray_update(self):
        """Update Analysis ROIs from ui table to mainWin.ROIarray"""
        self.ROIarray = np.zeros( (self.ui.tableWidget_ROI.rowCount(),self.ui.tableWidget_ROI.columnCount()) , dtype='<U20' )
        for i in range(self.ROIarray.shape[0]):
            for j in range(self.ROIarray.shape[1]):
                self.ROIarray[i,j] = str(self.ui.tableWidget_ROI.item(i,j).text())
        
        
    def logUIROIarray_start(self):
        """Initialize Analysis ROIs ui table from mainWin.ROIarray"""
        try:
            self.ROIarray
        except:
            self.ROIarray = np.array([['0','base', '0.0', '0.0', '100.0', '100.0']], dtype='<U20' )
        #clear ui array
        self.ui.tableWidget_ROI.setRowCount(0)
        # fill ui array
        for i in range(self.ROIarray.shape[0]):
            self.uiROIarrayAddRow(self.ROIarray[self.ROIarray.shape[0] - 1 - i])





    '''    
#####----------------------------Data saving and printing----
'''

    def save_imaging(self):
        """Save imaging results (imaging object and pictures of graphs) and increment filename."""
        self.Imaging.comment = str(self.ui.lineEdit_saving_comment.text())
        dirAndFileName = os.path.join(self.dirname, self.filename)
        self.Imaging.dirAndFileName = dirAndFileName
        if self.saveload_SaveImagePic:
            self.ui.mplwidgetImage.figure.savefig(
                dirAndFileName + '_Image.png')
        if self.saveload_SaveAnalysisGraphPic:
            self.ui.mplwidgetAnalysisGraph.figure.savefig(
                dirAndFileName + '_AnalysisGraph.png')
        self.Imaging.save_imaging_vars_as_dict(SaveAtomicDensity = self.saveload_SaveAtomicDensity)
        self.ui.lineEdit_saving_comment.clear()
        self.nextfile()
        
        
    def loadImagingvaluesToUI(self):
        """ Load the values of the imaging object to the UI.
            Only used when loading old results.
        """
        # load auto for ui objects defined as 'Imaging__'+.... 
        for i,val in enumerate(self.ui.__dict__):
            Qobject = str(self.ui.__dict__[val])[17:31]
            Qcmd=False
            if Qobject == 'QDoubleSpinBox' or Qobject == 'QSpinBox objec' :
                Qcmd = ['.setValue', '.value', '.valueChanged']
            elif Qobject == 'QCheckBox obje':
                Qcmd = ['.setChecked', '.isChecked', '.stateChanged']
            elif Qobject == 'QComboBox obje':
                Qcmd = ['.setCurrentIndex', '.currentIndex', '.currentIndexChanged']
            if (val.split('__')[0] == 'Imaging') and Qcmd and hasattr(self.Imaging, val.split('__')[-1]) :
                eval('self.ui.'+val+Qcmd[0]+'('\
                        +str(vars(eval('.'.join(('self__'+val).split('__')[:-1])))[val.split('__')[-1]])+')')
        # not auto stuff of Imaging attributes
        self.ui.imaging_averages.setValue(self.Imaging.averages)
        self.ui.imaging_scans.setValue(self.Imaging.scans)
        self.ui.lcdNumber_imaging_cycles.display(self.Imaging.cycles)
        self.ui.imaging_T_averages.setValue(self.Imaging.T_averages)
        self.ui.imaging_T_TOFscans.setValue(self.Imaging.T_TOFscans)
        self.ui.imaging_T_scans.setValue(self.Imaging.T_scans)
        self.ui.lcdNumber_imaging_T_cycles.display(self.Imaging.T_cycles)
        self.ui.imaging_LT_averages.setValue(self.Imaging.LT_averages)
        self.ui.imaging_LT_Tscans.setValue(self.Imaging.LT_Tscans)
        self.ui.imaging_LT_scans.setValue(self.Imaging.LT_scans)
        self.ui.lcdNumber_imaging_LT_cycles.display(self.Imaging.LT_cycles)
        self.ui.lineEdit_scanVarName.setText(self.Imaging.scanVarName)
        self.ui.lineEdit_scanUnitName.setText(self.Imaging.scanUnitName)
        # not auto stuff of Camera attributes saved in Imaging 
        self.ui.camera_cameraNumber.setValue(0) #set 0 for selected
        self.ui.lcdNumber_connectedCamera.display(self.Imaging.cameraNumber) #set used camera number from saved imaging file
        if not(self.Imaging.cameraNumber == 0):
            #for exposure, gain and trigger first check if present in loaded imaging object : for backwards comptibility with old files
            if hasattr(self.Imaging, 'cameraExposurems') : 
                self.ui.camera_exposurems.setValue(self.Imaging.cameraExposurems)
            if hasattr(self.Imaging, 'cameraGaindB') :
                self.ui.camera_gaindB.setValue(self.Imaging.cameraGaindB)
            if hasattr(self.Imaging, 'cameraTriggerMode') :
                self.ui.Camera__setTriggerModeFunc.setCurrentIndex(self.Imaging.cameraTriggerMode)
            if hasattr(self.Imaging, 'flushSensor') :
                self.ui.Imaging__flushSensor.setChecked(self.Imaging.flushSensor)
            if hasattr(self.Imaging, 'removeBackground') :
                self.ui.Imaging__removeBackground.setChecked(self.Imaging.removeBackground)
            self.ui.lcdNumber_camera_pixelCalXumperpx.display(self.Imaging.pixelCalXumperpx)
            self.ui.lcdNumber_camera_pixelCalYumperpx.display(self.Imaging.pixelCalYumperpx)
            self.ui.lcdNumber_camera_bit_depth.display(self.Imaging.imageBitDepth)
            self.ui.lcdNumber_camera_maxLevel.display(self.Imaging.cameraMaxLevel)
            self.ui.label_image_datatype.setText(str(self.Imaging.imageDtype))
            self.ui.lcdNumber_camera_QuantumEff.display(self.Imaging.cameraConfig['cameraQuantumEff'])
            self.ui.lcdNumber_camera_numericalAperture.display(self.Imaging.cameraConfig['numericalAperture'])
            self.ui.lcdNumber_imaging_atomicMassAU.display(self.Imaging.cameraConfig['Imaging__atomicMassAU'])
            self.ui.lcdNumber_imaging_atomicFrequencyTHz.display(self.Imaging.cameraConfig['Imaging__atomicFrequencyTHz'])
            self.ui.lcdNumber_imaging_crossSectionum2.display(self.Imaging.cameraConfig['Imaging__crossSectionum2'])
            self.ui.lcdNumber_imaging_Isat.display(self.Imaging.cameraConfig['Imaging__Isat'])
            self.ui.lcdNumber_imaging_atomicLineFWHWinMHz.display(self.Imaging.cameraConfig['Imaging__atomicLineFWHWinMHz'])
            self.ui.imaging_ROIblackNumber.blockSignals(True)
            self.ui.imaging_ROIblackNumber.setValue(self.Imaging.ROIblackTabIndex+1)
            self.ui.imaging_ROIblackNumber.blockSignals(False)
            self.ui.imaging_ROIredNumber.blockSignals(True)
            self.ui.imaging_ROIredNumber.setValue(self.Imaging.ROIredTabIndex+1)
            self.ui.imaging_ROIredNumber.blockSignals(False)
            self.ui.imaging_ROIgreenNumber.blockSignals(True)
            self.ui.imaging_ROIgreenNumber.setValue(self.Imaging.ROIgreenTabIndex+1)
            self.ui.imaging_ROIgreenNumber.blockSignals(False)
 
    
    def load_imaging(self):
        """ Load the data from previously saved imaging object. """
        #disable UI acquisition buttons
        self.setEnabledAcquisitionUIbuttons(False)
        #if previous imaging was measured save ui settings in persistentData
        if not(self.Imaging.loaded) :
            self.logPersistent_save()
            self.persistentData.close()
        del(self.Imaging)
        #load object from pickle format
        dirAndFileName = os.path.join(self.dirname,self.filename)
        self.Imaging = Imagings.ImagingClass(dirAndFileName = dirAndFileName,
                                    mplwidgetImage = self.ui.mplwidgetImage,
                                    mplwidgetAnalysisGraph = self.ui.mplwidgetAnalysisGraph)
        self.Imaging.load_imaging_vars_from_dict(dirAndFileName)
        self.Imaging.loaded = True
        # reconstruct ROIarray
        self.ROIarray = np.zeros((self.Imaging.ROIn, 6), dtype='<U20' )
        self.ROIarray[:, 0] = ((np.ones(self.Imaging.ROIn)*self.Imaging.cameraNumber).astype(int)).astype('<U20')
        self.ROIarray[:, 1] = self.Imaging.ROInameTab.astype('<U20')
        self.ROIarray[:, 2:6] = self.Imaging.ROIxywhTabum.astype('<U20')
        self.logUIROIarray_start()
        #load values and plots to UI
        self.ui.lineEdit_saving_comment.setText(self.Imaging.comment)
        self.ui.textBrowser_analyse_dictionary.setText(self.print_dict(vars(self.Imaging)))
        self.loadImagingvaluesToUI() 
        if type(self.Imaging.atomicDensityIntZperum2Av)==type(np.zeros((2,2))):
            self.Imaging.plot_2Ddata_on_mplwidgetImage(self.Imaging.atomicDensityIntZperum2Av)
        self.Imaging.plotAnalysis_update()
        

    def changeDirectory(self, dirname):
        """Change the folder where data will be saved in, and also save a copy of current UI values in this folder.
        
        Args : 
            dirname (str) : Absolute path to directory.
        
        """
        if dirname:
            self.dirname = os.path.normpath(dirname)
            os.chdir(self.dirname)
            self.logPersistent_save()
            self.nextfile()
            #save a copy of persistent data and config file
            shutil.copy(os.path.join(scriptDirPath,'persistentData.dat'),dirname)
            shutil.copy(os.path.join(scriptDirPath,'persistentData.dir'),dirname)
            shutil.copy(os.path.join(scriptDirPath,'persistentData.bak'),dirname)
            shutil.copy(os.path.join(scriptDirPath,'Cameras\Config.py'),dirname)


    def nextfile(self):
        """Find and set the next filename Imaging<N> with incremented number N."""
        files = glob.glob('Imaging*.txt')
        next_num = 0
        if files:
            files.sort()
            next_num = int(files[-1][-8:-4]) + 1
        self.filename = 'Imaging{0:04d}'.format(next_num)
        self.ui.label_save_ImagingObject_file.setText(
                os.path.join(self.dirname, self.filename))


    def display_configured_cameras_list(self):
        """Print in UI the main parameters of the cameras configured in Cameras.Config.camerasConfigs"""
        configuredCamerasText = ''       
        for camN in range(1,len(self.camerasConfigs)):
            configuredCamerasText += str(camN) + ' : ' +str(self.camerasConfigs[camN]['name'])
            configuredCamerasText += ' : ' + str(self.camerasConfigs[camN]['driver'])
            configuredCamerasText += ' ' + str(self.camerasConfigs[camN]['model'])
            configuredCamerasText += ' SN: ' + str(self.camerasConfigs[camN]['serial']) + '\n' 
        self.ui.textBrowser_configuredCameras.setText(configuredCamerasText)

    
    def print_dict(self, d, indentation=0):
        """Make a pretty string representation of the content of a dictionary.
        
        Args:
            d (dict) : Dictionnary to represent by a string
            
        Keyword Args:
            indentation (int) :  Number of spaces to place before key name 
                Used in recursive call for d variables that are dicts.
        
        Return: 
            String representation of d
        """
        s = ''
        for k,v in sorted(d.items()):
            s0 = ' '*indentation + str(k) + ' : '
            if type(v) is dict:
                s += s0+'\n'
                s += self.print_dict(v, indentation+2)
            elif type(v) == type(np.zeros((10,10))):
                if np.size(v) < 200 :
                    s += s0 + str(v)[:200-len(s0)] + '\n'
                else :
                    s += s0 + 'Array too large be printed \n'
            else:
                s += s0 + str(v)[:200-len(s0)] + '\n'
        return s


    '''
#####-------------------------- Imaging and Camera objects initializations and connections --
'''

    def imagingObjectInit(self):
        """Initialize Imaging object handling the data acquisition and analysis."""
        if hasattr(self, 'Imaging'):            
            del(self.Imaging)
        #create Imaging object
        dirAndFileName = os.path.join(self.dirname,self.filename)
        self.Imaging = Imagings.ImagingClass(dirAndFileName = dirAndFileName,
                                    mplwidgetImage = self.ui.mplwidgetImage,
                                    mplwidgetAnalysisGraph = self.ui.mplwidgetAnalysisGraph)
        # load values from ui
        self.loadUiValues(['Imaging'])
        #not auto stuff
        self.Imaging.averages = self.ui.imaging_averages.value()
        self.Imaging.scans = self.ui.imaging_scans.value()
        self.Imaging.cycles = self.Imaging.averages*self.Imaging.scans
        self.ui.lcdNumber_imaging_cycles.display(self.Imaging.cycles)
        self.Imaging.T_averages = self.ui.imaging_T_averages.value()
        self.Imaging.T_TOFscans = self.ui.imaging_T_TOFscans.value()
        self.Imaging.T_scans = self.ui.imaging_T_scans.value()
        self.Imaging.T_cycles = self.Imaging.T_averages*self.Imaging.T_TOFscans*self.Imaging.T_scans
        self.ui.lcdNumber_imaging_T_cycles.display(self.Imaging.T_cycles)
        self.Imaging.LT_averages = self.ui.imaging_LT_averages.value()
        self.Imaging.LT_Tscans = self.ui.imaging_LT_Tscans.value()
        self.Imaging.LT_scans = self.ui.imaging_LT_scans.value()
        self.Imaging.LT_cycles = self.Imaging.LT_averages*self.Imaging.LT_Tscans*self.Imaging.LT_scans
        self.ui.lcdNumber_imaging_LT_cycles.display(self.Imaging.LT_cycles)
        if hasattr(self, 'Camera') and not(self.camera_cameraNumber == 0) :
            self.Imaging.set_Imaging_variables_from_cam(self.Camera) # load values from Camera object
            self.Imaging.set_ROIs_from_ROIarray(self.ROIarray)
            #if no ROI defined for this camera : add one 
            if self.Imaging.ROIn == 0 :
                self.uiROIarrayAddRow(row = [str(int(self.Imaging.cameraNumber)),'NEW !', '0.0', '0.0', '100.0', '100.0'])
                self.on_pushButton_ROI_set_clicked()
                self.Imaging.set_ROIs_from_ROIarray(self.ROIarray)
            self.on_imaging_ROIblackNumber_valueChanged()
            self.on_imaging_ROIredNumber_valueChanged()
            self.on_imaging_ROIgreenNumber_valueChanged()


    def camera_connector(self):
        """Initialize Camera object handling the camera, 
        connect and configure camera ready for acquistion, 
        create corresponding Imaging object.
        """
        # record previous camera number
        try :
            oldCameraNumber = self.Camera._cameraNumber
            del(self.Camera)
            # print('Deleting previous camera , number ',oldCameraNumber)
        except : 
            oldCameraNumber = -1
            # print('No camera object was present')
        # reload persistent ui values if not in loaded analysis mode
        if hasattr(self, 'Imaging') and self.Imaging.loaded :
            oldCameraNumber = -1
            cameraNumber = self.camera_cameraNumber
            self.logPersistent_load()
            self.ui.camera_cameraNumber.setValue(cameraNumber)
        # load correct diver if possible
        self.Camera = Cameras.create_Camera(self.camera_cameraNumber, 
                                            triggerMode=self.ui.Camera__setTriggerModeFunc.currentIndex(),
                                            exposurems=self.camera_exposurems, 
                                            gaindB=self.camera_gaindB,
                                            loadDefault = self.camera_loadDefault)
        self.ui.camera_cameraNumber.setValue(self.Camera._cameraNumber)
        self.connectUiVariables(objectsToConnect=['Camera'])
        if not(self.camera_cameraNumber == 0):
            # print values in UI displays
            self.ui.camera_exposurems.setValue(self.Camera.exposurems)
            self.ui.camera_gaindB.setValue(self.Camera.gaindB)
            self.ui.Camera__setTriggerModeFunc.setCurrentIndex(self.Camera.triggerMode)
            if self.camera_loadDefault :
                self.ui.Imaging__flushSensor.setChecked(self.Camera.cameraConfig['defaultFlushSensor'])
                self.ui.Imaging__removeBackground.setChecked(self.Camera.cameraConfig['defaultRemoveBackground'])
            else : 
                self.ui.Imaging__flushSensor.stateChanged()
                self.ui.Imaging__removeBackground.stateChanged()
            self.ui.lcdNumber_camera_pixelCalXumperpx.display(self.Camera.pixelCalXumperpx)
            self.ui.lcdNumber_camera_pixelCalYumperpx.display(self.Camera.pixelCalYumperpx)
            self.ui.lcdNumber_camera_maxLevel.display(self.Camera.maxLevel)
            self.ui.lcdNumber_camera_QuantumEff.display(self.Camera.cameraConfig['cameraQuantumEff'])
            self.ui.lcdNumber_camera_numericalAperture.display(self.Camera.cameraConfig['numericalAperture'])
            self.ui.lcdNumber_imaging_atomicMassAU.display(self.Camera.cameraConfig['Imaging__atomicMassAU'])
            self.ui.lcdNumber_imaging_atomicFrequencyTHz.display(self.Camera.cameraConfig['Imaging__atomicFrequencyTHz'])
            self.ui.lcdNumber_imaging_crossSectionum2.display(self.Camera.cameraConfig['Imaging__crossSectionum2'])
            self.ui.lcdNumber_imaging_Isat.display(self.Camera.cameraConfig['Imaging__Isat'])
            self.ui.lcdNumber_imaging_atomicLineFWHWinMHz.display(self.Camera.cameraConfig['Imaging__atomicLineFWHWinMHz'])
            self.ui.Imaging__thresholdAbsImg.setValue(self.Camera.cameraConfig['Imaging__thresholdAbsImg'])
            self.ui.Imaging__includeSaturationEffects.setChecked(self.Camera.cameraConfig['Imaging__includeSaturationEffects'])
            self.ui.Imaging__laserPulseDurationus.setValue(self.Camera.cameraConfig['Imaging__laserPulseDurationus'])
            self.ui.Imaging__laserIntensity.setValue(self.Camera.cameraConfig['Imaging__laserIntensity'])
            self.ui.Imaging__laserDetuningMHz.setValue(self.Camera.cameraConfig['Imaging__laserDetuningMHz'])
            #set image array 
            self.image_shown = self.Camera.image.copy()
            #enable UI acquisition buttons
            self.setEnabledAcquisitionUIbuttons(True)
        else :
            #disable UI acquisition buttons
            self.setEnabledAcquisitionUIbuttons(False)
        # initialize Imaging object
        if hasattr(self, 'Imaging') :
            del(self.Imaging)
        self.imagingObjectInit()
        # change ROI black, red , green numbers if not the same cameras or if camera 0
        if oldCameraNumber != self.Imaging.cameraNumber :
            if self.Imaging.cameraNumber == 0 : 
                self.ui.imaging_ROIblackNumber.setValue(0)
                self.ui.imaging_ROIredNumber.setValue(0)
                self.ui.imaging_ROIgreenNumber.setValue(0)
            else :
                newROIindex = np.where(self.Imaging.ROInameTab == self.Camera.cameraConfig['defaultROIkrgnames'][0])[0]
                if len(newROIindex) > 0 :
                    self.ui.imaging_ROIblackNumber.setValue(self.Imaging.ROIarrayIndexTab[newROIindex[0]]+1)
                else :
                    self.ui.imaging_ROIblackNumber.setValue(self.Imaging.ROIarrayIndexTab[0]+1)
                newROIindex = np.where(self.Imaging.ROInameTab == self.Camera.cameraConfig['defaultROIkrgnames'][1])[0]
                if len(newROIindex) > 0 :
                    self.ui.imaging_ROIredNumber.setValue(self.Imaging.ROIarrayIndexTab[newROIindex[0]]+1)
                else :
                    self.ui.imaging_ROIredNumber.setValue(self.Imaging.ROIarrayIndexTab[0]+1)
                newROIindex = np.where(self.Imaging.ROInameTab == self.Camera.cameraConfig['defaultROIkrgnames'][2])[0]
                if len(newROIindex) > 0 :
                    self.ui.imaging_ROIgreenNumber.setValue(self.Imaging.ROIarrayIndexTab[newROIindex[0]]+1)
                else :
                    self.ui.imaging_ROIgreenNumber.setValue(self.Imaging.ROIarrayIndexTab[0]+1)
        # display connected camera
        self.ui.lcdNumber_connectedCamera.display(self.Camera._cameraNumber)
        


    '''
#####-------------------------- Define actions for gui buttons --
'''



    #################### TabWdiget leftside #####################################

    #################### Tab Camera ##########################################
    @QtCore.pyqtSlot()
    def on_pushButton_connect_camera_clicked(self):
        """Action of pushButton **Connect camera** in tab *Camera*."""
        self.camera_connector()

    @QtCore.pyqtSlot()
    def on_pushButton_take_image_clicked(self):
        """Action of pushButton **Take image** in tab *Camera*."""
        self.Camera.imageAcqLastFailed = False
        if self.Camera.triggerMode == 0: # if external trigger : rely on indicated number of triggers
            for i in range(self.ui.take_image_numberOfTriggers.value()) :
                image_i = self.Camera.grabArray()
                if self.Camera.imageAcqLastFailed :
                    self.ui.mplwidgetImage.figure.clf()
                    self.ui.mplwidgetImage.draw()
                    self.ui.mplwidgetImage.repaint()
                    return False
                if i == self.ui.take_image_shownImageNumber.value()-1 :
                    self.image_shown = image_i
        else : # if software trigger
            if self.Imaging.flushSensor : # flush sensor if asked
                self.Camera.grabArray()
                if self.Camera.imageAcqLastFailed :
                    self.ui.mplwidgetImage.figure.clf()
                    self.ui.mplwidgetImage.draw()
                    self.ui.mplwidgetImage.repaint()
                    return False
            image_taken = self.Camera.grabArray()
            if self.Camera.imageAcqLastFailed :
                self.ui.mplwidgetImage.figure.clf()
                self.ui.mplwidgetImage.draw()
                self.ui.mplwidgetImage.repaint()
                return False
            else :
                self.image_shown = image_taken
        self.ui.lcdNumber_image_mean.display(self.image_shown.mean())
        self.ui.lcdNumber_image_max.display(self.image_shown.max())
        self.ui.lcdNumber_image_mean_percent.display(100*self.image_shown.mean()/self.Camera.maxLevel)
        self.ui.lcdNumber_image_max_percent.display(100*self.image_shown.max()/self.Camera.maxLevel)
        self.ui.mplwidgetImage.figure.clf()# clear figure to avoid double scale bar 
        self.ui.mplwidgetImage.axes = self.ui.mplwidgetImage.figure.add_subplot(111)
        self.Imaging.plot_Image_on_mplwidgetImage(self.image_shown, title = 'Camera image')
        self.ui.mplwidgetImage.draw()
        self.ui.mplwidgetImage.repaint()

        
    @QtCore.pyqtSlot()
    def on_pushButton_save_image_clicked(self):
        """Action of pushButton **Save image** in tab *Camera*."""
        self.ui.mplwidgetImage.figure.savefig(os.path.join(self.dirname, self.filename \
                + '_Camera'+ str(self.Camera._cameraNumber)+'_Picture_' \
                + time.ctime().replace(' ', '_') .replace(':', '-')+ '.png'))
                                            

    #################### Image Config Exposure, Gain and Trigger ################################

    
    @QtCore.pyqtSlot()
    def on_pushButton_exposure_gain_set_clicked(self):
        """Action of pushButton **Set Exposure and Gain** in tab *Exposure and Gain*."""
        self.Camera.setExposurems(self.camera_exposurems)
        self.ui.camera_exposurems.setValue(self.Camera.exposurems)
        self.Camera.setGaindB(self.camera_gaindB)
        self.ui.camera_gaindB.setValue(self.Camera.gaindB)
        self.on_pushButton_take_image_clicked()

    @QtCore.pyqtSlot()
    def on_pushButton_exposure_auto_av_clicked(self):
        """Action of pushButton **Average auto adjust** in tab *Exposure and Gain*."""
        self.Camera.exposureLevelAutoAdjust(attemptsMax=20,Optimization = 'Average')
        self.ui.camera_exposurems.setValue(self.Camera.exposurems)
        self.ui.camera_gaindB.setValue(self.Camera.gaindB)
        self.on_pushButton_take_image_clicked()

    @QtCore.pyqtSlot()
    def on_pushButton_exposure_auto_max_clicked(self):
        """Action of pushButton **Maximum auto adjust** in tab *Exposure and Gain*."""
        self.Camera.exposureLevelAutoAdjust(attemptsMax=20,Optimization = 'Max')
        self.ui.camera_exposurems.setValue(self.Camera.exposurems)
        self.ui.camera_gaindB.setValue(self.Camera.gaindB)
        self.on_pushButton_take_image_clicked()
                
    
    #################### Tab Camera Infos  ##############################
    
    # automatic loading

    #################### Tab Regions of interest (ROIs)  ##############################
    
    @QtCore.pyqtSlot()  
    def on_pushButton_ROI_set_clicked(self):
        """Action of pushButton **Set** in tab *Analysis ROIs*."""
        #sort to get ROI listed by camera number
        self.ui.tableWidget_ROI.sortByColumn(1,0)
        self.ui.tableWidget_ROI.sortByColumn(0,0)
        #log from ui to ROIarray
        oldROIarray = self.ROIarray
        self.logROIarray_update()
        # update list of ROIs in the Imaging object from ROIarray : keep only the ones of the current camera if not 0
        if self.Imaging.cameraNumber != 0 :
            self.Imaging.set_ROIs_from_ROIarray(self.ROIarray)
            #update selected (black, red, green) ROIs numbers if camera changed or ROI numbers  changed
            newROIindex = np.where(self.Imaging.ROInameTab == oldROIarray[self.Imaging.ROIblackNumber-1,1] )[0]
            if len(newROIindex) > 0 :
                self.ui.imaging_ROIblackNumber.setValue(self.Imaging.ROIarrayIndexTab[newROIindex[0]]+1)
            else :
                self.ui.imaging_ROIblackNumber.setValue(self.Imaging.ROIarrayIndexTab[0]+1)
            newROIindex = np.where(self.Imaging.ROInameTab == oldROIarray[self.Imaging.ROIredNumber-1,1] )[0]
            if len(newROIindex) > 0 :
                self.ui.imaging_ROIredNumber.setValue(self.Imaging.ROIarrayIndexTab[newROIindex[0]]+1)
            else :
                self.ui.imaging_ROIredNumber.setValue(self.Imaging.ROIarrayIndexTab[0]+1)
            newROIindex = np.where(self.Imaging.ROInameTab == oldROIarray[self.Imaging.ROIgreenNumber-1,1] )[0]
            if len(newROIindex) > 0 :
                self.ui.imaging_ROIgreenNumber.setValue(self.Imaging.ROIarrayIndexTab[newROIindex[0]]+1)
            else :
                self.ui.imaging_ROIgreenNumber.setValue(self.Imaging.ROIarrayIndexTab[0]+1)

     
    def uiROIarrayAddRow(self, row = ['0','NEW !', '0.0', '0.0', '100.0', '100.0']):
        """Add a row to table of ROIs in GUI."""
        self.ui.tableWidget_ROI.insertRow(0)
        item = QtWidgets.QTableWidgetItem(str(int(row[0])))
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.ui.tableWidget_ROI.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem(str(row[1]))
        self.ui.tableWidget_ROI.setItem(0, 1, item)
        item = QtWidgets.QTableWidgetItem(str(float(row[2])))
        item.setTextAlignment(QtCore.Qt.AlignRight)
        self.ui.tableWidget_ROI.setItem(0, 2, item)
        item = QtWidgets.QTableWidgetItem(str(float(row[3])))
        item.setTextAlignment(QtCore.Qt.AlignRight)
        self.ui.tableWidget_ROI.setItem(0, 3, item)
        item = QtWidgets.QTableWidgetItem(str(float(row[4])))
        item.setTextAlignment(QtCore.Qt.AlignRight)
        self.ui.tableWidget_ROI.setItem(0, 4, item)
        item = QtWidgets.QTableWidgetItem(str(float(row[5])))
        item.setTextAlignment(QtCore.Qt.AlignRight)
        self.ui.tableWidget_ROI.setItem(0, 5, item)

    
    @QtCore.pyqtSlot()  
    def on_pushButton_ROI_add_clicked(self):
        """Action of pushButton **Add** in tab *Analysis ROIs*."""
        self.uiROIarrayAddRow()
        #update ROI table
        self.on_pushButton_ROI_set_clicked()


    @QtCore.pyqtSlot()  
    def on_pushButton_ROI_delete_clicked(self):
        """Action of pushButton **Delete** in tab *Analysis ROIs*."""
        descrip = self.ui.tableWidget_ROI.item(
                self.ui.tableWidget_ROI.currentRow(),1).text()
        reply = QtWidgets.QMessageBox.question(self, 'Delete ?',
            "Are you sure to delete the ROI "+descrip+" ?",
            QtWidgets.QMessageBox.Yes | 
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes :
            self.ui.tableWidget_ROI.removeRow(self.ui.tableWidget_ROI.currentRow())
            #update ROI table
            self.on_pushButton_ROI_set_clicked()
    
    
    @QtCore.pyqtSlot() 
    def on_imaging_ROIblackNumber_valueChanged(self):
        if self.Imaging.cameraNumber == 0 :
            # blocks signal to avoid infinite loop of setValue => valueChanged ...
              self.ui.imaging_ROIblackNumber.blockSignals(True)
              self.ui.imaging_ROIblackNumber.setValue(0)
              #unblock signals
              self.ui.imaging_ROIblackNumber.blockSignals(False)
        elif self.ui.imaging_ROIblackNumber.value() < 1 \
          or self.ui.imaging_ROIblackNumber.value() > self.ROIarray.shape[0] \
          or self.ROIarray[self.ui.imaging_ROIblackNumber.value()-1,0] != str(self.Imaging.cameraNumber) :
              self.Imaging.ROIblackTabIndex = 0
              self.Imaging.ROIblackNumber = self.Imaging.ROIarrayIndexTab[0]+1
              # blocks signal to avoid infinite loop of setValue => valueChanged ...
              self.ui.imaging_ROIblackNumber.blockSignals(True)
              self.ui.imaging_ROIblackNumber.setValue(self.Imaging.ROIblackNumber)
              #unblock signals
              self.ui.imaging_ROIblackNumber.blockSignals(False)
              self.ui.plot_ROIblackDescription.setText(self.ROIarray[self.Imaging.ROIblackNumber-1,1])
        else :
            self.Imaging.ROIblackNumber = self.ui.imaging_ROIblackNumber.value()
            self.Imaging.ROIblackTabIndex = np.where(self.Imaging.ROIarrayIndexTab == (self.Imaging.ROIblackNumber-1))[0][0]
            self.ui.plot_ROIblackDescription.setText(self.ROIarray[self.Imaging.ROIblackNumber-1,1])
        
    
    @QtCore.pyqtSlot() 
    def on_imaging_ROIredNumber_valueChanged(self):
        if self.Imaging.cameraNumber == 0 :
            # blocks signal to avoid infinite loop of setValue => valueChanged ...
              self.ui.imaging_ROIredNumber.blockSignals(True)
              self.ui.imaging_ROIredNumber.setValue(0)
              #unblock signals
              self.ui.imaging_ROIredNumber.blockSignals(False)
        elif self.ui.imaging_ROIredNumber.value() < 1 \
          or self.ui.imaging_ROIredNumber.value() > self.ROIarray.shape[0] \
          or self.ROIarray[self.ui.imaging_ROIredNumber.value()-1,0] != str(self.Imaging.cameraNumber) :
              self.Imaging.ROIredTabIndex = 0
              self.Imaging.ROIredNumber = self.Imaging.ROIarrayIndexTab[0]+1
              # blocks signal to avoid infinite loop of setValue => valueChanged ...
              self.ui.imaging_ROIredNumber.blockSignals(True)
              self.ui.imaging_ROIredNumber.setValue(self.Imaging.ROIredNumber)
              #unblock signals
              self.ui.imaging_ROIredNumber.blockSignals(False)
              self.ui.plot_ROIredDescription.setText(self.ROIarray[self.Imaging.ROIredNumber-1,1])
        else :
            self.Imaging.ROIredNumber = self.ui.imaging_ROIredNumber.value()
            self.Imaging.ROIredTabIndex = np.where(self.Imaging.ROIarrayIndexTab == (self.Imaging.ROIredNumber-1) )[0][0]
            self.ui.plot_ROIredDescription.setText(self.ROIarray[self.Imaging.ROIredNumber-1,1])
    
    
    @QtCore.pyqtSlot() 
    def on_imaging_ROIgreenNumber_valueChanged(self):
        if self.Imaging.cameraNumber == 0 :
            # blocks signal to avoid infinite loop of setValue => valueChanged ...
              self.ui.imaging_ROIgreenNumber.blockSignals(True)
              self.ui.imaging_ROIgreenNumber.setValue(0)
              #unblock signals
              self.ui.imaging_ROIgreenNumber.blockSignals(False)
        elif self.ui.imaging_ROIgreenNumber.value() < 1 \
          or self.ui.imaging_ROIgreenNumber.value() > self.ROIarray.shape[0] \
          or self.ROIarray[self.ui.imaging_ROIgreenNumber.value()-1,0] != str(self.Imaging.cameraNumber) :
              self.Imaging.ROIgreenTabIndex = 0
              self.Imaging.ROIgreenNumber = self.Imaging.ROIarrayIndexTab[0]+1
              # blocks signal to avoid infinite loop of setValue => valueChanged ...
              self.ui.imaging_ROIgreenNumber.blockSignals(True)
              self.ui.imaging_ROIgreenNumber.setValue(self.Imaging.ROIgreenNumber)
              #unblock signals
              self.ui.imaging_ROIgreenNumber.blockSignals(False)
              self.ui.plot_ROIgreenDescription.setText(self.ROIarray[self.Imaging.ROIgreenNumber-1,1])
        else :
            self.Imaging.ROIgreenNumber = self.ui.imaging_ROIgreenNumber.value()
            self.Imaging.ROIgreenTabIndex = np.where(self.Imaging.ROIarrayIndexTab == (self.Imaging.ROIgreenNumber-1))[0][0]
            self.ui.plot_ROIgreenDescription.setText(self.ROIarray[self.Imaging.ROIgreenNumber-1,1])

    #################### TabWidget rightside ###################################

    #################### Tab Imaging ########################################
    @QtCore.pyqtSlot()
    def on_imaging_averages_valueChanged(self):
        self.Imaging.averages = self.ui.imaging_averages.value()
        self.Imaging.cycles = self.Imaging.averages*self.Imaging.scans
        self.ui.lcdNumber_imaging_cycles.display(self.Imaging.cycles)
        
    @QtCore.pyqtSlot()
    def on_imaging_scans_valueChanged(self):
        self.Imaging.scans = self.ui.imaging_scans.value()
        self.Imaging.cycles = self.Imaging.averages*self.Imaging.scans
        self.ui.lcdNumber_imaging_cycles.display(self.Imaging.cycles)
    
    @QtCore.pyqtSlot()
    def on_pushButton_imaging_start_measurement_clicked(self):
        """Action of pushButton **Start measurement** in tab *Imaging*."""
        self.imagingObjectInit()
        self.Imaging.imaging_scan(self.Camera,self.ui)
        if self.Imaging.scanDone and self.saveload_autoSaveMeas :
            self.save_imaging()
 
    #################### Tab Temperature  ############################################

    @QtCore.pyqtSlot()
    def on_imaging_T_averages_valueChanged(self):
        self.Imaging.T_averages = self.ui.imaging_T_averages.value()
        self.Imaging.T_cycles = self.Imaging.T_averages*self.Imaging.T_TOFscans*self.Imaging.T_scans
        self.ui.lcdNumber_imaging_T_cycles.display(self.Imaging.T_cycles)
        
    @QtCore.pyqtSlot()
    def on_imaging_T_TOFscans_valueChanged(self):
        self.Imaging.T_TOFscans = self.ui.imaging_T_TOFscans.value()
        self.Imaging.T_cycles = self.Imaging.T_averages*self.Imaging.T_TOFscans*self.Imaging.T_scans
        self.ui.lcdNumber_imaging_T_cycles.display(self.Imaging.T_cycles)
        
    @QtCore.pyqtSlot()
    def on_imaging_T_scans_valueChanged(self):
        self.Imaging.T_scans = self.ui.imaging_T_scans.value()
        self.Imaging.T_cycles = self.Imaging.T_averages*self.Imaging.T_TOFscans*self.Imaging.T_scans
        self.ui.lcdNumber_imaging_T_cycles.display(self.Imaging.T_cycles)
    
    @QtCore.pyqtSlot()
    def on_pushButton_start_temp_measurement_clicked(self):
        """Action of pushButton **Start Temperature measurement** in tab *Temperature*."""
        self.imagingObjectInit()
        self.Imaging.temperature_measurement_scan(self.Camera, self.ui)
        if self.Imaging.scanDone and self.saveload_autoSaveMeas :
            self.save_imaging()
    
     #################### Tab Lifetime  ############################################

    @QtCore.pyqtSlot()
    def on_imaging_LT_averages_valueChanged(self):
        self.Imaging.LT_averages = self.ui.imaging_LT_averages.value()
        self.Imaging.LT_cycles = self.Imaging.LT_averages*self.Imaging.LT_Tscans*self.Imaging.LT_scans
        self.ui.lcdNumber_imaging_LT_cycles.display(self.Imaging.LT_cycles)
        
    @QtCore.pyqtSlot()
    def on_imaging_LT_Tscans_valueChanged(self):
        self.Imaging.LT_Tscans = self.ui.imaging_LT_Tscans.value()
        self.Imaging.LT_cycles = self.Imaging.LT_averages*self.Imaging.LT_Tscans*self.Imaging.LT_scans
        self.ui.lcdNumber_imaging_LT_cycles.display(self.Imaging.LT_cycles)
        
    @QtCore.pyqtSlot()
    def on_imaging_LT_scans_valueChanged(self):
        self.Imaging.LT_scans = self.ui.imaging_LT_scans.value()
        self.Imaging.LT_cycles = self.Imaging.LT_averages*self.Imaging.LT_Tscans*self.Imaging.LT_scans
        self.ui.lcdNumber_imaging_LT_cycles.display(self.Imaging.LT_cycles)
    
    @QtCore.pyqtSlot()
    def on_pushButton_start_LT_measurement_clicked(self):
        """Action of pushButton **Start Lifetime measurement** in tab *Lifetime*."""
        self.imagingObjectInit()
        self.Imaging.lifetime_measurement_scan(self.Camera, self.ui)
        if self.Imaging.scanDone and self.saveload_autoSaveMeas :
            self.save_imaging()
    
    #################### Tab Plot  ############################################
    
    @QtCore.pyqtSlot()
    def on_pushButton_plotAnalysis_update_clicked(self):
        """Action of pushButton **Update** in tab *Plot*."""
        self.Imaging.plotAnalysis_update()
    
    #################### Tab Analysis Results #################################

    @QtCore.pyqtSlot()
    def on_pushButton_print_imaging_object_as_dict_clicked(self):
        """Action of pushButton **Print** in tab *Analysis results*."""
        self.ui.textBrowser_analyse_dictionary.setText(self.print_dict(vars(self.Imaging)))

    
    #################### Tab Save #############################################

    @QtCore.pyqtSlot()
    def on_pushButton_save_choose_dir_clicked(self):
        """Action of pushButton **Choose Directory** in tab *Save/Load*."""
        dirname = str(QtWidgets.QFileDialog.getExistingDirectory(self,
                "Save to :", "",
                QtWidgets.QFileDialog.ShowDirsOnly | \
                QtWidgets.QFileDialog.DontResolveSymlinks))
        self.changeDirectory(dirname)

    @QtCore.pyqtSlot()
    def on_pushButton_save_imagingObject_clicked(self):
        """Action of pushButton **Save Imaging Results** in tab *Save/Load*."""
        self.save_imaging()
    
    @QtCore.pyqtSlot()
    def on_saveload_autoSaveMeas_stateChanged(self):
        self.saveload_autoSaveMeas = self.ui.saveload_autoSaveMeas.isChecked()
        if self.saveload_autoSaveMeas :
            self.ui.Imaging__autoSaveImages.setEnabled(True)
        else : 
            self.ui.Imaging__autoSaveImages.setEnabled(False)
            self.ui.Imaging__autoSaveImages.setChecked(False)

    @QtCore.pyqtSlot()
    def on_pushButton_load_imagingObject_clicked(self):
        """Action of pushButton **Load Imaging Results** in tab *Save/Load*."""
        dirAndFileName_loaded = str(QtWidgets.QFileDialog.getOpenFileName(self, 
                "Load from :",
                self.dirname, 
                "Imaging object only (*.imo)")[0])
        if dirAndFileName_loaded:
            [dirname, filename] = os.path.split(dirAndFileName_loaded)
            self.dirname = os.path.normpath(dirname)
            self.filename = filename[:-4]
            os.chdir(self.dirname)
            self.ui.label_save_ImagingObject_file.setText(
                    os.path.join(self.dirname, self.filename))
            self.load_imaging()
            
    #################### Tab Scripting ########################################

    @QtCore.pyqtSlot()
    def on_pushButton_loadScript_clicked(self):
        """Action of pushButton **Load script** in tab *Scripting*."""
        dirAndFileName_loaded = str(QtWidgets.QFileDialog.getOpenFileName(self, 
                "Load from :",
                os.path.join(scriptDirPath, 'Scripts'),
                "Python files only (*.py);; All files (*.*)")[0])
        if dirAndFileName_loaded:
            self.scriptFilename1 = dirAndFileName_loaded
            self.ui.label_scriptFile1.setText(dirAndFileName_loaded)
            self.ui.pushButton_reloadRunScript1.setText('Reload and Run: ' + os.path.split(dirAndFileName_loaded)[-1])

    @QtCore.pyqtSlot()
    def on_pushButton_reloadRunScript_clicked(self):
        """Action of pushButton **Reload and Run Script** in tab *Scripting*."""
        f = open(self.scriptFilename1, 'rb')
        script = f.read()
        f.close()
        self.ui.label_scriptFile1.setText(self.scriptFilename1)
        exec(script)


    @QtCore.pyqtSlot()
    def on_pushButton_closeFigures_clicked(self):
        """Action of pushButton **Close figures** in tab *Scripting*."""
        plt.close('all')


'''
################################################## Starting the Program ..... ##
'''     

scriptDirPath = os.path.abspath('.')
print("Program directory path :", scriptDirPath)
  
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    mainWin = MainWindow()
    mainWin.show()
    #check if IPython console, if yes set for interaction with console
    try :  
        from IPython import get_ipython
        ipython = get_ipython()
    except :
        ipython = None
    if ipython is None :
        sys.exit(app.exec_()) 
    # sys.exit(app.exec_()) 







