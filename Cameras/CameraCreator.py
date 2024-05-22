# -*- coding: utf-8 -*- 

"""
Define camera_creator : the Builder / factory that create the Camera object 
"""

from .Config import camerasConfigs
from .CameraClassDef import CameraClass

#make lists of cameras driver and model from camerasConfigs
driverList = []
modelList = []
for camConfig in camerasConfigs :
    if not type(camConfig)==dict :
        driverList.append('None')
        modelList.append('None')
    elif ('driver' in camConfig)  and ('model' in camConfig) :
        driverList.append(camConfig['driver'])
        modelList.append(camConfig['model'])
    elif ('driver' in camConfig) :
        driverList.append(camConfig['driver'])
        modelList.append('None') 
    elif ('model' in camConfig) :
        driverList.append('None')
        modelList.append(camConfig['model'])
    else :
        driverList.append('None')
        modelList.append('None') 

# try to import drivers for all cameras listed in camerasConfigs 
# we do this here rather than on the fly to avoid the import cost at runtime
loadedDriversList = []
unavailableDriversList = []
cameraClassNameList = ['None']*len(camerasConfigs)
for icam in range(len(camerasConfigs)) :
    if driverList[icam] == 'None' or driverList[icam] in unavailableDriversList :
        if icam != 0 :
            print('ERROR ! : Camera number '+str(icam)+' : Config missing driver or driver unvailable')
    elif driverList[icam] in loadedDriversList and hasattr(eval(driverList[icam]),modelList[icam]+'Class') :
        # child class for specific model already loaded in previous import, use generic driver class
        cameraClassNameList[icam] = driverList[icam]+'.'+modelList[icam]+'Class'
    elif driverList[icam] in loadedDriversList and not(hasattr(eval(driverList[icam]),modelList[icam]+'Class')) :
        # no child class for specific model, use generic driver class
        cameraClassNameList[icam] = driverList[icam]+'.'+driverList[icam]+'Class'
        if modelList[icam] == 'None' and icam != 0 :
            print('WARNING ! : Camera number '+str(icam)+' : Config missing model')
    else :
        #try loading the driver
        try : 
            exec('from . import '+driverList[icam])
            loadedDriversList.append(driverList[icam])
            if hasattr(eval(driverList[icam]),modelList[icam]+'Class')  : 
                # if class exist for model
                cameraClassNameList[icam] = driverList[icam]+'.'+modelList[icam]+'Class'
            else : 
                # no child class for specific model, use generic driver class
                cameraClassNameList[icam] = driverList[icam]+'.'+driverList[icam]+'Class'
                if modelList[icam] == 'None' and icam != 0:
                    print('WARNING ! : Camera number '+str(icam)+' : Config missing model')
                elif  icam != 0 : 
                    print("""Advice : Camera number """+str(icam)+""" does not have a model-specific driver. 
        Loading generic driver class """+str(driverList[icam])+""" instead.
        If using several camera models from a same manufacturer, 
        define model-specific class (a child class) handling initialization differences.""")
        except :
            unavailableDriversList.append(driverList[icam])
            print('ERROR ! : Camera number '+str(icam)+' : Config driver '+ driverList[icam] +'  misspelled or not implemented')



def create_Camera(cameraNumber, triggerMode=0, exposurems=1., gaindB=0., camROI=None, loadDefault = False): 
    """Builder / factory that create the Camera object 
    
    With the right specific class (interface with parent class CameraClass) 
    depending on the camera model as defined by the info in Config.camerasConfigs
    
    Args:
        cameraNumber (int) : index of camera in camerasConfigs list
        
    Keyword Args:
        triggerMode=0  (int) : 0 for hardware/external, 1 for software/internal
        
        exposurems=1. (float) : Exposition duration (exposure) in ms.
        
        gaindB=0. (float) : hardware gain of the camera in dB.
        
        camROI=None (None or [int]*4) : Camera region of interest to read from sensor
            [x offset , y offset , x size , y size ] (binning is not implemented)
        
        loadDefault = False  (bool): Decide if default values from cameraConfigs should be set at creation 
        
    Return: 
        Camera object (interface CameraClass)        
    """
    # if out of range or 0 => 0 and empty base camera object
    if cameraNumber > (len(camerasConfigs)-1) or cameraNumber < 0 \
        or camerasConfigs[cameraNumber] == None or cameraNumber == 0 :
        if cameraNumber != 0 :
            print('WARNING ! : No camera configured for the number '+ str(cameraNumber)+' \n Create empty base camera object')
        #Create empty base camera object if camera number does not match a config
        Camera = CameraClass(0)
    # if driver not defined properly => 0 and empty base camera object
    elif cameraClassNameList[cameraNumber] == 'None' :
        print('ERROR ! :Camera '+ str(cameraNumber)+' driver class not defined \n Create empty base camera object')
        #Create empty base camera object if camera number does not match a config
        Camera = CameraClass(0)
    # initialize camera normally
    else :
        Camera = eval(cameraClassNameList[cameraNumber])(cameraNumber, triggerMode=triggerMode, exposurems=exposurems, 
                                                         gaindB=gaindB, camROI=camROI, loadDefault=loadDefault)
        if not(Camera.cameraDriverInstalled) or not(Camera.cameraConnected) :
            print('ERROR ! : Camera '+ str(cameraNumber)+' is not connected or driver not installed \n Create empty base camera object')
            Camera = CameraClass(0)
    return Camera
  