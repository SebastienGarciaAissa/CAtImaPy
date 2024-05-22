# -*- coding: utf-8 -*-

"""
Define camera driver classes for Thorlabs cameras via pylablibInterface
"""

import numpy as np
from .PylablibInterfaceClassDef import PylablibInterfaceClass

try : 
    from pylablib.devices import IMAQdx
    pylablibIMAQdxDriverInstalled = True
except :
    print('ERROR ! : Tried to load pylablib NIIMAQdx driver, but it is not installed')
    pylablibIMAQdxDriverInstalled = False

class NIIMAQdxClass(PylablibInterfaceClass) :
    """Parent class for all camera NIIMAQdx classes using pylablib python driver.
    
     => NEED a model-specific child class defined in same file below"""
        
    def __init__(self, cameraNumber, triggerMode=0, exposurems=1, 
                 gaindB=1, camROI=None, loadDefault = False) :	
        """Initialize the Camera object 
        
        Warning: 
            Contrary to other camera driver allowing for search of a camera with serial number,
            HERE cameraConfig['serial'] is passed as the camera index assigned by AndorSDK.
            Hopefully this won't change from day to day but this could be an issue. 
            If this is an issue, modify the initalization procedure to connect and grab serial until found.
            Contact developper if you can't solve this by yourself.
        
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
            NIIMAQdxClass camera object
        """
        super().__init__(cameraNumber, triggerMode=triggerMode, exposurems=exposurems,
                          gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)
        #check if pylablib and pylablib DCAM are installed, if no return
        if not(self.cameraDriverInstalled) or not(pylablibIMAQdxDriverInstalled) :
            self.cameraDriverInstalled = False
            return 
        if not str(self.cameraConfig['serial']) in IMAQdx.list_cameras() :
            print('ERROR ! : IMAQdx Camera serial in cameraConfig should correspond to a valid camera name of IMAQdx.list_cameras')
            return
        try : 
            self.pylablibCamera = IMAQdx.IMAQdxCamera(str(self.cameraConfig['serial']) )
        except :
            print('ERROR ! : Could not connect camera '+str(cameraNumber))
            return 
        #checked if could connect the right camera
        if not(self.pylablibCamera.is_opened()) :
            print('ERROR ! : Could not connect camera '+str(cameraNumber))
            return 
        # set bitdepth as the one obtained from camera (can not change the image format)
        self.imageBitDepth = int(self.cameraConfig['imageBitDepth'])
        if self.imageBitDepth <= 8 :
            self.pylablibCamera.set_attribute_value("PixelFormat", "Mono8")
            self.imageDtype = np.uint8
        elif self.imageBitDepth <= 16 :
            self.pylablibCamera.set_attribute_value("PixelFormat", "Mono16")
            self.imageDtype = np.uint16
        elif self.imageBitDepth <= 32:
            self.pylablibCamera.set_attribute_value("PixelFormat", "Mono32")
            self.imageDtype = np.uint32
        else : 
            print('ERROR ! : Camera return bit depth larger than 32 !')
            return
        # set trigger mode
        self.setTriggerMode(self.triggerMode)
        #get min and max exposure and Set of exposure
        self.exposuremsMin = self.pylablibCamera.get_attribute("AcquisitionControl/ExposureTime").min
        self.exposuremsMax = self.pylablibCamera.get_attribute("AcquisitionControl/ExposureTime").max
        self.setExposurems(exposurems)
        # gaindB is set at 0 for these camera
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
            WARNING : Need to be defined specifically for camera model in a child class !
        
        Args:
            triggerMode (int) :  0 for hardware/external, 1 for software/internal
        """
        raise NotImplementedError('Funtion SetTriggerMode not defined') 
    
    def sendSoftwareTrigger(self):
        """Send a software trigger to the camera to start an exposure
            WARNING : Need to be defined specifically for camera model in a child class !
        """
        raise NotImplementedError('Funtion sendSoftwareTrigger not defined') 
    
    def setExposurems(self, exposurems) :
        """Set the duration of the exposition 
        
        Args:
            exposurems (float) : Exposition duration (exposure) in ms.
        """
        self.pylablibCamera.set_attribute_value("AcquisitionControl/ExposureTime", 1e3*exposurems)
        self.exposurems = 1e-3 * self.pylablibCamera.get_attribute_value("AcquisitionControl/ExposureTime")
        
    
    def setGaindB(self, gaindB) :
        """Set the hardware gain of camera readout
        WARNING : Not Defined for AndorSDK2 camera. 
        EMCCD Gain (if pertinent) can be set in cameraConfig as 'EMCCDgain'.
        
        Args:
            gaindB (float) : hardware gain of the camera in dB.
        """
        print("Warning  : setGaindB Not Defined for AndorSDK2 camera.\n EMCCD Gain (if pertinent) can be set in cameraConfig as 'EMCCDgain'.")
        self.gaindB = 0


    def startAcquisition(self):
        """Start acquisition or restart if already running """
        # common to Icamera interface but args,kwargs depend on camera driver/model
        self.pylablibCamera.setup_acquisition(mode="sequence", nframes=20) #set buffer size to 20
        self.pylablibCamera.start_acquisition(frames_per_trigger=1, auto_start=False, nframes=20) #set buffer size to 20





























