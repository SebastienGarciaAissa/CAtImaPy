# -*- coding: utf-8 -*-

"""
Define camera driver classes for Thorlabs cameras via pylablibInterface
"""

import numpy as np
from .PylablibInterfaceClassDef import PylablibInterfaceClass

try : 
    from pylablib.devices import uc480
    pylablibUC480DriverInstalled = True
except :
    print('ERROR ! : Tried to load pylablib Thorlabs driver, but it is not installed')
    pylablibUC480DriverInstalled = False

class IDSueyeClass(PylablibInterfaceClass) :
    """Parent class for all camera IDSueye classes using pylablib python driver.
    
    Used as generic driver class if no model-specific child class is defined in same file below"""
        
    def __init__(self, cameraNumber, triggerMode=0, exposurems=1, 
                 gaindB=1, camROI=None, loadDefault = False) :	
        """Initialize the Camera object 
        
        Args:
            cameraNumber (int) : index of camera in camerasConfigs list
            
        Keyword Args:
            triggerMode=0  (int) : 0 for hardware/external, 1 for software/internal
            
            exposurems=1. (float) : Exposition duration (exposure) in ms.
            
            gaindB=0. (float) : hardware gain of the camera in dB.
            
            camROI=None (None or [int]*4) : Camera region of interest to read from sensor
                [x offset , y offset , x size , y size ] (binning is not implemented)
            
            loadDefault = True  (bool): Decide if default values from cameraConfigs should be set at creation 
                        
        Return: 
            IDSueyeClass camera object
        """
        super().__init__(cameraNumber, triggerMode=triggerMode, exposurems=exposurems,
                          gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)
        #check if pylablib and pylablib UC480 ( UC480 thorlabs cameras are IDS ueye camera) are installed, if no return
        if not(self.cameraDriverInstalled) or not(pylablibUC480DriverInstalled) :
            self.cameraDriverInstalled = False
            return 
        # check if camera is here 
        if not( str(self.cameraConfig['serial']) in [info.serial_number for info in uc480.list_cameras(backend="ueye")] )  :
            print('ERROR ! : Could not find camera '+str(cameraNumber)+' with its serial number among connected cameras')
            return 
        # here is the main camera object that will be used to access camera via driver
        try : 
            self.pylablibCamera = uc480.UC480Camera(dev_id = uc480.find_by_serial(str(self.cameraConfig['serial']), backend="ueye"), backend="ueye")
        except :
            print('ERROR ! : Could not connect camera '+str(cameraNumber))
            return 
        #checked if connected
        if not(self.pylablibCamera.is_opened()) :
            print('ERROR ! : Could not connect camera '+str(cameraNumber))
            return 
        # set bitdepth 
        self.imageBitDepth = int(self.cameraConfig['imageBitDepth']) 
        if self.imageBitDepth <= 8 :
            self.imageDtype = np.uint8
            self.pylablibCamera.set_color_mode("mono8")
        elif self.imageBitDepth <= 16 :
            self.imageDtype = np.uint16
            self.pylablibCamera.set_color_mode("mono16")
        else : 
            print('ERROR ! : Camera bit depth set larger than 16 !')
            return
        # set trigger mode
        self.pylablibCamera.lib.is_SetExternalTrigger(self.pylablibCamera.hcam, uc480.uc480_defs.TRIGGER.IS_SET_TRIGGER_LO_HI)
        self.setTriggerMode(self.triggerMode)
        #get min and max exposure and Set of exposure
        exposuremsset = self.exposurems
        try :
            self.setExposurems(1.e-6) # we don't need less than that for cold atom imaging
            self.exposuremsMin = self.exposurems
            self.setExposurems(1.e3) # we don't need more than that for cold atom imaging
            self.exposuremsMax = self.exposurems
        except :
            self.exposuremsMin = 1.e-6
            self.exposuremsMax = 1.e3
        self.setExposurems(exposuremsset)
        # gaindB is set at 0 for these cameras , it could be set but it is a mess because setting is done between 0 and 100 % 
        self.gaindBMin, self.gaindBMax = (0.,0.)
        self.gaindB = 0.
        # set camera ROI, 
        self.setCamROI(ROI=self.camROI)
        # numpy image array
        self.imageSize = (self.hpx,self.wpx)
        self.image = np.array(self.imageSize, dtype=self.imageDtype)
        # image scaling and properties
        self.pixelCalXumperpx = self.cameraConfig['pixelCalXumperpx']
        self.pixelCalYumperpx = self.cameraConfig['pixelCalYumperpx']
        self.reversedAxes = self.cameraConfig['reversedAxes']
        self.maxLevel = 2**self.imageBitDepth - 1
        self.imageLimits = [-self.wpx/2*self.pixelCalXumperpx,
                            self.wpx/2*self.pixelCalXumperpx,
                            -self.hpx/2*self.pixelCalYumperpx,
                            self.hpx/2*self.pixelCalYumperpx]
        #start acquisition
        self.startAcquisition()
        self.cameraConnected = True
        
    
    def __del__(self) : 
        """Delete the Camera object by calling close function
        
        Close the Camera and free memory"""
        super().__del__() #ALWAYS call at end of any child class del
        
        
    def setTriggerMode(self, triggerMode):
        """Set the trigger mode 
        
        Args:
            triggerMode (int) :  0 for hardware/external, 1 for software/internal
        """
        # here do nothing on the trigger setting because in external mode, can still force software trigger 
        # on the contrary in software mode , the exposure is triggerred automatically at acquisition start
        self.triggerMode = triggerMode
        if not(triggerMode==0) or not(triggerMode==1) : 
            raise NameError('Trigger mode number not defined ')
    
    
    def sendSoftwareTrigger(self):
        """Send a software trigger to the camera to start an exposure"""
        self.pylablibCamera.lib.is_ForceTrigger(self.pylablibCamera.hcam)
    
    
    def setGaindB(self, gaindB) :
        """Set the hardware gain of camera readout
        WARNING : Not Defined for ThorlabsUC480Class camera . 
        
        Args:
            gaindB (float) : hardware gain of the camera in dB.
        """
        print("Warning  : setGaindB Not Defined for ThorlabsUC480Class camera.")
        self.gaindB = 0


    def startAcquisition(self):
        """Start acquisition or restart if already running """
        # common to Icamera interface but args,kwargs depend on camera driver/model
        self.pylablibCamera.start_acquisition(frames_per_trigger=1, auto_start=False, nframes=20) #set buffer size to 20











