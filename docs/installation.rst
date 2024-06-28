
Installation
************

Requirements
============

The basic requirements are:

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


.. _Installing-camera-drivers:

Installing camera drivers
=========================

The next step is to setup the driver for your camera(s). 
Below, you will find a generic description of the steps to get a camera driver settled in CAtImaPy. 
Precise instructions, depending on the camera manufacturer, are available in section :ref:`Camera-drivers`.

#.  The control of a camera uses a library of functions (driver) defined and written by the manufacturer. 
    The first step is then to install the driver.
    Most of the time, this means installing the software development kit (SDK) provided by the manufacturer on its website.
    
#.  On top of this driver, providing most of the time C functions, 
    we need a python driver accessing these functions. 
    In CAtImaPy code, there are two different ways to get this layer:

        * some implemented drivers rely on a python package provided by the manufacturer. It could also be written by a third party or you, if needed.
        
        * most of implemented drivers use the amazing `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package developed by Alexey Shkarin. 
          This software is a python package for controlling lab equipment in general. 
          We use here its control of cameras because most of scientific cameras are controllable via PyLabLib. 
        
        .. note::
            Alexey Shkarin also developed a separate, stand-alone software `PyLabLib cam-control <https://pylablib-cam-control.readthedocs.io/en/latest/>`_
            for universal camera control and frames acquisition with a convenient GUI. 
    
#.  The final layer for camera control is CAtImaPy specific drivers located in *Cameras* folder.
    Using the previous layer of python drivers, these drivers provide a unified interface for the rest of the code 
    (details in section :ref:`Cameras-code`).
    CAtImaPy implement generic drivers classes for camera operated via a given manufacturer's driver. 
    Theses CAtImaPy's drivers are python classes ``<Driver name>Class`` defined in *<Driver name>.py* files in *Cameras* directory. 
    
    These generic driver classes are intended to be used as a parent class 
    for model specific classes ``<Model name>Class`` defined in the same file.
    When implementing a new camera model for your application, I recommend creating such a model class. 
    The model class will allow to implement a customizable initialization procedure for the given camera model. 
    Even if you do not need this at start, it may come useful at some point latter. 
    Examples of basic inherited model classes are given in section :ref:`Model-Camera-classes`.


.. _Configuring-camera-and-acquisition-parameters:

Configuring camera and acquisition parameters
==============================================

The last step before launching the program is to configure the parameters of your camera(s). 

To do so, open file *Cameras/Config.py* in an editor. 
This file only contains the definition of ``camerasConfigs``: a list of dictionaries each configuring one camera. 
Leave the first element of the list (index 0) as :py:const:`None` because Camera 0 indicates that no actual camera is connected (at start or if connection fails). 

Go to the dictionary definition at list index 1, below the commented line ::
    
    # Camera number 1

And modify the variables values after the = signs to match the ones of your camera. 
The variables are listed below with their key (name of dictionary variable in python), 
the expected value type, their meaning and their use:

* name (:py:class:`str`): Name chosen by user. Only used to recognize camera number in the list of configured cameras.

* driver (:py:class:`str`): Driver name has to be the name of a file *<driver>.py* in *Cameras* folder, and is related to a given manufacturer's driver. 
  Used to find the python class controlling the camera.

* model (:py:class:`str`): Model name has to be the name of class ``<model>Class`` defined in <driver>.py file.
  Used to load specific child class (if :py:const:`None` or not matching  use generic ``<driver>Class``).

* serial (:py:class:`int` or :py:class:`str`): Serial number of the camera (or for some drivers the camera index). 
  Used to identify the camera at connection.

* imageBitDepth (:py:class:`int`): Set bit depth of sensor reading. 
  Used to set the format of image transfered by the camera to the computer. 
  Only if the driver allows it, otherwise the format is set automatically according to camera.
                 
* defaultExposurems (:py:class:`float`): Default duration of exposition (exposure) in milliseconds.
  Used at each camera connection for initial configuration of the camera if "Load camera default from config" is checked.

* defaultGaindB (:py:class:`float`): Default hardware gain (amplification) at sensor read in dB, if gain is avaible for this camera.
  Used at each camera connection for initial configuration of the camera if "Load camera default from config" is checked.

* defaultTrigger ('external' or 'software'): Default input for triggering the camera.
  Used at each camera connection for initial configuration of the camera if "Load camera default from config" is checked.
  Normally should be 'external' to trigger on digital signal rising up provided by hardware used for experiment control.

* defaultCamROI (:py:const:`None` or [:py:class:`int`]*4): Camera region of interest to read from sensor : 
  None for full sensor or [x offset , y offset , x size , y size ] in pixels (binning is not implemented so far).
  This parameter can only be changed via ``camerasConfigs`` (not yet implemented in the GUI).

* defaultFlushSensor (:py:class:`bool`): Default setting to decide if each image acquisition is preceded by a flush read of the camera,
  to remove accumulated charges on sensor. 
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.

* defaultRemoveBackground (:py:class:`bool`): Default setting to decide if a background image is taken and removed to the previous one(s),
  at the end of a cold-atom imaging cycle.
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.
  
* defaultROIkrgnames  ([:py:class:`str`]*3): Names of analysis ROIs that the code try to find in the ROI array 
  and select as the [black, red, green] imaging ROIs used to show results.
  Used at first camera connection (or reconnection if another camera was used previously).

* pixelCalXumperpx (:py:class:`float`): Calibration of width :math:`w_{\mathrm{px}}` of a pixel in the object plane in micrometers.

* pixelCalYumperpx (:py:class:`float`): Calibration of height :math:`h_{\mathrm{px}}` of a pixel in the object plane in micrometers.
  
* reversedAxes ([:py:class:`bool`]*2):  Decide if for each axis [X,Y], if it will be reversed. 
  This allows you to swap the images axes the way you like; for example, to get the atoms falling to the bottom of the image. 
  
* cameraQuantumEff (:py:class:`float`):  Quantum efficiency :math:`\eta_{\mathrm{QE}}` of the camera (or effective efficiency if sets bit depth limits the format).
  Used to calculate the number of photons per pixel from the number of recorded electrons. This allows to know the absolute intensity reaching the sensor.
  The absolute intensity is used in fluorescence imaging to calculate the atomic density, 
  and in absorption imaging to calculate the correction to the atomic density due to the saturation of the transition.
   
* numericalAperture (:py:class:`float`): The numerical aperture of your imaging system on the object side, typically :math:`\sin(\arctan(D/2f))`
  with  :math:`f` and :math:`D` the focal and the diameter of the clear aperture of your first lens, respectively. 
  Used in fluorescence imaging to calculate the atomic density.
  
* Imaging__imagingTypeText ('Absorption Imaging' or 'Fluorescence Imaging') : Type of imaging, details in :ref:`Tab-Imaging-Set`.
  Used at each camera connection for initial configuration of the camera, if "Load camera default from config" is checked.

* Imaging__atomicMassAU (:py:class:`float`): The mass of the atom in atomic units.
  Used to calculate temperature after time-of-flight measurements.
  
* Imaging__atomicFrequencyTHz (:py:class:`float`): The frequency in THz :math:`f \times 10^{-12}` of the transition used for imaging.
  Used in absorption imaging to calculate the correction to the atomic density due to the saturation of the transition.

* Imaging__Isat (:py:class:`float`): The effective saturation intensity :math:`I_{\mathrm{sat}}` in W/m² (or µW/mm²) of the transition used for imaging.
  Used in fluorescence and absorption imagings to calculate the atomic density.
  This effective value allows one to take into account the actual average transition dipole moment in the imaging configuration.
  The effective saturation intensity can be set properly to its actual value by ensuring 
  that the imaging results are independent of laser intensity.
  Unless the operator ensures that the imaging is performed in ideal "two-level-atom" conditions 
  (using the closed transition with the right polarization and magnetic field), 
  the effective saturation intensity will be larger than the one of the closed transition. 
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.

* Imaging__atomicLineFWHWinMHz (:py:class:`float`): The atomic natural linewidth in MHz (full width at half maximum in frequency) 
  of the transition used for imaging.
  Used to calculate the coherence (dipole) decay rate of the excited state as :math:`\gamma = \pi \times 10^{6} \times` Imaging__atomTransitionFWHWinMHz.   
  Used in fluorescence and absorption imaging to calculate the atomic density.

* Imaging__thresholdAbsImg (:py:class:`int`): The minimum measured intensity (in electrons per pixel) on reference frame (without atoms)
  in absorption imaging to calculate the atomic density. Below the threshold, the atomic density is set to zero.
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.
  
* Imaging__includeSaturationEffects (:py:class:`bool`): Decide to include saturation of atomic response to calculate atomic density. 
  If :py:const:`False`, this is equivalent of setting saturation intensity to infinity.
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.

* Imaging__laserPulseDurationus (:py:class:`float`):  The duration of laser pulse used for imaging in µs. Used to calculate atomic density.
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked. 

* Imaging__laserIntensity (:py:class:`float`): The intensity of the laser used for fluorescence imaging in W/m² (or µW/mm²).
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.

* Imaging__laserDetuningMHz (:py:class:`float`): The detuning in MHz from resonance of the laser used for for fluorescence imaging.
  Used at each camera connection for initial configuration of this imaging parameter, if "Load camera default from config" is checked.


If you have more than one camera, define new dictionaries as index 2,... of ``camerasConfigs``.

Any change in this *Config.py* file will only take effect after saving the file followed by a restart of CAtImaPy.

After setting the camera configuration(s), you can now use CAtImaPy with a guide provided by section :ref:`Description-and-Use`.







