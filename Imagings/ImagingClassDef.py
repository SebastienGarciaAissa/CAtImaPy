#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Define Imaging class and functions for aquisition and analysis
"""

from . import fittool 

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm 
import matplotlib.patches as patches
import time
import pickle
from PIL import Image
import tifffile


class ImagingClass():
    """Class of Imaging object : the center object for aquisition, analysis and saving"""
    
    def __init__(self, dirAndFileName='', mplwidgetImage=None, mplwidgetAnalysisGraph=None): 
        """Initialize the Imaging object 
        
        Keyword Args:
            dirAndFileName='' (str) : Absolute path file name with appended number but without extension
            
            mplwidgetImage=None (None or UImatplotlibWidget) : to plot images or atomic density on UI left graph
            
            mplwidgetAnalysisGraph=None (None or UImatplotlibWidget) : to plot analysis on UI right graph
            
        Return: 
            ImagingClass object
        """
        self.dirAndFileName = dirAndFileName
        self.imagingType = 0 # 0 : Absorption, 1:Fluo
        self.imagingTypeTextList = ['Absorption Imaging', 'Fluorescence Imaging'] 
        self.cameraNumber = 0
        self.cameraConfig = None
        self.cameraExposurems = 0.
        self.cameraGaindB = 0.
        self.cameraTriggerMode = 0
        self.flushSensor = False
        self.removeBackground = False
        self.pixelCalXumperpx = 1.
        self.pixelCalYumperpx = 1.
        self.pixelCalAreaum2 = 1. # in m^2
        self.imageSize = (1,1)
        self.wpx = 1 # with in pixel : X axis : in image array image[Y,X]
        self.hpx = 1 # hieght in pixel : Y axis : in image array image[Y,X]
        self.imageLimits = [0.,1.,0.,1.]
        self.cameraMaxLevel = 255
        self.imageDtype = np.uint8
        # axes of the image 
        self.Xaxispx = np.arange(self.wpx)
        self.Yaxispx = np.arange(self.hpx)
        self.Xaxisum = (np.arange(self.wpx)-float(self.wpx)/2.)*self.pixelCalXumperpx
        self.Yaxisum = (np.arange(self.hpx)-float(self.hpx)/2.)*self.pixelCalXumperpx
        #ROI for fit and atom number integration
        self.ROIn = 1 #number of ROIs
        self.ROIarrayIndexTab = np.array([int(0)])
        self.ROInameTab = np.array([str('New')])
        self.ROIxywhTabum = np.array([[[0.,1.],[0.,1.]]]) #ROI x center, y center, x width, y height
        self.ROIlimitsTabum = np.array([[[-1.,1.],[-1.,1.]]])
        self.ROIlimitsTabpx = np.array([[[0,1],[0,1]]],dtype=np.int)
        self.ROIblackNumber = 1
        self.ROIredNumber = 0
        self.ROIgreenNumber = 0
        self.ROIblackTabIndex = 0
        self.ROIredTabIndex = None
        self.ROIgreenTabIndex = None
        self.drawROIblack = True
        self.drawROIred = False
        self.drawROIgreen = False
        #fit ROI
        self.fitROIlimitsTabpx = np.array([[[0,1],[0,1]]],dtype=np.int)
        # define images 
        self.imAt = np.zeros((1,1), dtype=self.imageDtype) #image with atoms
        self.imRef = np.zeros((1,1), dtype=self.imageDtype) # image reference without atoms for absorption
        self.imBkgd = np.zeros((1,1), dtype=self.imageDtype) # image of background (without atoms nor imaging light)
        #define variables for imaging
        self.Isat = 16.69 # value (W.m^-2) of effective saturation intensity for the aborption imaging here, set in config file
        self.cameraQuantumEff = 0.31/4 # quantum efficiency of the sensor at atomic frequency
        self.numericalAperture = 0.1 # numerical aperture of the imaging system
        self.hplanck = 6.62607e-34
        self.atomicFrequencyTHz = 384.230 # atomic transtion frequency
        self.atomicLineFWHWinMHz = 6.066 # atomic natural linewidth in MHz (full width at half maximum in frequency)
        self.atomicgamma = np.pi * self.atomicLineFWHWinMHz * 1.0e+6 # gamma = Gamma/2
        self.laserPulseDurationus = 1.
        self.includeSaturationEffects = True # add correction due to saturation of atomic response to atomic density
        # define variables for absorption
        self.thresholdAbsImg = 1 # threshold value for absorption
        self.crossSectionum2 = 0.2906 # effective value (um^2) of cross section  = 1e+12*self.hplanck*self.atomicFrequencyTHz*1.e+12*self.atomicgamma / self.Isat
        self.coeffAbsStrongSatcalc = 0. # float(self.includeSaturationEffects) / self.atomicgamma / (self.pixelCalAreaum2 * self.cameraQuantumEff *self.laserPulseDurationus*1.e-6 )
        self.ODe = np.zeros((1,1)) # OD defined by ln(imAt/Iref)
        # define varaibles for Fluo
        self.laserIntensity = 1. # in W/m² 
        self.laserDetuningMHz = 0. # detuning from resonance in MHz
        self.rateScattFluoPerAtom = 1. #self.atomicgamma *(self.laserIntensity/self.Isat)/(1 + (self.laserIntensity/self.Isat) + (2*self.laserDetuningMHz/self.atomicLineFWHWinMHz)**2 )
        self.coeffFluoCalc = 1. #2./( (1-np.sqrt(1-self.numericalAperture**2)) *self.cameraQuantumEff*self.laserPulseDurationus*1.e-6*self.rateScattFluoPerAtom*self.pixelCalAreaum2)
        self.Fluo = np.zeros((1,1)) # Fluo image defined by I-Iref
        #define variables for Temperature measurement
        self.atomicMassUnitinSI = 1.6609e-27 #kg
        self.atomicMassAU = 86.609 #atom mass in atomic units
        self.kB = 1.3806e-23 #Boltzmann constant in SI
        # boolean for measurment type
        self.isTemperatureMeas = False  # mostly used for loading data
        self.isLifetimeMeas = False  # mostly used for loading data
        self.scanDone = False 
        self.atomImagingDone = False 
        #define general imaging result variables
        self.atomicDensityIntZperum2 = None# atomic density integrated along camera axis : calculated from images, unit atoms/µm² 
        self.atomNumber = np.zeros(1)
        self.cloudRadiium = np.zeros((1,2)) # X axis = index 1, Y axis = index 0 
        self.cloudPositionspx = np.zeros((1,2),dtype=np.int) # X axis = index 1, Y axis = index 0 
        self.cloudPositionsum = np.zeros((1,2)) # X axis = index 1, Y axis = index 0 
        #define average variables
        self.ODeAv = np.zeros((1,1)) # OD averaged defined by ln(imAt/Iref)    
        self.FluoAv = np.zeros((1,1)) # Fluo averaged defined by imAt - Iref       
        self.atomicDensityIntZperum2Av = np.zeros((1,1)) # atomic density averaged
        self.atomNumberAv = np.zeros(1)
        self.atomNumberAvErr = np.zeros((1,1))
        self.atomNumberList =  np.zeros((1,1))
        self.cloudRadiiumAv = np.zeros((1,2)) # X axis = index 1, Y axis = index 0
        self.cloudRadiiumList = np.zeros((1,1,2))
        self.cloudRadiiumAvErr = np.zeros((1,2))
        self.cloudPositionspxAv = np.zeros((1,2)) # X axis = index 1, Y axis = index 0
        self.cloudPositionspxList = np.zeros((1,1,2))
        self.cloudPositionsumList = np.zeros((1,1,2))
        self.cloudAvRadiium = np.zeros((1,1,2))  # results of fit on the averaged atomic density
        self.cloudAvPositionspx = np.zeros((1,1,2))  # results of fit on the averaged atomic density
        self.cloudAvPositionsum = np.zeros((1,1,2))  # results of fit on the averaged atomic density
        self.cloudZonepx =  np.zeros((1,2,2),dtype=np.int)
        self.cloudAvZonepx =  np.zeros((1,2,2),dtype=np.int)
        #define scan variables
        self.averages = 1
        self.averageIndex = 0
        self.scans = 1
        self.cycles = 1
        self.scanStart = 0.
        self.scanStep = 1.
        self.scanIndex = 0
        self.scan_xaxis = np.zeros(1)
        self.T_averages = 1
        self.T_TOFscans = 1
        self.T_TOFstartms = 0.
        self.T_TOFstepms = 1.
        self.T_scans = 1
        self.T_scanStart = 0.
        self.T_scanStep = 1.
        self.T_scanIndex = 0
        self.T_cycles = 1
        self.LT_averages = 1
        self.LT_Tscans = 1
        self.LT_Tstartms = 0.
        self.LT_Tstepms = 1.
        self.LT_scans = 1
        self.LT_scanStart = 0.
        self.LT_scanStep = 1.
        self.LT_scanIndex = 0
        self.LT_cycles = 1
        self.scanVarName = 'Scan parameter'
        self.scanUnitName = 'Units'
        # define scan results
        self.atomNumberArray = np.zeros((1,1,1))
        self.atomNumberAvList = np.zeros((1,1))
        self.atomNumberAvErrList = np.zeros((1,1))
        self.atomNumberAvAvList = np.zeros((1,1))
        self.atomNumberAvAvErrList = np.zeros((1,1))
        self.cloudRadiiumArray = np.zeros((1,1,1,2))
        self.cloudRadiiumAvList = np.zeros((1,1,2))
        self.cloudRadiiumAvErrList = np.zeros((1,1,2))
        self.cloudAvRadiiumList = np.zeros((1,1,2))  # results of fit on the averaged atomic density
        self.cloudPositionsumArray = np.zeros((1,1,1,2))
        self.cloudPositionsumAvList = np.zeros((1,1,2))
        self.cloudPositionsumAvErrList = np.zeros((1,1,2))
        self.cloudAvPositionsumList = np.zeros((1,1,2))  # results of fit on the averaged atomic density
        # define temperature measurement variables
        self.T_TOFmsaxis = np.zeros(1)
        self.T_tempXaxisuK = np.zeros(1)
        # self.T_tempXaxisuKErr = np.zeros(1)
        self.T_tempYaxisuK = np.zeros(1)
        # self.T_tempYaxisuKErr = np.zeros(1)
        self.T_tempXaxisuKList = np.zeros((1,1))
        # self.T_tempXaxisuKErrList = np.zeros((1,1))
        self.T_tempYaxisuKList = np.zeros((1,1))
        # self.T_tempYaxisuKErrList = np.zeros((1,1))
        self.T_cloudRadiusumXaxis = np.zeros((1,1))
        self.T_cloudRadiusumXaxisErr = np.zeros((1,1))
        self.T_cloudRadiusumYaxis = np.zeros((1,1))
        self.T_cloudRadiusumYaxisErr = np.zeros((1,1))
        self.linfitTX_xaxis = np.zeros((1,1)) 
        self.linfitTY_xaxis = np.zeros((1,1))
        self.linfitTX_yaxis = np.zeros((1,1)) 
        self.linfitTY_yaxis = np.zeros((1,1))
        # define lifetime measurement variables
        self.LT_Tmsaxis = np.zeros(1)
        self.LT_Lifetimems = np.zeros(1)
        self.LT_LifetimemsErr = np.zeros(1)
        self.LT_atomNumberTStartFitted = np.zeros(1)
        self.LT_atomNumberTStartFittedErr = np.zeros(1)
        self.LT_atomNumberOffsetFitted = np.zeros(1)
        self.LT_atomNumberOffsetFittedErr = np.zeros(1)
        self.LT_LifetimemsList = np.zeros((1,1))
        self.LT_LifetimemsErrList = np.zeros((1,1))
        self.LT_atomNumberTStartFittedList = np.zeros((1,1))
        self.LT_atomNumberTStartFittedErrList = np.zeros((1,1))
        self.LT_atomNumberOffsetFittedList = np.zeros((1,1))
        self.LT_atomNumberOffsetFittedErrList = np.zeros((1,1))
        self.LT_atomNumberAvTStartList = np.zeros((1,1))
        self.LT_atomNumberAvTStartErrList = np.zeros((1,1))
        self.expfitLT_xaxis = np.zeros((1,1)) 
        self.expfitLT_yaxis = np.zeros((1,1))
        #plotting bool variables
        self.plotSingleImage = False
        self.plotAtomicDensityAv = False
        self.plotFit1D = False
        # plotting axes
        self.plotLeftAxisVar = 0 # 0: Atom Number, 1: Radii, 2: Positions, 3: Temperature, 4: Lifetime
        self.plotRightAxisVar = 1 # 0: Atom Number, 1: Radii, 2: Positions, 3: Temperature, 4: Lifetime
        self.scan_xaxis = np.zeros(1)
        self.T_scan_xaxis = np.zeros(1)
        self.LT_scan_xaxis = np.zeros(1)
        #plot colors and markers
        self.colorL = (0.67,0.,0.)
        self.colorR = (0.2,0.2,1.)
        self.colorL2 = (0.8,0.4,0.4)
        self.colorR2 = (0.5,0.5,1.)
        self.linestyles1 = [(0, (1, 3)) , (2, (1, 3))]
        self.linestyles2 = [(0, (3, 9)) , (6, (3, 9))]
        self.linestylesFit1 = [(0, (2, 2)) , (2, (2, 2))]
        self.linestylesFit2 = [(0, (6, 6)) , (6, (6, 6))]
        self.ROIcolorList = [(0.,0.,0.), (1.,0.,0.), (0.,0.9,0.)]
        self.markerSize = 7
        self.markerEdgeWidth = 2.5
        self.markerL1 = 's'
        self.markerL2 = 'o'
        self.markerR1 = 'v'
        self.markerR2 = 'p'
        #ui plots figure
        self.mplwidgetImage = mplwidgetImage
        self.mplwidgetAnalysisGraph = mplwidgetAnalysisGraph
        self.figPos = None #cloud position figure
        self.axPos = None #cloud position axes
        #save 
        self.autoSaveImages = False
        self.saveImagesFormat = 0 # 0:NPZ (numpy) 1: PNG, 2: TIFF,
        self.comment = ''
        #boolean to know if measured now or loaded from old file
        self.loaded = False
        
        
    def set_Imaging_variables_from_cam(self,Camera):
        """Initialize some Imaging object variables from the Camera object variables
        
        Args:
            Camera (CameraClass) :  Camera object
        """
        self.cameraConfig = Camera.cameraConfig
        self.cameraNumber = Camera._cameraNumber
        self.cameraExposurems = Camera.exposurems
        self.cameraGaindB = Camera.gaindB
        self.cameraTriggerMode = Camera.triggerMode
        self.pixelCalXumperpx = Camera.pixelCalXumperpx
        self.pixelCalYumperpx = Camera.pixelCalYumperpx
        self.pixelCalAreaum2 = self.pixelCalXumperpx*self.pixelCalYumperpx #♠ in um^2
        self.imageSize = Camera.imageSize
        self.wpx = Camera.wpx # with in pixel : X axis : in image array image[Y,X]
        self.hpx = Camera.hpx # hieght in pixel : Y axis : in image array image[Y,X]
        self.imageLimits = Camera.imageLimits
        self.imageBitDepth = Camera.imageBitDepth
        self.cameraMaxLevel = Camera.maxLevel
        self.imageDtype = Camera.imageDtype
        self.Xaxispx = np.arange(self.wpx)
        self.Yaxispx = np.arange(self.hpx)
        self.Xaxisum = (np.arange(self.wpx)-float(self.wpx)/2.)*self.pixelCalXumperpx
        self.Yaxisum = (np.arange(self.hpx)-float(self.hpx)/2.)*self.pixelCalXumperpx
        # define images 
        self.imAt = np.zeros(self.imageSize, dtype=self.imageDtype) #image with atoms
        self.imRef = np.zeros(self.imageSize, dtype=self.imageDtype) # image reference without atoms for absorption
        self.imBkgd = np.zeros(self.imageSize, dtype=self.imageDtype) # image of background (without atoms nor imaging light)
        # define variables for imaging (some loaded directly from ui before) 
        self.cameraQuantumEff = self.cameraConfig['cameraQuantumEff'] # quantum efficiency of the sensor at 780 nm 
        self.numericalAperture = self.cameraConfig['numericalAperture']        
        self.atomicMassAU = self.cameraConfig['Imaging__atomicMassAU']
        self.atomicFrequencyTHz = self.cameraConfig['Imaging__atomicFrequencyTHz']
        self.atomicLineFWHWinMHz = self.cameraConfig['Imaging__atomicLineFWHWinMHz']  # atomic natural linewidth in MHz (full width at half maximum in frequency)
        self.atomicgamma = np.pi * self.atomicLineFWHWinMHz * 1.0e+6 # gamma = Gamma/2 : coherence/dipole decay
        self.atomicDensityIntZperum2 = np.zeros(self.imageSize)# atomic density integrated along camera axis : calculated from images, unit atoms/µm²      
        self.atomicDensityIntZperum2Av = np.zeros(self.imageSize)
        # define variables for absorption
        self.crossSectionum2 = 1e+12*self.hplanck*self.atomicFrequencyTHz*1.e+12*self.atomicgamma / self.Isat
        self.coeffAbsStrongSatcalc = float(self.includeSaturationEffects) / self.atomicgamma \
                                      / (self.pixelCalAreaum2 * self.cameraQuantumEff * self.laserPulseDurationus*1.e-6 )
        self.ODe = np.zeros(self.imageSize) # OD defined by ln(imAt/Iref)
        self.ODeAv = np.zeros(self.imageSize) # OD average defined by ln(imAt/Iref)  
        # define varaibles for Fluo
        self.rateScattFluoPerAtom = self.atomicgamma *(self.laserIntensity/self.Isat)\
                                        /(1 + (self.laserIntensity/self.Isat) \
                                            + (2*self.laserDetuningMHz/self.atomicLineFWHWinMHz)**2 )
        self.coeffFluoCalc = 2./( (1-np.sqrt(1-self.numericalAperture**2)) *self.cameraQuantumEff\
                                        *self.laserPulseDurationus*1.e-6\
                                        *self.rateScattFluoPerAtom*self.pixelCalAreaum2)
        self.Fluo = np.zeros(self.imageSize) # Fluo defined by I-Iref
        self.FluoAv = np.zeros(self.imageSize) # Fluo average defined by I-Iref
        
        
    def set_ROIs_from_ROIarray(self, ROIarray) :
        """ Refresh analysis ROI defintions from ROIarray loaded from UI  
        
        Args:
            ROIarray (numpy array 6*n dtype = str) :  analysis ROI defintions
        """
        self.ROIarrayIndexTab = np.where( ROIarray[:,0] == str(int(self.cameraNumber)) )[0] # carefull ROI index is ROI number -1 
        self.ROIn = len(self.ROIarrayIndexTab)
        self.ROInameTab = ROIarray[self.ROIarrayIndexTab, 1]
        #ROI x center, y center, x width, y height
        self.ROIxywhTabum = ROIarray[ self.ROIarrayIndexTab, 2:6].astype(float) #ROI x center, y center, x width, y height
        self.ROIlimitsTabum = np.zeros((self.ROIn, 2,2))
        self.ROIlimitsTabpx = np.zeros((self.ROIn, 2,2),dtype=np.int)
        for i in range(self.ROIn) : 
            self.ROIlimitsTabum[i] =  [[min(max((self.ROIxywhTabum[i,1]-self.ROIxywhTabum[i,3]/2.),self.imageLimits[2]),self.imageLimits[3]),
                                        max(min((self.ROIxywhTabum[i,1]+self.ROIxywhTabum[i,3]/2.),self.imageLimits[3]),self.imageLimits[2])],
                                        [min(max((self.ROIxywhTabum[i,0]-self.ROIxywhTabum[i,2]/2.),self.imageLimits[0]),self.imageLimits[1]),
                                         max(min((self.ROIxywhTabum[i,0]+self.ROIxywhTabum[i,2]/2.),self.imageLimits[1]),self.imageLimits[0])]]
            self.ROIlimitsTabpx[i] =  [[int(min(max((-self.ROIxywhTabum[i,1]-self.ROIxywhTabum[i,3]/2.)/self.pixelCalYumperpx+self.hpx/2.,0),self.hpx)),
                                        int(max(min((-self.ROIxywhTabum[i,1]+self.ROIxywhTabum[i,3]/2.)/self.pixelCalYumperpx+self.hpx/2.,self.hpx),0))],
                                       [int(min(max((self.ROIxywhTabum[i,0]-self.ROIxywhTabum[i,2]/2.)/self.pixelCalXumperpx+self.wpx/2.,0),self.wpx)),
                                        int(max(min((self.ROIxywhTabum[i,0]+self.ROIxywhTabum[i,2]/2.)/self.pixelCalXumperpx+self.wpx/2.,self.wpx),0))]]
            if (self.ROIlimitsTabpx[i][0,0] == self.ROIlimitsTabpx[i][0,1]) or (self.ROIlimitsTabpx[i][1,0] == self.ROIlimitsTabpx[i][1,1]) :
                print("Warning : ROI " + self.ROInameTab[i] + " defined out of field of view. \n Redefine this ROI in Imaging as full field of view !")
                self.ROIlimitsTabpx[i] =  [[0, self.hpx], [0, self.wpx]]
                self.ROIlimitsTabum[i] = [[self.imageLimits[2], self.imageLimits[3]], [self.imageLimits[0], self.imageLimits[1]]]

            
    def print_dict_full(self, d, indentation=0):
        """ Returns a string representation of the content of a dictionary for saving.
        
            No line limits, arrays limited to 10000 elements
        
        Args: 
            d (dict) : dictionary to print
            
        Keyword Args:
            indentation (int) : number of initial linespaces, 
                used in recursive call of function when item is dict
        
        Return: 
            String representation of the dict (str)
        """
        s = ''
        for k,v in sorted(d.items()):
            s0 = ' '*indentation + str(k) + ' : '
            if type(v) is dict:
                s += s0+'\n'
                s += self.print_dict_full(v, indentation+2)
            elif type(v) == type(np.zeros((10,10))):
                if np.size(v) < 10000 :
                    s += s0 + str(v) + '\n'
                else :
                    s += s0 + 'Array too large be printed \n'
            else:
                s += s0 + str(v) + '\n'
        return s
    
    
    def save_imaging_vars_as_dict(self, dirAndFileName=None, SaveAtomicDensity = True):
        """ Save Imaging object as a dictionnary
        
            Save two files : one '.txt' without 2D data and one '.imo' (binary pickle format) 
            2D data is not saved except atomic density if asked
        
        Args: 
            dirAndFileName (None or str) : Absolute path file name with appended number but without extension
        
            SaveAtomicDensity (bool) : Decide if 2D data of atomic density should be saved in '.imo' file
        """
        if dirAndFileName == None :
            dirAndFileName = self.dirAndFileName
        else :
            self.dirAndFileName = dirAndFileName
        ImagingDict = vars(self).copy()
        #remove large useless objects from imaging object
        excludedVars = ['mplwidgetImage', 'mplwidgetAnalysisGraph', 'ODe', 'ODeAv', 'atomicDensityIntZperum2', 
                        'imAt','imRef','imBkgd', 'Fluo', 'FluoAv']
        if not(SaveAtomicDensity) or not(type(ImagingDict['atomicDensityIntZperum2Av']) == type(np.zeros((10,10)))) :
            excludedVars.append('atomicDensityIntZperum2Av')
        else :
            ImagingDict['atomicDensityIntZperum2Av'] = self.atomicDensityIntZperum2Av.astype(np.float32)
        for var in excludedVars :
            ImagingDict.pop(var)
        #save text file
        with open(dirAndFileName + '.txt','w') as f:
            f.write('{0} : {1} \r\n')
            f.write(self.print_dict_full(vars(self), indentation=0))
        #save dict of object vars in pickle format
        try: 
            fc = open(dirAndFileName + '.imo','wb')
            pickle.dump(ImagingDict,fc,pickle.HIGHEST_PROTOCOL)
            fc.close()
        except :
            print('ERROR : could not save Imaging data into file : \n' + dirAndFileName + '.imo')

            
    def load_imaging_vars_from_dict(self, dirAndFileName):
        """ Load Imaging object variable from dictionary saved in file  
        
        Args: 
            dirAndFileName (str) : Absolute path file name with appended number but without extension
        """
        try :        
            fc = open(dirAndFileName + '.imo','rb')
            ImagingDict = pickle.load(fc, encoding='latin1') # encoding is here to allow loading of file saved with Python 2.7
            fc.close()
            for k,v in ImagingDict.items() :
                setattr(self,k,v)
            if 'atomicDensityIntZperum2Av' in ImagingDict.keys():
                self.atomicDensityIntZperum2Av = ImagingDict['atomicDensityIntZperum2Av'].astype(np.float)
        except:
            print('ERROR : could not load Imaging data from file : \n' + dirAndFileName + '.imo')
    
    
    def save_images(self, dirAndFileNameImages, saveImagesFormat=None):
        """ Save images taken during last atom_imaging.
        
        Args:
            dirAndFileNameImages (str) : Absolute path file name with appended number and scan(s) number(s) 
                                        but without extension
        
        Keyword Args:
           saveImagesFormat=None (None or str) : file format : 0:NPZ (numpy) 1: PNG, 2: TIFF,
               if None or not int or not 0<= <=2 : take saveImagesFormat attribute
        """
        if saveImagesFormat is not None and saveImagesFormat.type == int and 0<=saveImagesFormat<=2 :
            self.saveImagesFormat = saveImagesFormat
        # first list images to save depending on imaging settings
        imagesToSave = [self.imAt]
        imagesToSaveNames = ['imAt']
        if self.imagingType == 0 : # absorption
            imagesToSave.append(self.imRef)
            imagesToSaveNames.append('imRef')
        if self.removeBackground : 
            imagesToSave.append(self.imBkgd)
            imagesToSaveNames.append('imRef')
        # save images
        if self.saveImagesFormat == 0 : #NPZ
            try: 
                np.savez_compressed(dirAndFileNameImages, **dict(zip(imagesToSaveNames,imagesToSave)))
            except :
                print('ERROR : could not save images into file : \n' + dirAndFileNameImages + '.npz')
        elif self.saveImagesFormat == 1 : #PNG
            for iIm in range(len(imagesToSave)) :
                fname = dirAndFileNameImages +'_' + imagesToSaveNames[iIm] +'.png'
                try: 
                    if imagesToSave[iIm].dtype == np.uint8 :
                        Image.fromarray(imagesToSave[iIm], mode='L').save(fname)
                    else :
                        Image.fromarray(imagesToSave[iIm].astype(np.int32) << (16-self.imageBitDepth), mode='I').save(fname) #Pillow is not able to manage 16bit png only 8bit-uint or 32bit-signed-int but in that case use only up to 16 bit for compatibility with image viewers
                        if self.imageBitDepth > 16 :
                            print('ERROR ! : PNG saving cause data loss with camera bit depth larger than 16. \n Save in another format to avoid information loss!')
                except :
                    print('ERROR : could not save images into file : \n' + fname)
        elif self.saveImagesFormat == 2 : #TIFF
            fname = dirAndFileNameImages +'.tiff'
            try: 
                if imagesToSave[0].dtype == np.uint8 :
                    # Image.fromarray(imagesToSave[0], mode='L').save(fname, format='tiff', save_all=True,
                    #                         append_images=[Image.fromarray(imagesToSave[iIm], mode='L') for iIm in range(1,len(imagesToSave))] )
                    tifffile.imwrite(fname, np.array(imagesToSave), photometric='minisblack', metadata={'Labels': imagesToSaveNames})
                else :
                    # Image.fromarray(imagesToSave[0].astype(np.int32) << (31-self.imageBitDepth) , mode='I').save(fname, format='tiff', save_all=True,
                    #                         append_images=[Image.fromarray(imagesToSave[iIm].astype(np.int32) << (32-self.imageBitDepth), mode='I') for iIm in range(1,len(imagesToSave))] )
                    tifffile.imwrite(fname, (np.array(imagesToSave) << (16-self.imageBitDepth)).astype(np.uint16), photometric='minisblack', metadata={'Labels': imagesToSaveNames})
                    if self.imageBitDepth > 16 :
                        print('ERROR ! : TIFF saving cause data loss with camera bit depth larger than 16. \n Save in another format to avoid information loss!')
            except :
                print('ERROR : could not save images into file : \n' + fname)
        else :
            print('ERROR : Invalid self.saveImagesFormat in save_images method of Imaging class')


    def save_images_during_atom_imaging(self, averages=1):
        """ Save images automatically (called in atom imaging)."""
        dirAndFileNameImages = self.dirAndFileName
        if self.isTemperatureMeas and self.T_scans>1 :
            dirAndFileNameImages += '_T{0:02d}'.format(self.T_scanIndex)
        elif self.isLifetimeMeas and self.LT_scans>1 :
            dirAndFileNameImages += '_LT{0:02d}'.format(self.LT_scanIndex)
        dirAndFileNameImages += '_scan{0:02d}'.format(self.scanIndex)
        if averages > 1 :
            dirAndFileNameImages += '_av{0:02d}'.format(self.averageIndex)
        self.save_images(dirAndFileNameImages)
        
    
    def imaging_scan(self, Camera, ui):
        """ Do a standard scan of acquistion and analysis (Imaging tab)
        
        Args: 
            Camera (CameraClass) :  Camera object
            
            ui (UI.Ui_MainWindow) : GUI object to collect and pass variables and graphs
            
        Return:
            If scan performed normally (bool) 
        """
        self.isTemperatureMeas = False
        self.isLifetimeMeas = False
        # clear camera buffer
        Camera.clearBuffer()
        # set var name and unit
        self.scanVarName = ui.lineEdit_scanVarName.text()
        self.scanUnitName = ui.lineEdit_scanUnitName.text()
        self.scanDone = self.imaging_scan_measurement(Camera, ui, averages=self.averages, scans=self.scans)
        return self.scanDone
        
        
    def temperature_measurement_scan(self, Camera, ui):
        """ Do a scan of temperature measurements and analysis (Temperature tab) 
        
        Args: 
            Camera (CameraClass) :  Camera object
            
            ui (UI.Ui_MainWindow) : GUI object to collect and pass variables and graphs
            
        Return:
            If scan performed normally (bool) 
        """
        self.isTemperatureMeas = True
        self.isLifetimeMeas = False
        # clear camera buffer
        Camera.clearBuffer()
        #set right axis to cloud radii during the scan
        ui.Imaging__plotRightAxisVar.setCurrentIndex(1)
        self.plotRightAxisVar = 1
        #define result arrays
        self.scanVarName = ui.lineEdit_scanVarName.text()
        self.scanUnitName = ui.lineEdit_scanUnitName.text()
        self.T_tempXaxisuKList = np.zeros((self.ROIn,self.T_scans))
        # self.T_tempXaxisuKErrList = np.zeros((self.ROIn,self.T_scans))
        self.T_tempYaxisuKList = np.zeros((self.ROIn,self.T_scans))
        # self.T_tempYaxisuKErrList = np.zeros((self.ROIn,self.T_scans))
        self.T_atomNumberArray = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,self.T_averages))
        self.T_atomNumberAvList =  np.zeros((self.ROIn,self.T_scans,self.T_TOFscans))
        self.T_atomNumberAvErrList = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans))
        self.T_cloudRadiiumArray = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,self.T_averages,2))
        self.T_cloudRadiiumAvList = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,2))
        self.T_cloudRadiiumAvErrList = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,2))
        self.T_cloudAvRadiiumList = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,2))
        self.T_cloudPositionsumArray = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,self.T_averages,2))
        self.T_cloudPositionsumAvList = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,2))
        self.T_cloudPositionsumAvErrList = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,2))
        self.T_cloudAvPositionsumList = np.zeros((self.ROIn,self.T_scans,self.T_TOFscans,2))
        self.atomNumberAvAvList = np.zeros((self.ROIn,self.T_scans))
        self.atomNumberAvAvErrList = np.zeros((self.ROIn,self.T_scans))
        self.cloudAvRadiiumAvList = np.zeros((self.ROIn,self.T_scans,2))
        self.cloudAvRadiiumAvErrList = np.zeros((self.ROIn,self.T_scans,2))
        self.cloudAvPositionsumAvList = np.zeros((self.ROIn,self.T_scans,2))
        self.cloudAvPositionsumAvErrList = np.zeros((self.ROIn,self.T_scans,2))
        for i in range(self.T_scans) :
            self.T_scanIndex = i
            self.scanDone = self.imaging_scan_measurement(Camera, ui, averages=self.T_averages, 
                                                     scans=self.T_TOFscans)
            if not(self.scanDone) : 
                return False
            else : 
                self.fit_T_measurement(ui)
                self.plot_T_measurement()
                self.T_tempXaxisuKList[:,i] = self.T_tempXaxisuK
                # self.T_tempXaxisuKErrList[:,i] = self.T_tempXaxisuKErr
                self.T_tempYaxisuKList[:,i] = self.T_tempYaxisuK
                # self.T_tempYaxisuKErrList[:,i] = self.T_tempYaxisuKErr
                self.T_atomNumberArray[:,i] = self.atomNumberArray
                self.T_atomNumberAvList[:,i] =  self.atomNumberAvList
                self.T_atomNumberAvErrList[:,i] = self.atomNumberAvErrList
                self.T_cloudRadiiumArray[:,i] = self.cloudRadiiumArray
                self.T_cloudRadiiumAvList[:,i] = self.cloudRadiiumAvList
                self.T_cloudRadiiumAvErrList[:,i] = self.cloudRadiiumAvErrList
                self.T_cloudAvRadiiumList[:,i] = self.cloudAvRadiiumList
                self.T_cloudPositionsumArray[:,i] = self.cloudPositionsumArray
                self.T_cloudPositionsumAvList[:,i] = self.cloudPositionsumAvList
                self.T_cloudPositionsumAvErrList[:,i] = self.cloudPositionsumAvErrList
                self.T_cloudAvPositionsumList[:,i] = self.cloudAvPositionsumList
                self.atomNumberAvAvList[:,i] = self.atomNumberAvList.mean(axis=(1))
                self.atomNumberAvAvErrList[:,i] = self.atomNumberArray.std(axis=(1,2))/np.sqrt(self.atomNumberArray[0].size)
                self.cloudAvRadiiumAvList[:,i] = self.cloudAvRadiiumList.mean(axis=(1))
                self.cloudAvRadiiumAvErrList[:,i] = self.cloudAvRadiiumList.std(axis=(1))/np.sqrt(self.T_TOFscans)
                self.cloudAvPositionsumAvList[:,i] = self.cloudAvPositionsumList.mean(axis=(1))
                self.cloudAvPositionsumAvErrList[:,i] = self.cloudAvPositionsumList.std(axis=(1))/np.sqrt(self.T_TOFscans)
        if self.T_scans > 1:
            #set right axis to temperature at the end of the scan
            ui.Imaging__plotRightAxisVar.setCurrentIndex(3)
            self.plotRightAxisVar = 3
            # wait 1s to see last scan result before plotting global result
            time.sleep(1.) 
            self.plot_T_measurement_scan()
        return self.scanDone
    
    
    def lifetime_measurement_scan(self, Camera, ui):
        """ Do a scan of lifetime measurements and analysis (Lifetime tab) 
        
        Args: 
            Camera (CameraClass) :  Camera object
            
            ui (UI.Ui_MainWindow) : GUI object to collect and pass variables and graphs
            
        Return:
            If scan performed normally (bool) 
        """
        self.isTemperatureMeas = False
        self.isLifetimeMeas = True
        # clear camera buffer
        Camera.clearBuffer()
        #set left axis to atom number during scan
        ui.Imaging__plotLeftAxisVar.setCurrentIndex(0)
        self.plotLeftAxisVar = 0
        #define result arrays
        self.scanVarName = ui.lineEdit_scanVarName.text()
        self.scanUnitName = ui.lineEdit_scanUnitName.text()
        self.LT_LifetimemsList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_LifetimemsErrList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_atomNumberTStartFittedList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_atomNumberTStartFittedErrList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_atomNumberOffsetFittedList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_atomNumberOffsetFittedErrList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_atomNumberAvTStartList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_atomNumberAvTStartErrList = np.zeros((self.ROIn,self.LT_scans))
        self.LT_atomNumberArray = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,self.LT_averages))
        self.LT_atomNumberAvList =  np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans))
        self.LT_atomNumberAvErrList = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans))
        self.LT_cloudRadiiumArray = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,self.LT_averages,2))
        self.LT_cloudRadiiumAvList = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,2))
        self.LT_cloudRadiiumAvErrList = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,2))
        self.LT_cloudAvRadiiumList = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,2))
        self.LT_cloudPositionsumArray = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,self.LT_averages,2))
        self.LT_cloudPositionsumAvList = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,2))
        self.LT_cloudPositionsumAvErrList = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,2))
        self.LT_cloudAvPositionsumList = np.zeros((self.ROIn,self.LT_scans,self.LT_Tscans,2))
        self.atomNumberAvAvList = np.zeros((self.ROIn,self.LT_scans))
        self.atomNumberAvAvErrList = np.zeros((self.ROIn,self.LT_scans))
        self.cloudAvRadiiumAvList = np.zeros((self.ROIn,self.LT_scans,2))
        self.cloudAvRadiiumAvErrList = np.zeros((self.ROIn,self.LT_scans,2))
        self.cloudAvPositionsumAvList = np.zeros((self.ROIn,self.LT_scans,2))
        self.cloudAvPositionsumAvErrList = np.zeros((self.ROIn,self.LT_scans,2))
        for i in range(self.LT_scans) :
            self.LT_scanIndex = i
            self.scanDone = self.imaging_scan_measurement(Camera, ui, averages=self.LT_averages, 
                                                     scans=self.LT_Tscans)
            if not(self.scanDone) : 
                return False
            else : 
                self.fit_LT_measurement(ui)
                self.plot_LT_measurement()
                self.LT_LifetimemsList[:,i] = self.LT_Lifetimems
                self.LT_LifetimemsErrList[:,i] = self.LT_LifetimemsErr
                self.LT_atomNumberTStartFittedList[:,i] = self.LT_atomNumberTStartFitted
                self.LT_atomNumberTStartFittedErrList[:,i] = self.LT_atomNumberTStartFittedErr
                self.LT_atomNumberOffsetFittedList[:,i] = self.LT_atomNumberOffsetFitted
                self.LT_atomNumberOffsetFittedErrList[:,i] = self.LT_atomNumberOffsetFittedErr
                self.LT_atomNumberAvTStartList[:,i] = self.atomNumberAvList[:,0] 
                self.LT_atomNumberAvTStartErrList[:,i] = self.atomNumberAvErrList[:,0] 
                self.LT_atomNumberArray[:,i] = self.atomNumberArray
                self.LT_atomNumberAvList[:,i] =  self.atomNumberAvList
                self.LT_atomNumberAvErrList[:,i] = self.atomNumberAvErrList
                self.LT_cloudRadiiumArray[:,i] = self.cloudRadiiumArray
                self.LT_cloudRadiiumAvList[:,i] = self.cloudRadiiumAvList
                self.LT_cloudRadiiumAvErrList[:,i] = self.cloudRadiiumAvErrList
                self.LT_cloudAvRadiiumList[:,i] = self.cloudAvRadiiumList
                self.LT_cloudPositionsumArray[:,i] = self.cloudPositionsumArray
                self.LT_cloudPositionsumAvList[:,i] = self.cloudPositionsumAvList
                self.LT_cloudPositionsumAvErrList[:,i] = self.cloudPositionsumAvErrList
                self.LT_cloudAvPositionsumList[:,i] = self.cloudAvPositionsumList
                self.atomNumberAvAvList[:,i] = self.atomNumberAvList.mean(axis=(1))
                self.atomNumberAvAvErrList[:,i] = self.atomNumberArray.std(axis=(1,2))/np.sqrt(self.atomNumberArray[0].size)
                self.cloudAvRadiiumAvList[:,i] = self.cloudAvRadiiumList.mean(axis=(1))
                self.cloudAvRadiiumAvErrList[:,i] = self.cloudAvRadiiumList.std(axis=(1))/np.sqrt(self.LT_Tscans)
                self.cloudAvPositionsumAvList[:,i] = self.cloudAvPositionsumList.mean(axis=(1))
                self.cloudAvPositionsumAvErrList[:,i] = self.cloudAvPositionsumList.std(axis=(1))/np.sqrt(self.LT_Tscans)
        if self.LT_scans > 1:
            #set right axis to Lifetime at the end of the scan
            ui.Imaging__plotRightAxisVar.setCurrentIndex(4)
            self.plotRightAxisVar = 4
            # wait 1s to see last scan result before plotting global result
            time.sleep(1.) 
            self.plot_LT_measurement_scan()
        return self.scanDone

    
    def imaging_scan_measurement(self, Camera, ui, averages=1, scans=1):
        """ Do a one-axis scan of measurements and analysis 
        
        Args: 
            Camera (CameraClass) :  Camera object
            
            ui (UI.Ui_MainWindow) : GUI object to collect and pass variables and graphs
            
        Keyword Args:
            averages=1 (int) : number of averages (atom_imaging) per scan point
            
            scans=1 (int) : lenght of scan axis (number of scan points)
        
        Return:
            If scan performed normally (bool) 
        """
        #define result arrays
        self.atomNumberArray = np.zeros((self.ROIn,scans,averages))
        self.atomNumberAvList =  np.zeros((self.ROIn,scans))
        self.atomNumberAvErrList = np.zeros((self.ROIn,scans))
        self.cloudRadiiumArray = np.zeros((self.ROIn,scans,averages,2))
        self.cloudRadiiumAvList = np.zeros((self.ROIn,scans,2))
        self.cloudRadiiumAvErrList = np.zeros((self.ROIn,scans,2))
        self.cloudAvRadiiumList = np.zeros((self.ROIn,scans,2))
        self.cloudPositionsumArray = np.zeros((self.ROIn,scans,averages,2))
        self.cloudPositionsumAvList = np.zeros((self.ROIn,scans,2))
        self.cloudPositionsumAvErrList = np.zeros((self.ROIn,scans,2))
        self.cloudAvPositionsumList = np.zeros((self.ROIn,scans,2)) 
        for i in range(scans):
            self.scanIndex = i
            self.atomImagingDone = self.atom_imaging(Camera, averages=averages) # calculate OD and atomic density
            if not(self.atomImagingDone) :
                ui.mplwidgetImage.figure.clf()
                ui.mplwidgetImage.draw()
                ui.mplwidgetImage.repaint()
                return False
            else :
                self.atomNumberArray[:,i] = self.atomNumberList 
                self.atomNumberAvList[:,i] = self.atomNumberAv
                ui.lcdNumber_Imaging_NumberofAtomsAv.display(self.atomNumberAv[self.ROIblackTabIndex])
                ui.lcdNumber_T_NumberofAtomsAv.display(self.atomNumberAv[self.ROIblackTabIndex])
                self.atomNumberAvErrList[:,i] = self.atomNumberAvErr
                ui.lcdNumber_Imaging_NumberofAtomsAvErr.display(self.atomNumberAvErr[self.ROIblackTabIndex])
                ui.lcdNumber_T_NumberofAtomsAvErr.display(self.atomNumberAvErr[self.ROIblackTabIndex])
                self.cloudRadiiumArray[:,i] = self.cloudRadiiumList
                self.cloudRadiiumAvList[:,i] = self.cloudRadiiumAv
                ui.lcdNumber_Imaging_CloudRadiusXaxisumAv.display(self.cloudAvRadiium[self.ROIblackTabIndex][1])
                ui.lcdNumber_Imaging_CloudRadiusYaxisumAv.display(self.cloudAvRadiium[self.ROIblackTabIndex][0])
                self.cloudRadiiumAvErrList[:,i] = self.cloudRadiiumAvErr
                ui.lcdNumber_Imaging_CloudRadiusXaxisumAvErr.display(self.cloudRadiiumAvErr[self.ROIblackTabIndex][1])
                ui.lcdNumber_Imaging_CloudRadiusYaxisumAvErr.display(self.cloudRadiiumAvErr[self.ROIblackTabIndex][0])
                self.cloudAvRadiiumList[:,i] = self.cloudAvRadiium
                self.cloudPositionsumArray[:,i] = self.cloudPositionsumList
                self.cloudPositionsumAvList[:,i] = self.cloudPositionsumAv
                ui.lcdNumber_Imaging_CloudPositionXaxisumAv.display(self.cloudAvPositionsum[self.ROIblackTabIndex][1])
                ui.lcdNumber_Imaging_CloudPositionYaxisumAv.display(self.cloudAvPositionsum[self.ROIblackTabIndex][0])
                self.cloudPositionsumAvErrList[:,i] = self.cloudPositionsumAvErr
                ui.lcdNumber_Imaging_CloudPositionXaxisumAvErr.display(self.cloudPositionsumAvErr[self.ROIblackTabIndex][1])
                ui.lcdNumber_Imaging_CloudPositionYaxisumAvErr.display(self.cloudPositionsumAvErr[self.ROIblackTabIndex][0])
                self.cloudAvPositionsumList[:,i] = self.cloudAvPositionsum
                # if standard scan plot dynamically
                if not(self.isTemperatureMeas) and not(self.isLifetimeMeas) : 
                    self.plot_scan_results()
                #update GUI
                ui.widget.repaint()
        return self.atomImagingDone
                
    
    def atom_imaging(self, Camera, averages=1):
        """ Do one point measurements and analysis 
        
        Args: 
            Camera (CameraClass) :  Camera object

        Keyword Args:
            averages=1 (int) : number of averages 
        
        Return:
            If scan performed normally (bool) 
        """
        if self.imagingType == 0 : #absorption
            self.ODeAv *= 0.
            self.crossSectionum2 = 1e+12*self.hplanck*self.atomicFrequencyTHz*1.e+12*self.atomicgamma / self.Isat
            self.coeffAbsStrongSatcalc = float(self.includeSaturationEffects) / self.atomicgamma \
                                          / (self.pixelCalAreaum2 * self.cameraQuantumEff * self.laserPulseDurationus*1.e-6 )
        else : #fluorescence
            self.FluoAv *= 0.
            self.rateScattFluoPerAtom = self.atomicgamma *(self.laserIntensity/self.Isat)\
                                        /(1 + (self.laserIntensity/self.Isat)*float(self.includeSaturationEffects) \
                                            + (2*self.laserDetuningMHz/self.atomicLineFWHWinMHz)**2 )
            self.coeffFluoCalc = 2./( (1-np.sqrt(1-self.numericalAperture**2)) *self.cameraQuantumEff\
                                        *self.laserPulseDurationus*1.e-6\
                                        *self.rateScattFluoPerAtom*self.pixelCalAreaum2)
        self.atomicDensityIntZperum2Av *= 0.
        self.atomNumber = np.zeros(self.ROIn)
        self.cloudRadiium = np.zeros((self.ROIn,2))
        self.cloudPositionspx = np.zeros((self.ROIn,2))
        self.cloudPositionsum = np.zeros((self.ROIn,2))
        self.cloudZonepx = np.zeros((self.ROIn, 2 , 2),dtype=np.int)
        self.atomNumberList = np.zeros((self.ROIn, averages))
        self.cloudRadiiumList = np.zeros((self.ROIn, averages, 2))
        self.cloudPositionspxList = np.zeros((self.ROIn, averages, 2))
        self.cloudPositionsumList = np.zeros((self.ROIn, averages, 2))
        for i in range(averages) :
            self.averageIndex = i
            # flush sensor if asked
            if self.flushSensor :
                Camera.grabArray()
                if Camera.imageAcqLastFailed :
                    return False
            #image with atoms
            self.imAt = Camera.grabArray()
            if Camera.imageAcqLastFailed :
                    return False
            #reference image for absorption imaging
            if self.imagingType == 0 : #absorption
                #flush sensor if asked
                if self.flushSensor :
                    Camera.grabArray()
                    if Camera.imageAcqLastFailed :
                        return False
                #reference image 
                self.imRef = Camera.grabArray()
            if Camera.imageAcqLastFailed :
                    return False
            # take and remove background image if asked
            if self.removeBackground : 
                # flush sensor if asked
                if self.flushSensor :
                    Camera.grabArray()
                    if Camera.imageAcqLastFailed :
                        return False
                #image without light : background
                self.imBkgd = Camera.grabArray()
                if Camera.imageAcqLastFailed :
                        return False
                # remove background without letting negative values
                self.imAt = np.where(self.imAt<self.imBkgd, np.zeros(self.imAt.shape, dtype=self.imageDtype), self.imAt - self.imBkgd)
                self.imRef = np.where(self.imRef<self.imBkgd, np.zeros(self.imRef.shape, dtype=self.imageDtype), self.imRef - self.imBkgd)
            # reckon atomic density
            if self.imagingType == 0 : #absorption
                #calulate ODe sum for average
                self.ODe = - np.log(np.where(self.imAt==0, np.ones(self.imAt.shape), self.imAt.astype(np.float)))\
                                + np.log(np.where(self.imRef==0, np.ones(self.imRef.shape), self.imRef.astype(np.float)))
                self.ODe[self.imRef<self.thresholdAbsImg] = 0.
                self.ODeAv += self.ODe
                #calculate atomic density sum with strong saturation part 
                self.atomicDensityIntZperum2 = self.ODe / self.crossSectionum2 \
                                                + (self.imRef.astype(np.float)-self.imAt.astype(np.float))*self.coeffAbsStrongSatcalc     
                self.atomicDensityIntZperum2[self.imRef<self.thresholdAbsImg] = 0.
            else : #fluorescence
                self.Fluo = self.imAt.astype(np.float)
                self.FluoAv += self.Fluo
                self.atomicDensityIntZperum2 = self.Fluo * self.coeffFluoCalc
            # average integrated atomic density
            self.atomicDensityIntZperum2Av += self.atomicDensityIntZperum2
            # fit cloud dimensions for each ROI
            for ROIi in range(self.ROIn) :
                cloudRadiipx, cloudPositionspx, cloudRadiium, cloudPositionsum = self.fit_Atomic_Cloud_1D(self.atomicDensityIntZperum2, ROIi)
                self.cloudRadiium[ROIi] = cloudRadiium
                self.cloudRadiiumList[ROIi][i] = cloudRadiium
                self.cloudPositionspx[ROIi] = cloudPositionspx
                self.cloudPositionspxList[ROIi][i] = cloudPositionspx
                self.cloudPositionsum[ROIi] = cloudPositionsum
                self.cloudPositionsumList[ROIi][i] = cloudPositionsum
                #calculate atom number : : sum only ROI region : minus on y coordinate because inverted in pixel
                self.cloudZonepx[ROIi] =  self.ROIlimitsTabpx[ROIi]
                # sum only in region of +/- 3 * fitted sigma inside ROI if asked
                if self.atomNumberUseFit3sigma :
                    self.cloudZonepx[ROIi] = np.array([[int(min(max(cloudPositionspx[0]-3*cloudRadiipx[0],self.ROIlimitsTabpx[ROIi][0,0]),self.ROIlimitsTabpx[ROIi][0,1])),
                                                  int(max(min(cloudPositionspx[0]+3*cloudRadiipx[0],self.ROIlimitsTabpx[ROIi][0,1]),self.ROIlimitsTabpx[ROIi][0,0]))],
                                                [int(min(max(cloudPositionspx[1]-3*cloudRadiipx[1],self.ROIlimitsTabpx[ROIi][1,0]),self.ROIlimitsTabpx[ROIi][1,1])),
                                                 int(max(min(cloudPositionspx[1]+3*cloudRadiipx[1],self.ROIlimitsTabpx[ROIi][1,1]),self.ROIlimitsTabpx[ROIi][1,0]))]])
                self.atomNumber[ROIi] = self.atomicDensityIntZperum2[self.cloudZonepx[ROIi][0,0]:self.cloudZonepx[ROIi][0,1],
                                                               self.cloudZonepx[ROIi][1,0]:self.cloudZonepx[ROIi][1,1]].sum()*self.pixelCalAreaum2
                self.atomNumberList[ROIi][i] = self.atomNumber[ROIi]
            # plot each image with atoms if asked for
            if self.plotSingleImage : 
                self.plot_Image_on_mplwidgetImage(self.imAt)
            # save each image if asked for
            if self.autoSaveImages :
                self.save_images_during_atom_imaging(averages=averages)
        #calc average OD
        if self.imagingType == 0 : #absorption
            self.ODeAv /= averages
        else : #fluourescence 
            self.FluoAv /= averages
        self.atomicDensityIntZperum2Av /= averages
        #calculate average atom number error from single measurement fit
        self.atomNumberAvErr = np.std(self.atomNumberList, axis=1)/np.sqrt(averages)
        # calculate average could dimensions and from single measurement fit
        self.cloudRadiiumAv = np.mean(self.cloudRadiiumList,axis=1)
        self.cloudRadiiumAvErr = np.std(self.cloudRadiiumList,axis=1)/np.sqrt(averages)
        self.cloudPositionspxAv = np.mean(self.cloudPositionspxList,axis=1)
        self.cloudPositionsumAv = np.mean(self.cloudPositionsumList,axis=1)
        self.cloudPositionsumAvErr = np.std(self.cloudPositionsumList,axis=1)/np.sqrt(averages)
        #fit average atomic density for each ROI only if averages > 1
        self.cloudAvZonepx = np.zeros((self.ROIn, 2 , 2),dtype=np.int)
        self.cloudAvRadiium  = self.cloudRadiiumAv
        self.cloudAvPositionspx  = self.cloudPositionspxAv
        self.cloudAvPositionsum  = self.cloudPositionsumAv
        self.atomNumberAv = self.atomNumber
        if averages > 1 :
            for ROIi in range(self.ROIn) :
                cloudAvRadiipx, cloudAvPositionspx, cloudAvRadiium, cloudAvPositionsum =\
                                self.fit_Atomic_Cloud_1D(self.atomicDensityIntZperum2Av, ROIi, plotFit1D = self.plotFit1D)
                self.cloudAvRadiium[ROIi] = cloudAvRadiium
                self.cloudAvPositionspx[ROIi] = cloudAvPositionspx
                self.cloudAvPositionsum[ROIi] = cloudAvPositionsum
                # caculate atom number
                self.cloudAvZonepx[ROIi] = self.ROIlimitsTabpx[ROIi] 
                # sum only in region of +/- 3 * fitted sigma inside ROI if asked
                if self.atomNumberUseFit3sigma :
                    self.cloudAvZonepx[ROIi] = np.array([[int(min(max(cloudAvPositionspx[0]-3*cloudAvRadiipx[0],self.ROIlimitsTabpx[ROIi][0,0]),self.ROIlimitsTabpx[ROIi][0,1])),
                                                    int(max(min(cloudAvPositionspx[0]+3*cloudAvRadiipx[0],self.ROIlimitsTabpx[ROIi][0,1]),self.ROIlimitsTabpx[ROIi][0,0]))],
                                                    [int(min(max(cloudAvPositionspx[1]-3*cloudAvRadiipx[1],self.ROIlimitsTabpx[ROIi][1,0]),self.ROIlimitsTabpx[ROIi][1,1])),
                                                     int(max(min(cloudAvPositionspx[1]+3*cloudAvRadiipx[1],self.ROIlimitsTabpx[ROIi][1,1]),self.ROIlimitsTabpx[ROIi][1,0]))]])
                self.atomNumberAv[ROIi] = self.atomicDensityIntZperum2Av[self.cloudAvZonepx[ROIi][0,0]:self.cloudAvZonepx[ROIi][0,1],
                                                                   self.cloudAvZonepx[ROIi][1,0]:self.cloudAvZonepx[ROIi][1,1]].sum()*self.pixelCalAreaum2

        # plot average OD if asked for
        if self.plotAtomicDensityAv :
            self.plot_2Ddata_on_mplwidgetImage(self.atomicDensityIntZperum2Av)
        return True

    
    def fit_Atomic_Cloud_1D(self, atomicDensityIntZperum2, ROIi, plotFit1D = False):
        """ Make fits for estimation of cloud radii, positions with Gaussian functions.
            Fits are done on data integrated along one axis.
            Fits are done a second time with adjusted position and integration width 
            dependin on other axis results.
        
        Args: 
            atomicDensityIntZperum2 (2D numpy array float) : measured atomic density data
            
            ROIi (int) : analysis ROI index (relative to  ROI Tabs)

        Keyword Args:
            plotFit1D = False (bool) : If True, open window to show the 1D fits 
        
        Return:
            cloudRadiipx, cloudPositionspx, cloudRadiium, cloudPositionsum : 
                4-Tuple of 2-list with fit results where the axes are [Y, X]  
        """
        # 
        # fit 1D functions gauss with offset along X and Y axes
        # fit mean of atomic intensity along X axis : Y axis fit 
        fitYaxispx = self.Yaxispx[self.ROIlimitsTabpx[ROIi][0,0]:self.ROIlimitsTabpx[ROIi][0,1]]
        fitYaxisum = self.Yaxisum[self.ROIlimitsTabpx[ROIi][0,0]:self.ROIlimitsTabpx[ROIi][0,1]]
        gaussfitY = fittool.FitUtility(fitYaxispx,
                                        atomicDensityIntZperum2[self.ROIlimitsTabpx[ROIi][0,0]:self.ROIlimitsTabpx[ROIi][0,1],
                                                               self.ROIlimitsTabpx[ROIi][1,0]:self.ROIlimitsTabpx[ROIi][1,1]].mean(axis=1)*1000.,
                                        fittool.gauss)               
        sigmaYpx = int(abs(gaussfitY.p[2]))
        positionYpx = int(gaussfitY.p[1])
        
        # fit mean of atomic intensity along Y axis : X axis fit 
        fitXaxispx = self.Xaxispx[self.ROIlimitsTabpx[ROIi][1,0]:self.ROIlimitsTabpx[ROIi][1,1]]
        fitXaxisum = self.Xaxisum[self.ROIlimitsTabpx[ROIi][1,0]:self.ROIlimitsTabpx[ROIi][1,1]]
        gaussfitX = fittool.FitUtility(fitXaxispx,
                                        atomicDensityIntZperum2[self.ROIlimitsTabpx[ROIi][0,0]:self.ROIlimitsTabpx[ROIi][0,1],
                                                               self.ROIlimitsTabpx[ROIi][1,0]:self.ROIlimitsTabpx[ROIi][1,1]].mean(axis=0)*1000.,
                                        fittool.gauss)  
        sigmaXpx = int(abs(gaussfitX.p[2]))
        positionXpx = int(gaussfitX.p[1])
        
        #do another fit with average only over the rows or collumns within the sigma of the other axis, unless fit failed
        # fit mean of atomic intensity along X axis : Y axis fit 
        if positionXpx < self.ROIlimitsTabpx[ROIi][1,0] or positionXpx > self.ROIlimitsTabpx[ROIi][1,1] : 
            positionXpx = (self.ROIlimitsTabpx[ROIi][1,0] + self.ROIlimitsTabpx[ROIi][1,1] )/2
            sigmaXpx = self.ROIlimitsTabpx[ROIi][1,1] - self.ROIlimitsTabpx[ROIi][1,0]
        Xminpx = int(min(max(positionXpx - sigmaXpx,self.ROIlimitsTabpx[ROIi][1,0]),self.ROIlimitsTabpx[ROIi][1,1]))
        Xmaxpx = int(max(min(positionXpx + sigmaXpx+1, self.ROIlimitsTabpx[ROIi][1,1]),self.ROIlimitsTabpx[ROIi][1,0])) 
        Yfitdata = atomicDensityIntZperum2[self.ROIlimitsTabpx[ROIi][0,0]:self.ROIlimitsTabpx[ROIi][0,1],Xminpx:Xmaxpx].mean(axis=1)*1000.
        gaussfitYpx = fittool.FitUtility(fitYaxispx, Yfitdata, fittool.gauss)
        sigmaYpx = abs(gaussfitYpx.p[2])
        sigmaYum = sigmaYpx*self.pixelCalYumperpx
        positionYpx = gaussfitYpx.p[1]
        positionYum = - (positionYpx-self.hpx/2.)*self.pixelCalYumperpx # minus sign because on plot the Y axis is inverted

        # fit mean of atomic intensity along Y axis : X axis fit 
        if positionYpx < self.ROIlimitsTabpx[ROIi][0,0] or positionYpx > self.ROIlimitsTabpx[ROIi][0,1] : 
            positionYpx = (self.ROIlimitsTabpx[ROIi][0,0] + self.ROIlimitsTabpx[ROIi][0,1] )/2
            sigmaYpx = self.ROIlimitsTabpx[ROIi][0,1] - self.ROIlimitsTabpx[ROIi][0,0]
        Yminpx = int(min(max(positionYpx - sigmaYpx,self.ROIlimitsTabpx[ROIi][0,0]),self.ROIlimitsTabpx[ROIi][0,1]))
        Ymaxpx =  int(max(min(positionYpx + sigmaYpx+1, self.ROIlimitsTabpx[ROIi][0,1]),self.ROIlimitsTabpx[ROIi][0,0])) 
        Xfitdata = atomicDensityIntZperum2[Yminpx:Ymaxpx,self.ROIlimitsTabpx[ROIi][1,0]:self.ROIlimitsTabpx[ROIi][1,1]].mean(axis=0)*1000.
        gaussfitXpx = fittool.FitUtility(fitXaxispx, Xfitdata, fittool.gauss)
        sigmaXpx = abs(gaussfitXpx.p[2])
        sigmaXum = sigmaXpx*self.pixelCalXumperpx
        positionXpx = gaussfitXpx.p[1]
        positionXum = (positionXpx-self.wpx/2.)*self.pixelCalXumperpx

        #plot fit as external plots if wanted
        if plotFit1D :
            #plotting
            fig=plt.figure()
            ax2 = fig.add_subplot(212)
            ax2.plot(-(gaussfitYpx.x-self.hpx/2.)*self.pixelCalYumperpx, gaussfitYpx.y, 'r-', lw = 2)
            ax2.plot(-fitYaxisum,Yfitdata)
            ax2.set_xlabel('Vertical  Yaxis (um)')
            ax2.set_ylabel('Integrated atomic density ')
            ax1 = fig.add_subplot(211)
            ax1.plot((gaussfitXpx.x-self.wpx/2.)*self.pixelCalXumperpx, gaussfitXpx.y, 'g-', lw = 2)
            ax1.plot(fitXaxisum,Xfitdata)
            ax1.set_xlabel('Horizontal Xaxis (um)')
            ax1.set_ylabel('Integrated atomic density ')
            ax1.set_title('Fit of atom cloud dimensions')
            plt.show()
            
        cloudRadiipx = [sigmaYpx , sigmaXpx]
        cloudPositionspx = [positionYpx , positionXpx]
        cloudRadiium = [sigmaYum , sigmaXum]
        cloudPositionsum = [positionYum , positionXum] #relative to center
        return cloudRadiipx, cloudPositionspx, cloudRadiium, cloudPositionsum


    def plot_scan_results(self):
        """Plot results of standard scan (Imaging tab)"""
        # calculate x axis
        self.scan_xaxis = np.arange(self.scans)*self.scanStep + self.scanStart
        self.mplwidgetAnalysisGraph.figure.clf() #clear figure  
        # prepare ROI loop
        plotROIlist = [self.plotROIblack, self.plotROIred, self.plotROIgreen]
        ROItabIndexList = [self.ROIblackTabIndex, self.ROIredTabIndex, self.ROIgreenTabIndex]
        #Left axis
        ax1 = self.mplwidgetAnalysisGraph.figure.add_subplot(111) 
        ax1.set_xlabel(self.scanVarName + ' ['+self.scanUnitName+']')
        # atom number
        if  self.plotLeftAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.scan_xaxis, self.atomNumberAvList[ROItabIndexList[ROIi]], 
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.scan_xaxis, self.atomNumberAvList[ROItabIndexList[ROIi]], 
                                 yerr = self.atomNumberAvErrList[ROItabIndexList[ROIi]], 
                                 color=self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'N')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Atom number, N', color=self.colorL)
        # Cloud radii
        if  self.plotLeftAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1], 
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,1], 
                                 color = self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0], 
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,0], 
                                 color = self.colorL2, linestyle=self.linestyles2[1], 
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorL)
            ax1.legend()
        # Cloud positions
        if  self.plotLeftAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.scan_xaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.scan_xaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1], 
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,1], 
                                 color = self.colorL, linestyle=self.linestyles1[1],
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.scan_xaxis,self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0], 
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.scan_xaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0], 
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,0], 
                                 color = self.colorL2, linestyle=self.linestyles2[1],
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud center positions [µm]',  color=self.colorL)
            ax1.legend()
        # instantiate a second axes that shares the same x-axis
        ax2 = ax1.twinx()  
        # atom number
        if  self.plotRightAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.scan_xaxis, self.atomNumberAvList[ROItabIndexList[ROIi]], 
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.scan_xaxis, self.atomNumberAvList[ROItabIndexList[ROIi]], 
                                 yerr = self.atomNumberAvErrList[ROItabIndexList[ROIi]], 
                                 color=self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'N')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Atom number, N', color=self.colorR)
        # Cloud radii
        if  self.plotRightAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1], 
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,1], 
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.scan_xaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0], 
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,0], 
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorR)
            ax2.legend()
        # Cloud positions
        if  self.plotRightAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.scan_xaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.scan_xaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1], 
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,1], 
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.scan_xaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.scan_xaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0], 
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,0], 
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud center positions [µm]',  color=self.colorR)
            ax2.legend()
        # redraw
        self.mplwidgetAnalysisGraph.draw()
        self.mplwidgetAnalysisGraph.repaint()

            
    def fit_T_measurement(self,ui):
        """Fit results of time of flight scan for temperature measurement
        
        Args:
            ui (UI.Ui_MainWindow) : GUI object to collect and pass variables and graphs
        """
        # time of flight axis        
        self.T_TOFmsaxis = np.arange(self.T_TOFscans)*self.T_TOFstepms + self.T_TOFstartms
        # fit temperature for X axis : use results of fit of average atomic density 'cloudAv'
        self.T_cloudRadiusumXaxis = self.cloudAvRadiiumList[:,:,1] 
        self.T_cloudRadiusumXaxisErr = self.cloudRadiiumAvErrList[:,:,1] 
        #define results arrays 
        self.T_tempXaxisuK = np.zeros(self.ROIn)
        # self.T_tempXaxisuKErr = np.zeros(self.ROIn)
        self.linfitTX_xaxis = np.zeros((self.ROIn, 200))
        self.linfitTX_yaxis = np.zeros((self.ROIn, 200))
        for ROIi in range(self.ROIn) :
            linfitTX = fittool.FitUtility(self.T_TOFmsaxis**2, self.T_cloudRadiusumXaxis[ROIi]**2,
                                               fittool.linear, NumberOfSteps= 200)
            #temperature error estimate not working because fit too dependent on cloud radius error dependence with TOF or if one of the gaussian fit fails
            # if self.T_averages == 1 : 
            # self.T_tempXaxisuKErr[ROIi] = 0.
            #else :
            #    linfitTX = fittool.FitUtility(self.T_TOFmsaxis**2, self.T_cloudRadiusumXaxis[ROIi]**2,
            #                                  fittool.linear, yerr = self.T_cloudRadiusumXaxisErr[ROIi]**2,
            #                                  NumberOfSteps= 200)
            #   self.T_tempXaxisuKErr[ROIi] = linfitTX.psigma[0] * self.atomicMassAU*self.atomicMassUnitinSI / self.kB
            self.T_tempXaxisuK[ROIi] = linfitTX.p[0] * self.atomicMassAU*self.atomicMassUnitinSI / self.kB
            self.linfitTX_xaxis[ROIi] = linfitTX.x
            self.linfitTX_yaxis[ROIi] = linfitTX.y
        ui.lcdNumber_T_TempXaxisuK.display(self.T_tempXaxisuK[self.ROIblackTabIndex])
        # ui.lcdNumber_T_TempXaxisuKErr.display(self.T_tempXaxisuKErr[self.ROIblackTabIndex])
        # fit temperature for Y axis : use results of fit of average atomic density 'cloudAv'
        self.T_cloudRadiusumYaxis = self.cloudAvRadiiumList[:,:,0] 
        self.T_cloudRadiusumYaxisErr = self.cloudRadiiumAvErrList[:,:,0] 
        #define results arrays 
        self.T_tempYaxisuK = np.zeros(self.ROIn)
        # self.T_tempYaxisuKErr = np.zeros(self.ROIn)
        self.linfitTY_xaxis = np.zeros((self.ROIn, 200))
        self.linfitTY_yaxis = np.zeros((self.ROIn, 200))
        for ROIi in range(self.ROIn) :
            #  temperature error estimate not working because fit too dependent on cloud radius error dependence with TOF or if one of the gaussian fit fails
            # if self.T_averages == 1 : 
            linfitTY = fittool.FitUtility(self.T_TOFmsaxis**2, self.T_cloudRadiusumYaxis[ROIi]**2,
                                           fittool.linear, NumberOfSteps= 200)
            # self.T_tempYaxisuKErr[ROIi] = 0.
            # else :
            #     linfitTY = fittool.FitUtility(self.T_TOFmsaxis**2, self.T_cloudRadiusumYaxis[ROIi]**2,
            #                                    fittool.linear, yerr = self.T_cloudRadiusumYaxisErr[ROIi]**2,
            #                                    NumberOfSteps= 200)
            #     self.T_tempYaxisuKErr[ROIi] = linfitTY.psigma[0] * self.atomicMassAU*self.atomicMassUnitinSI / self.kB
            self.T_tempYaxisuK[ROIi] = linfitTY.p[0] * self.atomicMassAU*self.atomicMassUnitinSI / self.kB
            self.linfitTY_xaxis[ROIi] = linfitTY.x
            self.linfitTY_yaxis[ROIi] = linfitTY.y
        ui.lcdNumber_T_TempYaxisuK.display(self.T_tempYaxisuK[self.ROIblackTabIndex])
        # ui.lcdNumber_T_TempYaxisuKErr.display(self.T_tempYaxisuKErr[self.ROIblackTabIndex])
        
        
    def plot_T_measurement(self):
        """Plot results of time of flight scan for temperature measurement"""
        # time of flight axis        
        # plot on analysis graph        
        self.mplwidgetAnalysisGraph.figure.clf()
        # prepare ROI loop
        plotROIlist = [self.plotROIblack, self.plotROIred, self.plotROIgreen]
        ROItabIndexList = [self.ROIblackTabIndex, self.ROIredTabIndex, self.ROIgreenTabIndex]
        #Left axis
        ax1 = self.mplwidgetAnalysisGraph.figure.add_subplot(111)
        ax1.set_xlabel('Time of flight [ms]')
        # atom number
        if  self.plotLeftAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.T_TOFmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.T_TOFmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]],
                                 yerr = self.atomNumberAvErrList[ROItabIndexList[ROIi]],
                                 color=self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'N')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Atom number, N', color=self.colorL)
        # Cloud radii
        if  self.plotLeftAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(np.sqrt(self.linfitTX_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTX_yaxis[ROItabIndexList[ROIi]]),
                             color = self.ROIcolorList[ROIi], linestyle=self.linestylesFit1[0], 
                             label=('X : T = '+ '{:.2f}'.format(self.T_tempXaxisuK[ROItabIndexList[ROIi]]) + ' uK'))
                    ax1.plot(np.sqrt(self.linfitTX_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTX_yaxis[ROItabIndexList[ROIi]]),
                             color=self.colorL, linestyle=self.linestylesFit1[1])
                    ax1.plot(np.sqrt(self.linfitTY_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTY_yaxis[ROItabIndexList[ROIi]]),
                             color = self.ROIcolorList[ROIi], linestyle=self.linestylesFit2[0], 
                             label=('Y : T = '+ '{:.2f}'.format(self.T_tempYaxisuK[ROItabIndexList[ROIi]]) + ' uK'))
                    ax1.plot(np.sqrt(self.linfitTY_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTY_yaxis[ROItabIndexList[ROIi]]),
                             color=self.colorL2, linestyle=self.linestylesFit2[1])
                    ax1.plot(self.T_TOFmsaxis, self.T_cloudRadiusumXaxis[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.T_TOFmsaxis, self.T_cloudRadiusumXaxis[ROItabIndexList[ROIi]],
                                 yerr = self.T_cloudRadiusumXaxisErr[ROItabIndexList[ROIi]],
                                 color = self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X data')
                    ax1.plot(self.T_TOFmsaxis, self.T_cloudRadiusumYaxis[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.T_TOFmsaxis, self.T_cloudRadiusumYaxis[ROItabIndexList[ROIi]],
                                 yerr = self.T_cloudRadiusumYaxisErr[ROItabIndexList[ROIi]],
                                 color = self.colorL2, linestyle=self.linestyles2[1], 
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y data')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorL)
            ax1.legend()
        # Cloud positions
        if  self.plotLeftAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1], 
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorL, linestyle=self.linestyles1[1],
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorL2, linestyle=self.linestyles2[1],
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud center positions [µm]',  color=self.colorL)
            ax1.legend()
        # instantiate a second axes that shares the same x-axis
        ax2 = ax1.twinx()  
        # atom number
        if  self.plotRightAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.T_TOFmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.T_TOFmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]],
                                 yerr = self.atomNumberAvErrList[ROItabIndexList[ROIi]],
                                 color=self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'N')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Atom number, N', color=self.colorR)
        # Cloud radii
        if  self.plotRightAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(np.sqrt(self.linfitTX_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTX_yaxis[ROItabIndexList[ROIi]]),
                             color = self.ROIcolorList[ROIi], linestyle=self.linestylesFit1[0], 
                             label=('X : T = '+ '{:.2f}'.format(self.T_tempXaxisuK[ROItabIndexList[ROIi]]) + ' uK'))
                    ax2.plot(np.sqrt(self.linfitTX_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTX_yaxis[ROItabIndexList[ROIi]]),
                             color=self.colorR, linestyle=self.linestylesFit1[1])
                    ax2.plot(np.sqrt(self.linfitTY_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTY_yaxis[ROItabIndexList[ROIi]]),
                             color = self.ROIcolorList[ROIi], linestyle=self.linestylesFit2[0], 
                             label=('Y : T = '+ '{:.2f}'.format(self.T_tempYaxisuK[ROItabIndexList[ROIi]]) + ' uK'))
                    ax2.plot(np.sqrt(self.linfitTY_xaxis[ROItabIndexList[ROIi]]), np.sqrt(self.linfitTY_yaxis[ROItabIndexList[ROIi]]),
                             color=self.colorR2, linestyle=self.linestylesFit2[1])
                    ax2.plot(self.T_TOFmsaxis, self.T_cloudRadiusumXaxis[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.T_TOFmsaxis, self.T_cloudRadiusumXaxis[ROItabIndexList[ROIi]],
                                 yerr = self.T_cloudRadiusumXaxisErr[ROItabIndexList[ROIi]],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X data')
                    ax2.plot(self.T_TOFmsaxis, self.T_cloudRadiusumYaxis[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.T_TOFmsaxis, self.T_cloudRadiusumYaxis[ROItabIndexList[ROIi]], 
                                 yerr = self.T_cloudRadiusumYaxisErr[ROItabIndexList[ROIi]],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y data')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorR)
            ax2.legend()
        # Cloud positions
        if  self.plotRightAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.T_TOFmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud center positions [µm]',  color=self.colorR)
            ax2.legend()
        #redraw
        self.mplwidgetAnalysisGraph.draw()
        self.mplwidgetAnalysisGraph.repaint()


    def plot_T_measurement_scan(self):
        # calculate x axis
        self.T_scan_xaxis = np.arange(self.T_scans)*self.T_scanStep + self.T_scanStart
        # plot on analysis graph        
        self.mplwidgetAnalysisGraph.figure.clf()
        # prepare ROI loop
        plotROIlist = [self.plotROIblack, self.plotROIred, self.plotROIgreen]
        ROItabIndexList = [self.ROIblackTabIndex, self.ROIredTabIndex, self.ROIgreenTabIndex]
        # left axis
        ax1 = self.mplwidgetAnalysisGraph.figure.add_subplot(111)
        ax1.set_xlabel(self.scanVarName + ' ['+self.scanUnitName+']')
        # atom number
        if  self.plotLeftAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.T_scan_xaxis, self.atomNumberAvAvList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.T_scan_xaxis, self.atomNumberAvAvList[ROItabIndexList[ROIi]],
                                 yerr = self.atomNumberAvAvErrList[ROItabIndexList[ROIi]],
                                 color=self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'N')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Atom number, N', color=self.colorL)
        # Cloud radii
        if  self.plotLeftAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorL2, linestyle=self.linestyles2[1], 
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorL)
            ax1.legend()
        # Cloud positions
        if  self.plotLeftAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorL, linestyle=self.linestyles1[1],
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorL2, linestyle=self.linestyles2[1],
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud center positions [µm]',  color=self.colorL) 
            ax1.legend()
        # Temperature
        if  self.plotLeftAxisVar == 3 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.T_scan_xaxis, self.T_tempXaxisuKList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.T_scan_xaxis, self.T_tempXaxisuKList[ROItabIndexList[ROIi]],
                                 # yerr = self.T_tempXaxisuKErrList[ROItabIndexList[ROIi]], 
                                 color = self.colorL, linestyle=self.linestyles1[1],
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.T_scan_xaxis, self.T_tempYaxisuKList[ROItabIndexList[ROIi]], 
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.T_scan_xaxis, self.T_tempYaxisuKList[ROItabIndexList[ROIi]], 
                                 # yerr = self.T_tempYaxisuKErrList[ROItabIndexList[ROIi]], 
                                 color = self.colorL2, linestyle=self.linestyles2[1],
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Temperature [uK]',  color=self.colorL)
            ax1.legend()
        # instantiate a second axes that shares the same x-axis
        ax2 = ax1.twinx()  
        # atom number
        if  self.plotRightAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.T_scan_xaxis, self.atomNumberAvAvList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.T_scan_xaxis, self.atomNumberAvAvList[ROItabIndexList[ROIi]],
                                 yerr = self.atomNumberAvAvErrList[ROItabIndexList[ROIi]],
                                 color=self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'N')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Atom number, N', color=self.colorR)
        # Cloud radii
        if  self.plotRightAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.T_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0], 
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorR)
            ax2.legend()
        # Cloud positions
        if  self.plotRightAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.T_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud center positions [µm]',  color=self.colorR) 
            ax2.legend()
        # Temperature
        if  self.plotRightAxisVar == 3 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.T_scan_xaxis, self.T_tempXaxisuKList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.T_scan_xaxis, self.T_tempXaxisuKList[ROItabIndexList[ROIi]],
                                 # yerr = self.T_tempXaxisuKErrList[ROItabIndexList[ROIi]],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.T_scan_xaxis, self.T_tempYaxisuKList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.T_scan_xaxis, self.T_tempYaxisuKList[ROItabIndexList[ROIi]],
                                 # yerr = self.T_tempYaxisuKErrList[ROItabIndexList[ROIi]],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Temperature [uK]',  color=self.colorR)
            ax2.legend()
        #redraw
        self.mplwidgetAnalysisGraph.draw()
        self.mplwidgetAnalysisGraph.repaint()
        
        

    def fit_LT_measurement(self,ui):
        """Fit exponential atom number decay for lifetime measurement
        
        Args:
            ui (UI.Ui_MainWindow) : GUI object to collect and pass variables and graphs
        """
        # time axis        
        self.LT_Tmsaxis = np.arange(self.LT_Tscans)*self.LT_Tstepms + self.LT_Tstartms
        # define arrays
        self.LT_Lifetimems = np.zeros(self.ROIn)
        self.LT_atomNumberTStartFitted = np.zeros(self.ROIn)
        self.LT_atomNumberOffsetFitted = np.zeros(self.ROIn)
        self.expfitLT_xaxis = np.zeros((self.ROIn, 200))
        self.expfitLT_yaxis = np.zeros((self.ROIn, 200))
        self.LT_LifetimemsErr = np.zeros(self.ROIn)
        self.LT_atomNumberTStartFittedErr = np.zeros(self.ROIn)
        self.LT_atomNumberOffsetFittedErr = np.zeros(self.ROIn)
        # fit exponential decay  
        for ROIi in range(self.ROIn) :
            if self.LT_averages == 1 : 
                expfitLT = fittool.FitUtility(self.LT_Tmsaxis, self.atomNumberAvList[ROIi],
                                               fittool.expdecay, NumberOfSteps= 200)
            else :
                expfitLT = fittool.FitUtility(self.LT_Tmsaxis, self.atomNumberAvList[ROIi],
                                               fittool.expdecay, yerr = self.atomNumberAvErrList[ROIi],
                                               NumberOfSteps= 200)
                if not(expfitLT.psigma is None) : 
                    self.LT_LifetimemsErr[ROIi] = expfitLT.psigma[1]
                    self.LT_atomNumberTStartFittedErr[ROIi] = expfitLT.psigma[0]
                    self.LT_atomNumberOffsetFittedErr[ROIi] = expfitLT.psigma[2]
            self.LT_Lifetimems[ROIi] = expfitLT.p[1]
            self.LT_atomNumberTStartFitted[ROIi] = expfitLT.p[0]
            self.LT_atomNumberOffsetFitted[ROIi] = expfitLT.p[2]
            self.expfitLT_xaxis[ROIi] = expfitLT.x
            self.expfitLT_yaxis[ROIi] = expfitLT.y
        ui.lcdNumber_LT_Lifetimems.display(self.LT_Lifetimems[self.ROIblackTabIndex])
        ui.lcdNumber_LT_LifetimemsErr.display(self.LT_LifetimemsErr[self.ROIblackTabIndex])
        ui.lcdNumber_LT_atomNumberTStartFitted.display(self.LT_atomNumberTStartFitted[self.ROIblackTabIndex])
        ui.lcdNumber_LT_atomNumberTStartFittedErr.display(self.LT_atomNumberTStartFittedErr[self.ROIblackTabIndex])
        ui.lcdNumber_LT_atomNumberOffsetFitted.display(self.LT_atomNumberOffsetFitted[self.ROIblackTabIndex])
        ui.lcdNumber_LT_atomNumberOffsetFittedErr.display(self.LT_atomNumberOffsetFittedErr[self.ROIblackTabIndex])
        
        
    def plot_LT_measurement(self):
        """Plot results of time scan for lifetime measurement"""
        # time axis        
        # plot on analysis graph        
        self.mplwidgetAnalysisGraph.figure.clf()
        # prepare ROI loop
        plotROIlist = [self.plotROIblack, self.plotROIred, self.plotROIgreen]
        ROItabIndexList = [self.ROIblackTabIndex, self.ROIredTabIndex, self.ROIgreenTabIndex]
        #Left axis
        ax1 = self.mplwidgetAnalysisGraph.figure.add_subplot(111)
        ax1.set_xlabel('Time [ms]')
        # atom number
        if  self.plotLeftAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.expfitLT_xaxis[ROItabIndexList[ROIi]], self.expfitLT_yaxis[ROItabIndexList[ROIi]],
                             color = self.ROIcolorList[ROIi], linestyle=self.linestylesFit1[0], 
                             label = ('Fitted Lifetime = '+ '{:.1f}'.format(self.LT_Lifetimems[ROItabIndexList[ROIi]]) + ' ms'))
                    ax1.plot(self.expfitLT_xaxis[ROItabIndexList[ROIi]], self.expfitLT_yaxis[ROItabIndexList[ROIi]],
                             color = self.colorL, linestyle=self.linestylesFit1[1] )
                    ax1.plot(self.LT_Tmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.LT_Tmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]],
                                 yerr = self.atomNumberAvErrList[ROItabIndexList[ROIi]],
                                 color=self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Measured')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Atom number', color=self.colorL)
            ax1.legend()
        # Cloud radii
        if  self.plotLeftAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorL2, linestyle=self.linestyles2[1], 
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorL)
            ax1.legend()
        # Cloud positions
        if  self.plotLeftAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorL, linestyle=self.linestyles1[1],
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorL2, linestyle=self.linestyles2[1],
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud center positions [µm]',  color=self.colorL)
            ax1.legend()
        # instantiate a second axes that shares the same x-axis
        ax2 = ax1.twinx()  
        # atom number
        if  self.plotRightAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.expfitLT_xaxis[ROItabIndexList[ROIi]], self.expfitLT_yaxis[ROItabIndexList[ROIi]],
                             color = self.ROIcolorList[ROIi], linestyle=self.linestylesFit1[0], 
                             label = ('Fitted Lifetime = '+ '{:.1f}'.format(self.LT_Lifetimems[ROItabIndexList[ROIi]]) + ' ms'))
                    ax2.plot(self.expfitLT_xaxis[ROItabIndexList[ROIi]], self.expfitLT_yaxis[ROItabIndexList[ROIi]],
                             color = self.colorR, linestyle=self.linestylesFit1[1] )
                    ax2.plot(self.LT_Tmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.LT_Tmsaxis, self.atomNumberAvList[ROItabIndexList[ROIi]], 
                                 yerr = self.atomNumberAvErrList[ROItabIndexList[ROIi]], 
                                 color=self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Measured')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Atom number', color=self.colorR)
            ax2.legend()
        # Cloud radii
        if  self.plotRightAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.LT_Tmsaxis, self.cloudAvRadiiumList[ROItabIndexList[ROIi]][:,0], 
                                 yerr = self.cloudRadiiumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorR)
            ax2.legend()
        # Cloud positions
        if  self.plotRightAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.LT_Tmsaxis, self.cloudAvPositionsumList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud center positions [µm]',  color=self.colorR)
            ax2.legend()
        #redraw
        self.mplwidgetAnalysisGraph.draw()
        self.mplwidgetAnalysisGraph.repaint()


    def plot_LT_measurement_scan(self):
        # calculate x axis
        self.LT_scan_xaxis = np.arange(self.LT_scans)*self.LT_scanStep + self.LT_scanStart
        # plot on analysis graph        
        self.mplwidgetAnalysisGraph.figure.clf()
        # prepare ROI loop
        plotROIlist = [self.plotROIblack, self.plotROIred, self.plotROIgreen]
        ROItabIndexList = [self.ROIblackTabIndex, self.ROIredTabIndex, self.ROIgreenTabIndex]
        # left axis
        ax1 = self.mplwidgetAnalysisGraph.figure.add_subplot(111)
        ax1.set_xlabel(self.scanVarName + ' ['+self.scanUnitName+']')
        # atom number
        if  self.plotLeftAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.LT_scan_xaxis, self.LT_atomNumberAvTStartList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.LT_scan_xaxis, self.LT_atomNumberAvTStartList[ROItabIndexList[ROIi]],
                                 yerr = self.LT_atomNumberAvTStartErrList[ROItabIndexList[ROIi]],
                                 color=self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Measured')
                    ax1.plot(self.LT_scan_xaxis, self.LT_atomNumberTStartFittedList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.LT_scan_xaxis, self.LT_atomNumberTStartFittedList[ROItabIndexList[ROIi]], 
                                 yerr = self.LT_atomNumberTStartFittedErrList[ROItabIndexList[ROIi]], 
                                 color=self.colorL2, linestyle=self.linestyles2[1], 
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Fitted')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Atom number at Time Start', color=self.colorL)
            ax1.legend()
        # Cloud radii
        if  self.plotLeftAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorL, linestyle=self.linestyles1[1], 
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorL2, linestyle=self.linestyles2[1], 
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorL)
            ax1.legend()
        # Cloud positions
        if  self.plotLeftAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorL, linestyle=self.linestyles1[1],
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax1.plot(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax1.errorbar(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorL2, linestyle=self.linestyles2[1],
                                 marker=self.markerL2, ms = self.markerSize , markerfacecolor=self.colorL2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Cloud center positions [µm]',  color=self.colorL)
            ax1.legend()
        # Lifetime
        if  self.plotLeftAxisVar == 4 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax1.plot(self.LT_scan_xaxis, self.LT_LifetimemsList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax1.errorbar(self.LT_scan_xaxis, self.LT_LifetimemsList[ROItabIndexList[ROIi]], 
                                 yerr = self.LT_LifetimemsErrList[ROItabIndexList[ROIi]], 
                                 color = self.colorL, linestyle=self.linestyles1[1],
                                 marker=self.markerL1, ms = self.markerSize , markerfacecolor=self.colorL,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'ROI')
            ax1.tick_params(axis='y', colors=self.colorL)
            ax1.set_ylabel('Lifetime [ms]',  color=self.colorL)
            ax1.legend()
        # instantiate a second axes that shares the same x-axis
        ax2 = ax1.twinx()  
        # atom number
        if  self.plotRightAxisVar == 0 :
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.LT_scan_xaxis, self.LT_atomNumberAvTStartList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.LT_scan_xaxis, self.LT_atomNumberAvTStartList[ROItabIndexList[ROIi]],
                                 yerr = self.LT_atomNumberAvTStartErrList[ROItabIndexList[ROIi]],
                                 color=self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Measured')
                    ax2.plot(self.LT_scan_xaxis, self.LT_atomNumberTStartFittedList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.LT_scan_xaxis, self.LT_atomNumberTStartFittedList[ROItabIndexList[ROIi]],
                                 yerr = self.LT_atomNumberTStartFittedErrList[ROItabIndexList[ROIi]],
                                 color=self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Fitted')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Atom number at Time Start', color=self.colorR)
            ax2.legend()
        # Cloud radii
        if  self.plotRightAxisVar == 1 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.LT_scan_xaxis, self.cloudAvRadiiumAvList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudAvRadiiumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud radii (gaussian sigma) [µm]',  color=self.colorR)
            ax2.legend()
        # Cloud positions
        if  self.plotRightAxisVar == 2 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,1],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,1],
                                 color = self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'X')
                    ax2.plot(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles2[0])
                    ax2.errorbar(self.LT_scan_xaxis, self.cloudAvPositionsumAvList[ROItabIndexList[ROIi]][:,0],
                                 yerr = self.cloudAvPositionsumAvErrList[ROItabIndexList[ROIi]][:,0],
                                 color = self.colorR2, linestyle=self.linestyles2[1],
                                 marker=self.markerR2, ms = self.markerSize , markerfacecolor=self.colorR2,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'Y')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Cloud center positions [µm]',  color=self.colorR)
            ax2.legend()
        # Lifetime
        if  self.plotRightAxisVar == 4 : 
            for ROIi in range(3):
                if plotROIlist[ROIi] :
                    ax2.plot(self.LT_scan_xaxis, self.LT_LifetimemsList[ROItabIndexList[ROIi]],
                                 color=self.ROIcolorList[ROIi], linestyle=self.linestyles1[0])
                    ax2.errorbar(self.LT_scan_xaxis, self.LT_LifetimemsList[ROItabIndexList[ROIi]],
                                 yerr = self.LT_LifetimemsErrList[ROItabIndexList[ROIi]],
                                 color=self.colorR, linestyle=self.linestyles1[1],
                                 marker=self.markerR1, ms = self.markerSize , markerfacecolor=self.colorR,
                                 markeredgewidth = self.markerEdgeWidth, markeredgecolor=self.ROIcolorList[ROIi], 
                                 ecolor = self.ROIcolorList[ROIi],
                                 label= 'ROI')
            ax2.tick_params(axis='y', colors=self.colorR)
            ax2.set_ylabel('Lifetime [ms]',  color=self.colorR)
        #redraw()
        self.mplwidgetAnalysisGraph.draw()
        self.mplwidgetAnalysisGraph.repaint()


    def plotAnalysis_update(self):
        """ Update the analysis (right) graph. Used after changes in Plot tab. """
        if self.isTemperatureMeas : 
            if self.T_scans > 1 :
                self.plot_T_measurement_scan()
            else :
                self.plot_T_measurement()
        elif self.isLifetimeMeas :
            if self.LT_scans >1 :
                self.plot_LT_measurement_scan()
            else : 
                self.plot_LT_measurement()
        else : 
            self.plot_scan_results()


    def plot_Image_on_mplwidgetImage(self, imageToPlot, title = 'Camera image'):
        """ Show a camera image on the left graph in grey colorscale.
        
        Args:
            imageToPlot (2D numpy array) : image to plot
            
        Keyword Args:
            title = 'Camera image' (str) : Title for the left graph
        """
        self.mplwidgetImage.figure.clf()# clear figure
        self.mplwidgetImage.axes = self.mplwidgetImage.figure.add_subplot(111)
        self.mplwidgetImage.axes.imshow(imageToPlot,
                                        cmap = matplotlib.cm.Greys_r,
                                        vmin =0.,
                                        vmax=self.cameraMaxLevel,
                                        origin='upper',
                                        extent = self.imageLimits,
                                        interpolation='none')
        self.mplwidgetImage.axes.set_xlabel('X - direction [microns]')
        self.mplwidgetImage.axes.set_ylabel('Y - direction [microns]')
        self.mplwidgetImage.axes.set_title(title)
        #draw black ROI
        if self.drawROIblack :
            self.mplwidgetImage.axes.add_patch(\
                patches.Rectangle((self.ROIlimitsTabum[self.ROIblackTabIndex,1,0],self.ROIlimitsTabum[self.ROIblackTabIndex,0,0]),
                                  self.ROIlimitsTabum[self.ROIblackTabIndex,1,1]-self.ROIlimitsTabum[self.ROIblackTabIndex,1,0],
                                  self.ROIlimitsTabum[self.ROIblackTabIndex,0,1]-self.ROIlimitsTabum[self.ROIblackTabIndex,0,0],
                                fill=False, edgecolor=self.ROIcolorList[0]))
        #draw red ROI
        if self.drawROIred :
            self.mplwidgetImage.axes.add_patch(\
                patches.Rectangle((self.ROIlimitsTabum[self.ROIredTabIndex,1,0],self.ROIlimitsTabum[self.ROIredTabIndex,0,0]),
                                  self.ROIlimitsTabum[self.ROIredTabIndex,1,1]-self.ROIlimitsTabum[self.ROIredTabIndex,1,0],
                                  self.ROIlimitsTabum[self.ROIredTabIndex,0,1]-self.ROIlimitsTabum[self.ROIredTabIndex,0,0],
                                fill=False, edgecolor=self.ROIcolorList[1]))
        #draw green ROI
        if self.drawROIgreen :
            self.mplwidgetImage.axes.add_patch(\
                patches.Rectangle((self.ROIlimitsTabum[self.ROIgreenTabIndex,1,0],self.ROIlimitsTabum[self.ROIgreenTabIndex,0,0]),
                                  self.ROIlimitsTabum[self.ROIgreenTabIndex,1,1]-self.ROIlimitsTabum[self.ROIgreenTabIndex,1,0],
                                  self.ROIlimitsTabum[self.ROIgreenTabIndex,0,1]-self.ROIlimitsTabum[self.ROIgreenTabIndex,0,0],
                                fill=False, edgecolor=self.ROIcolorList[2]))
        self.mplwidgetImage.axes.set_xlim(left=self.imageLimits[0], 
                                             right=self.imageLimits[1])
        self.mplwidgetImage.axes.set_ylim(bottom=self.imageLimits[2], 
                                             top=self.imageLimits[3])
        self.mplwidgetImage.draw()
        self.mplwidgetImage.repaint()


    def plot_2Ddata_on_mplwidgetImage(self, data2D, title='Atomic density [atoms/micron^2]'):
        """ Show 2Ddata on the left graph in jet colorscale.
        
        Args:
            data2D (2D numpy array) : 2D data to plot
            
        Keyword Args:
            title = 'Atomic density [atoms/micron^2]' (str) : Title for the left graph
        """
        self.mplwidgetImage.figure.clf()# clear figure to avoid double scale bar 
        self.mplwidgetImage.axes = self.mplwidgetImage.figure.add_subplot(111)
        imsh = self.mplwidgetImage.axes.imshow(data2D,
                                        cmap = matplotlib.cm.jet,
                                        origin='upper',
                                        extent = self.imageLimits,
                                        interpolation='none')
        self.mplwidgetImage.axes.set_xlabel('X - direction [microns]')
        self.mplwidgetImage.axes.set_ylabel('Y - direction [microns]')
        self.mplwidgetImage.axes.set_title(title)
        self.mplwidgetImage.figure.colorbar(imsh)
        #draw black ROI
        if self.drawROIblack :
            self.mplwidgetImage.axes.add_patch(\
                patches.Rectangle((self.ROIlimitsTabum[self.ROIblackTabIndex,1,0],self.ROIlimitsTabum[self.ROIblackTabIndex,0,0]),
                                  self.ROIlimitsTabum[self.ROIblackTabIndex,1,1]-self.ROIlimitsTabum[self.ROIblackTabIndex,1,0],
                                  self.ROIlimitsTabum[self.ROIblackTabIndex,0,1]-self.ROIlimitsTabum[self.ROIblackTabIndex,0,0],
                                fill=False, edgecolor=self.ROIcolorList[0]))
        #draw red ROI
        if self.drawROIred :
            self.mplwidgetImage.axes.add_patch(\
                patches.Rectangle((self.ROIlimitsTabum[self.ROIredTabIndex,1,0],self.ROIlimitsTabum[self.ROIredTabIndex,0,0]),
                                  self.ROIlimitsTabum[self.ROIredTabIndex,1,1]-self.ROIlimitsTabum[self.ROIredTabIndex,1,0],
                                  self.ROIlimitsTabum[self.ROIredTabIndex,0,1]-self.ROIlimitsTabum[self.ROIredTabIndex,0,0],
                                fill=False, edgecolor=self.ROIcolorList[1]))
        #draw green ROI
        if self.drawROIgreen :
            self.mplwidgetImage.axes.add_patch(\
                patches.Rectangle((self.ROIlimitsTabum[self.ROIgreenTabIndex,1,0],self.ROIlimitsTabum[self.ROIgreenTabIndex,0,0]),
                                  self.ROIlimitsTabum[self.ROIgreenTabIndex,1,1]-self.ROIlimitsTabum[self.ROIgreenTabIndex,1,0],
                                  self.ROIlimitsTabum[self.ROIgreenTabIndex,0,1]-self.ROIlimitsTabum[self.ROIgreenTabIndex,0,0],
                                fill=False, edgecolor=self.ROIcolorList[2]))
        self.mplwidgetImage.axes.set_xlim(left=self.imageLimits[0], 
                                             right=self.imageLimits[1])
        self.mplwidgetImage.axes.set_ylim(bottom=self.imageLimits[2], 
                                             top=self.imageLimits[3])
        self.mplwidgetImage.draw()
        self.mplwidgetImage.repaint()

            



















        