
Installation
************

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









