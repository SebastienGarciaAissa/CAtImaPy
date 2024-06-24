# -*- coding: utf-8 -*-

"""
Define camera driver classes for Thorlabs cameras via pylablibInterface
"""

import numpy as np
from .PylablibInterfaceClassDef import PylablibInterfaceClass

try : 
    from pylablib.devices import DCAM
    pylablibDCAMdriverInstalled = True
except :
    print('ERROR ! : Tried to load pylablib Hamamatsu DCAM driver, but it is not installed')
    pylablibDCAMdriverInstalled = False

class HamamatsuDCAMClass(PylablibInterfaceClass) :
    """Parent class for all camera Hamamatsu DCAM classes using pylablib python driver.
    
    Used as generic driver class if no model-specific child class is defined in same file below"""
        
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
            HamamatsuDCAMClass camera object
        """
        super().__init__(cameraNumber, triggerMode=triggerMode, exposurems=exposurems,
                          gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)
        #check if pylablib and pylablib DCAM are installed, if no return
        if not(self.cameraDriverInstalled) or not(pylablibDCAMdriverInstalled) :
            self.cameraDriverInstalled = False
            return 
        if int(self.cameraConfig['serial']) >= DCAM.get_cameras_number() :
            print('ERROR ! : HamamatsuDCAM Camera serial in cameraConfig should correspond to a valid camera index (< Number of Hamamatsu cameras)')
            return
        try : 
            self.pylablibCamera = DCAM.DCAMCamera(idx=int(self.cameraConfig['serial']) )
        except :
            print('ERROR ! : Could not connect camera '+str(cameraNumber))
            return 
        #checked if could connect the right camera
        if not(self.pylablibCamera.is_opened()) :
            print('ERROR ! : Could not connect camera '+str(cameraNumber))
            return 
        # set bitdepth as the one obtained from camera (can not change the image format)
        self.imageBitDepth = int(self.pylablibCamera.get_attribute_value("BIT PER CHANNEL",default=8))
        if self.imageBitDepth != int(self.cameraConfig['imageBitDepth']) :
            print('Warning ! : Overwrite Camera.imageBitDepth with the one abtained from HamamatsuDCAM camera S/N '+str(self.cameraConfig['serial']))
        if self.imageBitDepth <= 8 :
            self.imageDtype = np.uint8
        elif self.imageBitDepth <= 16 :
            self.imageDtype = np.uint16
        elif self.imageBitDepth <= 32:
            self.imageDtype = np.uint32
        else : 
            print('ERROR ! : Camera return bit depth larger than 32 !')
            return
        # set trigger mode
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
        
        Args:
            triggerMode (int) :  0 for hardware/external, 1 for software/internal
        """
        # common to Icamera interface but args,kwargs depend on camera driver/model
        self.triggerMode = triggerMode
        if triggerMode==0:#'external'
            self.pylablibCamera.set_trigger_mode('ext')
        elif triggerMode==1:#'software'
            self.pylablibCamera.set_trigger_mode('software')
        else : raise NameError('Trigger mode number not defined ')
        self.startAcquisition() # restart acquisition because 'int' reset auto_start=True otherwise
    
    
    def sendSoftwareTrigger(self):
        """Send a software trigger to the camera to start an exposure"""
        self.pylablibCamera.send_software_trigger()
        
    
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





class ExampleModelClass(HamamatsuDCAMClass) :
    """Model-specific class for ... Hamamatsu camera using pylablib python driver.
    
        Child Class of HamamatsuDCAMClass. 
        Use to implement specific initialization for this camera model"""
        
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
            ExampleModelClass camera object
        """
        super().__init__(cameraNumber, triggerMode=triggerMode, exposurems=exposurems,
                          gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)
        
    
    def __del__(self) : 
        """Delete the Camera object by calling close function
        
        Close the Camera and free memory"""
        super().__del__() #ALWAYS call at end of any child class del



























