# -*- coding: utf-8 -*- 

"""
Define camera driver classes for FLIR cameras
"""

import numpy as np
from .CameraClassDef import CameraClass

# PySpin driver for FLIR cameras
try : 
    import PySpin 
    PySpinDriverInstalled = True
except :
    print('ERROR ! : Tried to load PySpin driver, but it is not installed')
    PySpinDriverInstalled = False


class FLIRPySpinClass(CameraClass) :
    """Parent class for FLIR cameras using PySpin python driver.
    
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
            FLIRPySpinClass camera object
        """
        super().__init__(cameraNumber, triggerMode=triggerMode, exposurems=exposurems,
                         gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)
        #check if driver installed, if no return
        self.cameraDriverInstalled = PySpinDriverInstalled 
        if not(self.cameraDriverInstalled) :
            print('ERROR ! : PySpin driver is not installed')
            return
        #init PySpin.System object and get camera list
        self.camSystem = PySpin.System.GetInstance()
        self.camList = self.camSystem.GetCameras()
        # here is the main camera object that will be used to access camera via driver
        # get serial number of camera to use from cameraConfig and pick the right camera in list
        self.pySpinCamera = self.camList.GetBySerial(str(self.cameraConfig['serial']))
        if not(self.pySpinCamera.IsValid()) :
            print('ERROR ! : Could not connect camera '+str(cameraNumber)+' (maybe check serial number)')
            return
        #connect camera
        self.pySpinCamera.Init()
        # # get camera and transport interfaces node maps to access to advanced features
        # self.pySpinNodeMap = self.pySpinCamera.GetNodeMap()
        # self.pySpinStreamNodeMap = self.pySpinCamera.GetTLStreamNodeMap()
        # set mode bit depth for image mono 8 or mono 16 depending on cameraCOnfig imageBitDepth
        self.imageBitDepth = int(self.cameraConfig['imageBitDepth']) 
        if self.imageBitDepth <= 8 :
            self.pySpinCamera.PixelFormat.SetValue(PySpin.PixelFormat_Mono8)
            self.imageDtype = np.uint8
            self.imageBitsToShift = int(8 - self.imageBitDepth) # number n of bits to right shift (/2^n) = difference bits(imageDtype) - imageBitDepth
        else :
            self.pySpinCamera.PixelFormat.SetValue(PySpin.PixelFormat_Mono16)
            self.imageDtype = np.uint16
            self.imageBitsToShift = int(16 - self.imageBitDepth) # number n of bits to right shift (/2^n) = difference bits(imageDtype) - imageBitDepth
        # set other properties  that are standard for proper acquisition
        self.pySpinCamera.BlackLevel.SetValue(0) # offset, former brightness
        self.pySpinCamera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        # self.pySpinCamera.Gamma.SetValue(1.) # not writable with some cameras like Chameleon 3 camera 
        # set trigger mode
        self.pySpinCamera.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)
        self.pySpinCamera.TriggerDelay.SetValue(self.pySpinCamera.TriggerDelay.GetMin())
        self.setTriggerMode(self.triggerMode)
        # get exposure min and max, set auto off and set exposure 
        self.exposuremsMin = self.pySpinCamera.ExposureTime.GetMin()*1.e-3
        self.exposuremsMax = self.pySpinCamera.ExposureTime.GetMax()*1.e-3
        self.pySpinCamera.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
        self.setExposurems(self.exposurems)
        # get gain properties and set gain
        self.gaindBMin = self.pySpinCamera.Gain.GetMin()
        self.gaindBMax = self.pySpinCamera.Gain.GetMax()
        self.pySpinCamera.GainAuto.SetValue(PySpin.GainAuto_Off)
        self.setGaindB(self.gaindB)
        # #set camera ROI, 
        self.setCamROI(ROI=camROI)
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
        # set camera buffer count to 20 images 
        self.pySpinCamera.TLStream.StreamBufferCountManual.SetValue(20)
        # 
        #start acquisition
        self.startAcquisition()
        self.startAcquisition() # to solve bug appearring on 25/05/2021
        self.cameraConnected = True
    
    
    def __del__(self) : 
        """Delete the Camera object by calling close function
        
        Close the Camera and free memory"""
        if self.cameraConnected :
            self.pySpinCamera.EndAcquisition()
            self.pySpinCamera.DeInit()
        del(self.pySpinCamera)
        self.camList.Clear()# Clear camera list before releasing system
        self.camSystem.ReleaseInstance()# Release PySpin system instance
        super().__del__() #ALWAYS call at end of any child class del
    
        
    def setTriggerMode(self, triggerMode):
        """Set the trigger mode 
        
        Args:
            triggerMode (int) :  0 for hardware/external, 1 for software/internal
        """
        acqStarted = self.pySpinCamera.IsStreaming()
        if acqStarted : #stop acquisition if already started
            self.pySpinCamera.EndAcquisition()
        self.triggerMode = triggerMode
        #stop trigger before change
        self.pySpinCamera.TriggerMode.SetValue(PySpin.TriggerMode_Off)
        if triggerMode==0:#'external'
            self.pySpinCamera.TriggerSource.SetValue(PySpin.TriggerSource_Line0)
        elif triggerMode==1:#'software'
            self.pySpinCamera.TriggerSource.SetValue(PySpin.TriggerSource_Software)
        else : raise NameError('Trigger mode number not defined ')
        #restart trigger
        self.pySpinCamera.TriggerMode.SetValue(PySpin.TriggerMode_On)
        if acqStarted : #restart acquisition if started initially
            self.pySpinCamera.BeginAcquisition()
    

    def sendSoftwareTrigger(self):
        """Send a software trigger to the camera to start an exposure"""
        self.pySpinCamera.TriggerSoftware.Execute()
        

    def setExposurems(self, exposurems) :
        """Set the duration of the exposition 
        
        Args:
            exposurems (float) : Exposition duration (exposure) in ms.
        """
        acqStarted = self.pySpinCamera.IsStreaming()
        if acqStarted : #stop acquisition if already started
            self.pySpinCamera.EndAcquisition()
        if exposurems >= self.exposuremsMin and exposurems <= self.exposuremsMax :
            self.pySpinCamera.ExposureTime.SetValue(exposurems*1.e3)
            self.exposurems = self.pySpinCamera.ExposureTime.GetValue()*1.e-3
        elif exposurems < self.exposuremsMin :
            self.pySpinCamera.ExposureTime.SetValue(self.exposuremsMin*1.e3)
            self.exposurems = self.pySpinCamera.ExposureTime.GetValue()*1.e-3
        else : 
            self.pySpinCamera.ExposureTime.SetValue(self.exposuremsMax*1.e3)
            self.exposurems = self.pySpinCamera.ExposureTime.GetValue()*1.e-3
        if acqStarted : #restart acquisition if started initially
            self.pySpinCamera.BeginAcquisition()
        

    def setGaindB(self, gaindB) :
        """Set the hardware gain of camera readout
        
        Args:
            gaindB (float) : hardware gain of the camera in dB.
        """
        acqStarted = self.pySpinCamera.IsStreaming()
        if acqStarted : #stop acquisition if already started
            self.pySpinCamera.EndAcquisition()
        gaindBset = gaindB
        if gaindBset > self.gaindBMax : gaindBset = self.gaindBMax
        if gaindBset < self.gaindBMin : gaindBset = self.gaindBMin
        self.pySpinCamera.Gain.SetValue(gaindBset)
        self.gaindB = self.pySpinCamera.Gain.GetValue()
        if acqStarted : #restart acquisition if started initially
            self.pySpinCamera.BeginAcquisition()


    def roundCamROI(self, ROI=None) :
        """Rounding of ROI values to closest possible one according to camera rules
        
        Keyword Args:
            ROI = None ( None or [int]*4) : [# x offset, y offset, x size, y size] 
                if None, set to [0, 0, max Width, max height]
            
        Return: 
            Camera ROI ([int]*4): [ x offset, y offset, x size, y size]
        """
        rules = [self.pySpinCamera.OffsetX.GetInc(),
                 self.pySpinCamera.OffsetY.GetInc(),
                 self.pySpinCamera.Width.GetInc(),
                 self.pySpinCamera.Height.GetInc()]
        self.wpxmax = self.pySpinCamera.Width.GetMax()
        self.hpxmax = self.pySpinCamera.Height.GetMax()
        if ROI is not None: 
            def rounding(a) :
                val, step = a
                return int(val - (val % step))
            [x,y,w,h] = ROI
            x = int(max(min(x,self.wpxmax-w), 0))
            y = int(max(min(y,self.hpxmax-h), 0))
            return map(rounding, zip([x,y,w,h], rules))
        else:
            return [0, 0, self.wpxmax , self.hpxmax]


    def setCamROI(self, ROI=None) :
        """Set the ROI of camera (without binning)
        
        Keyword Args:
            ROI = None ( None or [int]*4) : [ x offset, y offset, x size, y size] 
                if None, set to [0, 0, max Width, max height]
            
        Return: 
            Camera ROI ([int]*4) : [ x offset, y offset, x size, y size]
        """
        acqStarted = self.pySpinCamera.IsStreaming()
        if acqStarted : #stop acquisition if already started
            self.pySpinCamera.EndAcquisition()
        self.camROI = self.roundCamROI(ROI)
        [x,y,w,h] = self.camROI
        self.pySpinCamera.OffsetX.SetValue(x)
        self.pySpinCamera.OffsetX.SetValue(y)
        self.wpx = w #width
        self.pySpinCamera.Width.SetValue(w)
        self.hpx = h #height
        self.pySpinCamera.Height.SetValue(h)
        if acqStarted : #restart acquisition if started initially
            self.pySpinCamera.BeginAcquisition()
        return self.camROI

    def startAcquisition(self):
        """Start acquisition or restart if already running """
        if self.pySpinCamera.IsStreaming() :
            self.pySpinCamera.EndAcquisition()
        self.pySpinCamera.BeginAcquisition()
    
    
    def clearBuffer(self) :
        """ Clear camera buffer from images. 
        Use before imaging scans to make sure no previously acquired image is present in buffer"""
        while self.pySpinCamera.TLStream.StreamOutputBufferCount() > 0 :
            self._image = self.pySpinCamera.GetNextImage(int(100))


    def grabArray(self) :
        """Get an image from the camera. 
        Wait for trigger if external or generate one if internal.
            
        Return: 
            Camera image (numpy 2D array)
        """
        self.imageAcqLastFailed = False
        try: 
            if not self.pySpinCamera.IsStreaming() : # normally should not happen but if acquisition stopped, restart it
                self.startAcquisition()
            if self.triggerMode==1 :   
                self.sendSoftwareTrigger()
            self._image = self.pySpinCamera.GetNextImage(int(1000*self.timeout))
            if self._image.IsIncomplete():
                print('ERROR ! : Image incomplete with image status %d ...' % self._image.GetImageStatus())
                self.imageAcqLastFailed = True
                return False
            else :
                if self.reversedAxes == [False, False] :
                    self.image = np.array(self._image.GetNDArray()) >> self.imageBitsToShift
                elif self.reversedAxes == [True, False] :
                    self.image = np.flip(np.array(self._image.GetNDArray()) >> self.imageBitsToShift, 1) #X axis is second dimension in image array
                elif self.reversedAxes == [False, True] :
                    self.image = np.flip(np.array(self._image.GetNDArray()) >> self.imageBitsToShift, 0) #Y axis is first dimension in image array
                elif self.reversedAxes == [True, True] :
                    self.image = np.flip(np.array(self._image.GetNDArray()) >> self.imageBitsToShift, (0,1))
                else :
                    self.image = np.array(self._image.GetNDArray()) >> self.imageBitsToShift
                    print('WARNING ! : \n reversedAxes in camera config is not properly defined as [True/False , True/False] \n Axes unchanged from default [False, False]')
        except PySpin.SpinnakerException as ex:
            print('ERROR : %s' % ex)
            print('Failed to grab array from camera : probably Timeout')
            self.imageAcqLastFailed = True
            return False
        return self.image.copy()



class ExampleModelClass(FLIRPySpinClass) :
    """Model-specific class for ... FLIR camera using PySpin python driver.
    
        Child Class of FLIRPySpinClass. 
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




class Chameleon3Class(FLIRPySpinClass) :
    """Model-specific class for Chameleon3 FLIR cameras using PySpin python driver.
    
        Child Class of FLIRPySpinClass. 
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
            Chameleon3Class camera object
        """
        super().__init__(cameraNumber, triggerMode=triggerMode, exposurems=exposurems,
                         gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)

    def __del__(self) : 
        """Delete the Camera object by calling close function
        
        Close the Camera and free memory"""
        super().__del__() #ALWAYS call at end of any child class del


































