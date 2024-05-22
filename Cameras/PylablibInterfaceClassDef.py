# -*- coding: utf-8 -*-

"""
Define class interface of PyLabLib general driver for most of cameras
"""

import numpy as np

from .CameraClassDef import CameraClass

try : 
    from pylablib.devices.interface.camera import ICamera
    from pylablib.core.devio.comm_backend import DeviceError as pllDeviceError
    pylablibDriverInstalled = True
except :
    print('ERROR ! : Tried to load pylablib driver, but it is not installed')
    pylablibDriverInstalled = False


class PylablibInterfaceClass(CameraClass) :
    """Parent class for all camera driver classes using pylablib.
    
        Used as an interface through ICamera (IROICamera, IExposureCamera + Trigger) interface of pylablib """
        
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
            PylablibInterfaceClass camera object
        """
        super().__init__(cameraNumber, triggerMode=triggerMode, exposurems=exposurems,
                         gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)
        #check if pylablib driver installed, if no return
        self.cameraDriverInstalled = pylablibDriverInstalled 
        if not(self.cameraDriverInstalled) :
            print('ERROR ! : pylablib driver is not installed')
            return
        # here is the main camera object that will be used to access camera via driver : replaced in children classes
        self.pylablibCamera = ICamera()
        


    def __del__(self) : 
        """Delete the Camera object by calling close function
        
        Close the Camera and free memory"""
        if self.pylablibCamera.is_opened() :
            self.pylablibCamera.stop_acquisition()
            self.pylablibCamera.close()
        del(self.pylablibCamera)
        super().__del__() #ALWAYS call at end of any child class del

        
    def setTriggerMode(self, triggerMode):
        """Set the trigger mode 
        
        Args:
            triggerMode (int) :  0 for hardware/external, 1 for software/internal
        """
        raise NotImplementedError('Funtion SetTriggerMode not defined') 
        
    
    def sendSoftwareTrigger(self):
        """Send a software trigger to the camera to start an exposure"""
        raise NotImplementedError('Funtion sendSoftwareTrigger not defined') 
        

    def setExposurems(self, exposurems) :
        """Set the duration of the exposition 
        
        Args:
            exposurems (float) : Exposition duration (exposure) in ms.
        """
        self.exposurems = 1e3*self.pylablibCamera.set_exposure(exposurems*1e-3)
        
        
    def setGaindB(self, gaindB) :
        """Set the hardware gain of camera readout
        
        Args:
            gaindB (float) : hardware gain of the camera in dB.
        """
        raise NotImplementedError('Function setGaindB not defined') 


    def roundCamROI(self, ROI=None) :
        """Rounding of ROI values to closest possible one according to camera rules
        
        Keyword Args:
            ROI ( None or [int]*4) : [ x offset, y offset, x size, y size],
                if None, set to [0, 0, max Width, max height]
            
        Return: 
            Camera ROI ([int]*4) : [x offset, y offset, x size, y size]  
        """
        xlims,ylims = self.pylablibCamera.get_roi_limits()
        rules = [xlims[2], ylims[2], xlims[3], ylims[3]] # x offset step, y offset step, x size step, y size step
        self.wpxmax = xlims[1]
        self.hpxmax = ylims[1]
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
            ROI ( None or [int]*4) : [ x offset, y offset, x size, y size],
                if None, set to [0, 0, max Width, max height]
            
        Return: 
            Camera ROI ([int]*4) : [x offset, y offset, x size, y size]  
        """
        [x,y,w,h] = self.roundCamROI(ROI)
        self.pylablibCamera.set_roi(hstart=x, hend=w, vstart=y, vend=h)
        x,w,y,h,xbin,ybin = self.pylablibCamera.get_roi()
        self.wpx = w #width
        self.hpx = h #height
        self.camROI = [x,y,w,h]
        return self.camROI
    
    
    def startAcquisition(self):
        """Start acquisition or restart if already running 
        Defined as function in Icamera interface but require some specific parameters some times"""
        raise NotImplementedError('Function startAcquisition not defined') 
        
        
    def clearBuffer(self) :
        """ Clear camera buffer from images. 
        Use before imaging scans to make sure no previously acquired image is present in buffer"""
        if not self.pylablibCamera.acquisition_in_progress() : # normally should not happen but if acquisition stopped, restart it
            self.startAcquisition()
        while self.pylablibCamera.get_frames_status()[1] > 0 :
            self._image = self.pylablibCamera.read_oldest_image()
        

    def grabArray(self) :
        """Get an image from the camera. 
        Wait for trigger if external or generate one if software.
            
        Return: 
            Camera image (numpy 2D array)
        """
        self.imageAcqLastFailed = False
        try: 
            if not self.pylablibCamera.acquisition_in_progress() : # normally should not happen but if acquisition stopped, restart it
                self.startAcquisition()
            if self.triggerMode==1 :   
                self.sendSoftwareTrigger()
            self.pylablibCamera.wait_for_frame(since="lastread", nframes=1, timeout=self.timeout, error_on_stopped=True)
            self._image = self.pylablibCamera.read_oldest_image()
            if self.reversedAxes == [False, False] :
                self.image = np.array(self._image) 
            elif self.reversedAxes == [True, False] :
                self.image = np.flip(np.array(self._image) , 1) #X axis is second dimension in image array
            elif self.reversedAxes == [False, True] :
                self.image = np.flip(np.array(self._image) , 0) #Y axis is first dimension in image array
            elif self.reversedAxes == [True, True] :
                self.image = np.flip(np.array(self._image) , (0,1))
            else :
                self.image = np.array(self._image) 
                print('WARNING ! : \n reversedAxes in camera config is not properly defined as [True/False , True/False] \n Axes unchanged from default [False, False]')
        except pllDeviceError as ex:
            print('ERROR ! : Error doc :  %s' % ex.__doc__)
            self.imageAcqLastFailed = True
            return False
        return self.image.copy()


        






































