
Installation
************

Requirements
============

The basic requirements are :

* `Python 3 <https://docs.python.org/3>`_ to run the code with the following packages included,

* `NumPy <https://numpy.org/doc/stable/>`_ for basic computations and overall array interface,

* `PyQt5 <https://www.riverbankcomputing.com/static/Docs/PyQt5/>`_ for the graphical user interface,

* `Matplotlib <https://matplotlib.org/stable/>`_ for plotting.

The program has been tested with Python 3.10 within `Anaconda <https://www.anaconda.com/>`_ distribution version 2023.03-1 and Windows 64 bits. 
The main reason for this choice is dictated by the latest FLIR camera driver using Python 3.10 at the time of development, 
and Anaconda version 2023.03-1 is the latest providing Python 3.10. 

The archive of Anaconda distributions is available `here <https://repo.anaconda.com/archive/>`_ .


Getting CAtImaPy code
=====================

CAtImaPy can be downloaded from `CAtImaPy GitHub repository <https://github.com/SebastienGarciaAissa/CAtImaPy.git>`_. 

Click on *Code* and select *Download ZIP*. Unzip and place the CAtImaPy folder wherever you want.

Alternatively (in particular if you want to contribute), you can use Git to clone the repository::

    git clone https://github.com/SebastienGarciaAissa/CAtImaPy


Installing Camera drivers
=========================

The next step is to setup the driver for your camera(s). 
Below, you will find a generic description of the steps to get a camera driver settled in CAtImaPy. 
Precise instructions, depending on the camera manufacturer, are available in section :ref:`Camera-drivers`.

#.  The control of a camera uses a library of funcions (driver) defined and written by the manufacturer. 
    The first step is then to install the driver.
    Most of the time, this means installing the software development kit (SDK) provided by the manufacturer on its website.
    
#.  On top of this driver, providing most of the time C functions, 
    we need a python driver accessing these functions. 
    In CAtImaPy code, there are two different ways to get this layer:

        * some implemented drivers rely on a python package provided by the manufacturer. It could also be written by a third party or you, if needed.
        
        * most of implemented drivers use the amazing `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package developed by Alexey Shkarin. 
          This software is a python package for controlling lab equipement in general. 
          We use here its control of cameras because most of scientific cameras are controllable via PyLabLib. 
        
        .. note::
            Alexey Shkarin also developed a separate, stand-alone software `PyLabLib cam-control <https://pylablib-cam-control.readthedocs.io/en/latest/>`_
            for universal camera control and frames acquisition with a convenient GUI. 
    
#.  The final layer for camera control are CAtImaPy specific drivers located in *Cameras* folder.
    Using the previous layer of python drivers, these drivers provide a unified interface for the rest of the code 
    (details in section :ref:`Cameras-code`, if you are interested).
    CAtImaPy implement generic drivers classes for camera operated via a given manufacturer's driver. 
    Theses CAtImaPy's drivers are python classes ``<Driver name>Class`` defined in *<Driver name>.py* files in *Cameras* directory. 
    
    These generic driver classes are intended to be used as a parent class for model specific classes ``<Model name>Class`` defined in the same file.
    When implementing a new camera model for your application, I recommend creating such a model class. 
    The model class will allow to implement a customizable initialization procedure for the given camera model. 
    Even if you do not need this at start, it may come useful at some point latter. 
    Examples of basic inherited model classes are given in section :ref:`Model-Camera-classes`.


Configuring camera and acquisition parameters
==============================================

The last step before launching the program is to configure the parameters of your camera(s). 

To do so, open file *Cameras\Config.py* in an editor. 
This file only contains the definition of ``camerasConfigs`` : a list of dictionnaries each configuring one camera. 
Leave the first element of the list (index 0) as :py:const:`None` because Camera 0 indicates that no actual camera is connected (at start or if connection fails). 

Go to the dictionnary defintion at list index 1, below the commented line ::
    
    # Camera number 1

And modify the variables values after the = signs to match the ones of your camera. 
The variables are listed below with their key (name of dictionnary variable in python), the expected value type, their meaning and their use :

* name (:py:class:`str`) : Name chosen by user. Only used to reckonize camera number in the list of configured cameras.

* driver (:py:class:`str`) : Driver name has to be the name of a file *<driver>.py* in *Cameras* folder, and is related to a given manufacturer's driver. 
  Used to find the python class controlling the camera.

* model (:py:class:`str`) : Model name has to be the name of class ``<model>Class`` defined in <driver>.py file.
  Used to load specific child class (if :py:const:`None` or not matching  use generic ``<driver>Class``).

* serial (:py:class:`int` or :py:class:`str`) : Serial number of the camera (or for some drivers the camera index). 
  Used to identify the camera at connection.

* imageBitDepth (:py:class:`int`) : Set bit depth of sensor reading. 
  Used to set the format of image transfered by the camera to the computer. 
  Only if the driver allows it, otherwise the format is set automatically according to camera.
                 
* defaultExposurems (:py:class:`float`) : Default duration of exposition (exposure) in milliseconds.
  Used at each camera connection for initial configuration of the camera if "Load camera default from config" is checked.

* defaultGaindB (:py:class:`float`) : Default hardware gain (amplification) at sensor read in dB, if gain is avaible for this camera.
  Used at each camera connection for initial configuration of the camera if "Load camera default from config" is checked.

* defaultTrigger ('external' or 'software') : Default input for triggering the camera.
  Used at each camera connection for initial configuration of the camera if "Load camera default from config" is checked.
  Normally should be 'external' to trigger on digital signal rising up provided by hardware used for experiment control.

* defaultCamROI (:py:const:`None` or [:py:class:`int`]*4) : Camera region of interest to read from sensor : 
  None for full senseor or [x offset , y offset , x size , y size ] in pixels (binning is not implemented so far).
  This parameter can only be changed via ``camerasConfigs`` (not yet implemented in the GUI).

* defaultFlushSensor (:py:class:`bool`) : Default setting to decide if each image acquisition is preceded by a flush read of the camera,
  to remove accumulated charges on sensor. 
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.

* defaultRemoveBackground (:py:class:`bool`) : Default setting to decide if a background image is taken and removed to the previous one(s),
  at the end of a cold-atom imaging cycle.
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.
  
* defaultROIkrgnames  ([:py:class:`str`]*3) : Names of analysis ROIs that the code try to find in the ROI array 
  and select as the [black, red, green] imaging ROIs used to show results.
  Used at first camera connection (or reconnection if another camera was used previously).

* pixelCalXumperpx (:py:class:`float`) : Calibration of width of a pixel in the object plane in micrometers.

* pixelCalYumperpx (:py:class:`float`) : Calibration of height of a pixel in the object plane in micrometers.
  
* reversedAxes ([:py:class:`bool`]*2) :  Decide if for each axis [X,Y], if it will be reversed. 
  This allows you to swap the images axes the way you like ; for example to get the atoms falling to the bottom of the image. 
  
* cameraQuantumEff (:py:class:`float`) :  Quantum efficiency of the camera (or effective efficiency if sets bit depth limits the format).
  Used to calculate the number of photon per pixel from the number of recorded electrons. This allows to know the absolute intensity reaching the sensor.
  The absolute intensity is used in fluorescence imaging to calculate the atomic density, 
  and in absorption imaging to calculate the correction to the atomic density due to the saturation of the transition.
   
* numericalAperture (:py:class:`float`) : The numerical aperture of your imaging system on the object side, typically :math:`\sin(\arctan(D/2f))`
  with  :math:`f` and :math:`D` the focal and the diameter of the clear aperture of your first lens, respectively. 
  Used in fluorescence imaging to calculate the atomic density.

* Imaging__atomicMassAU (:py:class:`float`) : The mass of the atom in atomic units.
  Used to calculate temperature after time-of-flight measurements.
  
* Imaging__atomicFrequencyTHz (:py:class:`float`) : The frequency in THz of the transition used for imaging.
  Used in absorption imaging to calculate the correction to the atomic density due to the saturation of the transition.

* Imaging__crossSectionum2 (:py:class:`float`) : The cross section in µm² of the transition used for imaging.
  Used in absorption imaging to calculate the atomic density.

* Imaging__Isat (:py:class:`float`) : The saturation intensity in W/m² (or µW/mm²) of the transition used for imaging.
  Used in fluorescence imaging to calculate the atomic density, 
  and in absorption imaging to calculate the correction to the atomic density due to the saturation of the transition.

* Imaging__atomicLineFWHWinMHz (:py:class:`float`) : The atomic natural linewidth in MHz (full width at half maximum in frequency) 
  of the transition used for imaging.
  Used to calculate the population decay rate of the excited state as :math:`\Gamma = 2 \pi \times 10^{6} \times` Imaging__atomTransitionFWHWinMHz.   
  Used in fluorescence imaging to calculate the atomic density.

* Imaging__thresholdAbsImg (:py:class:`int`) : The minimum measured intensity (in electrons per pixel) on reference frame (without atoms)
  in absorption imaging to calculate the atomic density. Below the threshold, the atomic density is set to zero.
  Used at each camera connection for initial configuration of this imaging parameter.
  
* Imaging__includeSaturationEffects (:py:class:`bool`) : Decide to include saturation of atomic response to calculate atomic density. 
  If :py:const:`False`, this is equivalent of setting saturation intensity to infinity.
  Used at each camera connection for initial configuration of this imaging parameter.

* Imaging__laserPulseDurationus (:py:class:`float`) :  The duration of laser pulse used for imaging in µs. Used to calculate atomic density.
  Used at each camera connection for initial configuration of this imaging parameter. 

* Imaging__laserIntensity (:py:class:`float`) : The intensity of the laser used for fluorescence imaging in W/m² (or µW/mm²).
  Used at each camera connection for initial configuration of this imaging parameter.

* Imaging__laserDetuningMHz (:py:class:`float`) : The detunning in MHz from resonance of the laser used for for fluorescence imaging.
  Used at each camera connection for initial configuration of this imaging parameter.



After setting the camera configuration(s), you can now use CAtImaPy with a guide provided by section :ref:`Description-and-Use`.







