.. _CAtImaPy-main-code:

CAtImaPy main code
******************

.. currentmodule:: CAtImaPy

The central object of the code is the ``mainWin`` object of class :class:`~MainWindow` described below and defined in *CAtImaPy.py* file.
The main attributes of ``mainWin`` object are :

* the ``ui`` object of class :class:`UI.Ui_MainWindow` hosting the graphical user interface (GUI).
  The code of this class is located in *UI* folder, loaded as a module and described in section :ref:`GUI-code`. 

* the ``Camera`` object of base class :class:`~Cameras.CameraClass` controlling a camera. 
  The code of this class is located in *Cameras* folder, loaded as a module and described in section :ref:`Cameras-code`.
  Refer to section  :ref:`Camera-drivers` for details on writing specific code implementation for your camera(s) model(s).
  
* the ``Imaging`` object of class :class:`~Imagings.ImagingClass` used to acquire, analyze, plot and save series of measurements. 
  The code of this class is located in *Imagings* folder, loaded as a module and described in section :ref:`Imagings-code`.
  The ``Imaging`` object contains the information over a measurement and is saved in string and pickle formats 
  in '.txt' and '.imo' files respectively.
  
The *Scripts* folder hosts pieces of codes that can be executed like a method of ``mainWin`` with ``self`` referring to it. 
The folder contains two examples and it could also host your own code, if you need this feature.


MainWindow class
================

.. autoclass:: MainWindow
   :members:
   :special-members: __init__, __del__





