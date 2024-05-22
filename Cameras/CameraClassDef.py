# -*- coding: utf-8 -*- 

"""
Define generic camera driver class CameraClass
"""

import numpy as np
from .Config import camerasConfigs

class CameraClass: 
    """Top Parent Class for controlling camera : used as an interface"""
    
    def __init__(self, cameraNumber, triggerMode=0, exposurems=1., gaindB=0., camROI=None, loadDefault=False ):
        """Initialize the Camera object 
        
        Args:
            cameraNumber (int) : index of camera in camerasConfigs list
            
        Keyword Args:
            triggerMode  (int) : 0 for hardware/external, 1 for software/internal
            
            exposurems (float) : Exposition duration (exposure) in ms.
            
            gaindB (float) : hardware gain of the camera in dB.
            
            camROI (None or [int]*4) : Camera region of interest to read from sensor
                [x offset , y offset , x size , y size ] (binning is not implemented)
            
            loadDefault  (bool): Decide if default values from cameraConfigs should be set at creation 
            
        Return: 
            CameraClass object
        """
        self.cameraDriverInstalled = False
        self.cameraConnected = False
        # define common variables of acquisition
        self._cameraNumber = cameraNumber
        if self._cameraNumber > len(camerasConfigs)-1 :
            raise NameError('Camera number higher than config array')
        elif camerasConfigs[self._cameraNumber] is None :
            if self._cameraNumber > 0 :
                print('ERROR ! : No config for this camera number')
            self.cameraConfig = camerasConfigs[self._cameraNumber]
        else : 
            self.cameraConfig = camerasConfigs[self._cameraNumber]       
            if ('defaultTrigger' in self.cameraConfig) and loadDefault :
                if self.cameraConfig['defaultTrigger'] == 'external':
                    triggerMode = 0
                else : triggerMode = 1
            if ('defaultGaindB' in self.cameraConfig) and loadDefault:
                gaindB = self.cameraConfig['defaultGaindB']
            if ('defaultExposurems' in self.cameraConfig) and loadDefault:
                exposurems = self.cameraConfig['defaultExposurems']
            if ('defaultCamROI' in self.cameraConfig) and loadDefault:
                camROI = self.cameraConfig['defaultCamROI']
        self.triggerMode = triggerMode #  0='external' , 1='software'
        self.triggerModeTextList = ['external','software']
        self.gaindB = gaindB #gain of the camera in dB
        self.gaindBMin = None # minimum gain in dB
        self.gaindBMax = None # maximum gain in dB
        self.exposurems = exposurems # exposure in milliseconds 
        self.exposuremsMin = None 
        self.exposuremsMax = None
        self.exposureAutoAvLevel = None
        self.exposureAutoAvRange = None
        self.exposureAutoMaxLevel = None
        self.exposureAutoMaxRange = None
        self.exposureIncreaseHardwareGain = None
        self.timeout = 10 #timeout in seconds
        self.imageAcqLastFailed = False
        # image size
        self.wpxmax = 1 # width max of camera
        self.hpxmax = 1 # height max of camera
        self.wpx = self.wpxmax # width of camera
        self.hpx = self.hpxmax # height of camera
        self.camROI = camROI #Camera region of interest (read part of sensor) [OffsetX, OffsetY, Width, Height]
        self.imageSize = (self.hpx,self.wpx) #in numpy axes are reversed
        self.pixelCalXumperpx = 1. # calibration from pixels to micrometers along X axis
        self.pixelCalYumperpx = 1. # calibration from pixels to micrometers along Y axis
        self.imageLimits = [-self.wpx/2*self.pixelCalXumperpx,
                            self.wpx/2*self.pixelCalXumperpx,
                            -self.hpx/2*self.pixelCalYumperpx,
                            self.hpx/2*self.pixelCalYumperpx] # in micrometers
        self.reversedAxes = [False,False]
        #image arrays
        self.imageBitDepth = 8 # read sensor bit depth
        self.maxLevel = 2**self.imageBitDepth - 1
        self.imageDtype = np.uint8 # image bith depth (dtype in numpy) : typically 8 or 16 bits => uint8 or uint16
        self.image = np.array(self.imageSize, dtype=self.imageDtype) #last image taken
        self._image = np.array(self.imageSize, dtype=self.imageDtype) #PROTECTED pointer for loading camera image 
        

    def __del__(self):
        """Delete the Camera object by calling close function
        
        Close the Camera and free memory"""
        del(self._image, self.image)        
        
        
    def setTriggerMode(self, triggerMode):
        """Set the trigger mode 
        
        Args:
            triggerMode (int) :  0 for hardware/external, 1 for software/internal
        """
        raise NotImplementedError('Funtion SetTriggerMode not defined')
        
        
    def sendSoftwareTrigger(self):
        """Send a software trigger to the camera to start an exposure"""
        raise NotImplementedError('Funtion sendSoftwareTrigger not defined') 
        
        
    def setExposurems(self,exposurems):
        """Set the duration of the exposition 
        
        Args:
            exposurems (float) : Exposition duration (exposure) in ms.
        """
        raise NotImplementedError('Function setExposure not defined')
        
        
    def setGaindB(self,gaindB):
        """Set the hardware gain of camera readout
        
        Args:
            gaindB (float) : hardware gain of the camera in dB.
        """
        raise NotImplementedError('Function setGaindB not defined')
        
        
    def setCamROI(self, ROI=None) :
        """Set the ROI of camera (without binning)
        
        Keyword Args:
            ROI ( None or [int]*4) : [ x offset, y offset, x size, y size],
                if None, set to [0, 0, max Width, max height]
            
        Return: 
            Camera ROI ([int]*4) : [x offset, y offset, x size, y size]
        """
        raise NotImplementedError('Function setCamROI not defined')
    
    
    def startAcquisition(self):
        """Start acquisition or restart if already running """
        raise NotImplementedError('Function startAcquisition not defined')
    
    
    def clearBuffer(self) :
        """ Clear camera buffer from images. 
        Use before imaging scans to make sure no previously acquired image is present in buffer"""
        raise NotImplementedError('Function startAcquisition not defined')
    
        
    def grabArray(self):
        """Get an image from the camera. 
        Wait for trigger if external or generate one if internal.
            
        Return: 
            Camera image (numpy 2D array)
        """
        raise NotImplementedError('Function grabArray not defined')
        
        
    def exposureLevelAutoAdjust(self, attemptsMax=20, Optimization = 'Max'):
        """Automatic adjustment of exposure for setting image 'Max' or 'Average' to a given level.
        
            Can use  gaindB increase to reach specified level  if maximum exposure is not sufficient.
            
        Keyword Args:
            attemptsMax (int) : Maximum number of steps (images) in optimization
            
            Optimization (str) : Select image value to optimize 'Max' or 'Average'
        
        Return: 
            Optimized image value (int)          
        """
        self.setGaindB(0)
        attempts = 0
        image = self.grabArray()
        if self.imageAcqLastFailed :
            return False
        else :
            if Optimization == 'Average':
                level = self.exposureAutoAvLevel/100. * self.maxLevel
                acceptedRange = self.exposureAutoAvRange/100. * self.maxLevel
                imageValue = image.mean()
            elif Optimization == 'Max':
                level = self.exposureAutoMaxLevel/100. * self.maxLevel
                acceptedRange = self.exposureAutoMaxRange/100. * self.maxLevel
                imageValue = image.max()
            else : 
                raise NameError('Optimisation criterion not defined in exposureLevelAutoAdjust')
            exposure = self.exposurems
            old_exposure = 0.
            new_exposure = 0.
            while abs(imageValue - level) > acceptedRange \
                    and attempts < attemptsMax:
                if new_exposure < self.exposuremsMin \
                        and old_exposure == exposure:
                    print("WARNING ! : Camera : exposureLevelAutoAdjust \n"\
                            + "Could not adjust exposure to specified level \n"\
                            + "Ideal point lower than exposure minimum")
                    break
                if new_exposure > self.exposuremsMax \
                        and old_exposure == exposure:
                    if self.increaseGain : 
                        if self.gaindB > (self.gaindBMax-0.1) :
                            print("WARNING ! : Camera : exposureLevelAutoAdjust"\
                                    +"\n Could not adjust exposure to specified" \
                                    +"max level \n Ideal point Higher than "\
                                    +"exposure maximum\n Maximum hardware gain"\
                                    +"was used")
                            break
                        else:                    
                            self.setGaindB(self.gaindB + 3)
                            old_exposure = 0.
                            continue
                    else :
                        print("WARNING !: Camera : exposure_max_level_auto_adjust"\
                                +"\n Could not adjust exposure to specified level"\
                                +"level \n Ideal point Higher than exposure"\
                                +"maximum\n Consider increasing hardware gain")
                        break  
                attempts += 1
                self.setExposurems(new_exposure)
                exposure =  self.exposurems
                # return previous image sometime (unknow reason)
                image = self.grabArray()
    
                if Optimization == 'Average':
                    imageValue = image.mean()
                elif Optimization == 'Max':
                    imageValue = image.max()
                if imageValue == self.maxLevel :
                    new_exposure = exposure/4.
                else :
                    new_exposure = exposure * level / (imageValue+ 0.01)
            if attempts == attemptsMax :
                print("WARNING ! : Camera : exposure_max_level_auto_adjust \n"\
                        +"Could not adjust exposure to specified max level")
                return False
            return imageValue
        
