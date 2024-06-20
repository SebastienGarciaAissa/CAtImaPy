.. _Imagings-code:

Imagings code
*************

.. currentmodule:: Imagings

Architecture
============

The *Imagings* folder is defined as a module loaded in :ref:`CAtImaPy-main-code`.

The code used to acquire, analyze, plot and save series of measurements is included in the class :class:`ImagingClass` described below.
This class defines the ``Imaging`` object, attribute of ``mainWin``. 
The ``Imaging`` object contains the information over a measurement and is saved in string and pickle formats 
in '.txt' and '.imo' files respectively.

Fitting of functions performed in :class:`ImagingClass` methods uses the sub-module ``fittool``. 
In this module, the :class:`~fittool.FitUtility` performs the fit of a function (instance of :class:`~fittool.FitFunction`) on the data.
The defined functions available for fitting are listed in ``fitFunctionsList`` variable. 


ImagingsClass
=================

.. autoclass:: ImagingClass
   :members:
   :special-members: __init__, __del__



Fitting 
=======

.. autoclass:: Imagings.fittool.FitUtility
   :members:
   :special-members: __init__, __del__

.. autoclass:: Imagings.fittool.FitFunction
   :members:
   :special-members: __init__, __del__
   
   
