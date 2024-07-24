.. _Cameras-code:

Cameras code
************

.. currentmodule:: Cameras

Architecture
============

The *Cameras* folder is defined as a module loaded in :ref:`CAtImaPy-main-code`.

The code controlling cameras rely on the use a base class :class:`CameraClass` (described below) 
as an interface and parent for all manufacturer/model specific camera classes.

The configurations of cameras are set in the *Cameras/Config.py* file as a list ``camerasConfigs`` of dictionaries.

The creation of the ``Camera`` object, attribute of ``mainWin``, is realized by the factory/builder function :func:`create_Camera`.
:func:`create_Camera` selects the child class for the specified driver (manufacturer API) and model,
as given by keys 'driver' and 'model' in ``camerasConfigs``.
Ideally, the creator should load a child class for the specified model with proper initialization of this model. 
The model classes ``<Model name>Class`` are inherited from the driver class ``<Driver name>Class``, 
defined in *<Driver name>.py* file in *Cameras* directory.
The model classes are defined in the same file. 
If no model class is defined, the creator loads the generic driver class. 


Driver camera classes are derived from base class :class:`CameraClass`. 
Either directly by connecting to a python driver, for example, :class:`FLIRPySpinClass` connect to the PySpin driver package provided by FLIR.
Or with the `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package, via an interface class :class:`PylablibInterfaceClass`, 
inherited from :class:`CameraClass` and used as parent of the driver class. 
An example is given by the camera class :class:`ThorlabsClass`.
Available driver classes are listed below in section :ref:`Driver-Camera-classes`.


Model camera classes are the way for the user to properly initialize the camera.
Indeed, if the generic driver class may work, the different camera models often have different available options or properties.
In order to set all the parameters optimally the user should define a model class. 
Even in the case where the driver class is working, 
the user should preferably define a model class simply inheriting everything from the driver class.
This should avoid future conflicts if other camera models with the same driver need to be added. 
The  *<Driver name>.py* file contains the definition of a ``ExampleModelClass``,
that you can copy to make your model ``<Model name>Class`` by changing its name (and docstring). 
Two examples of properly defined model classes are given below in section :ref:`Model-Camera-classes`. 


Base Camera class
=================

.. autoclass:: CameraClass
   :members:
   :special-members: __init__, __del__


Camera creator
==============  

.. autofunction:: create_Camera
 

.. _Driver-Camera-classes:

Driver Camera classes
=====================


Direct driver classes
---------------------

.. autosummary::
    :toctree: _generated
    :nosignatures:
        
        ~FLIRPySpin.FLIRPySpinClass


PyLabLib interface class
------------------------

.. autosummary::
    :toctree: _generated
    :nosignatures:
        
        ~PylablibInterfaceClassDef.PylablibInterfaceClass


PyLabLib-based driver classes
-----------------------------

.. autosummary::
    :toctree: _generated
    :nosignatures:
        
        ~AndorSDK2.AndorSDK2Class
        ~AndorSDK3.AndorSDK3Class
        ~HamamatsuDCAM.HamamatsuDCAMClass
        ~IDSueye.IDSueyeClass
        ~NIIMAQdx.NIIMAQdxClass
        ~PCOSC2.PCOSC2Class
        ~Photometrics.PhotometricsClass
        ~PrincetonInstruments.PrincetonInstrumentsClass
        ~Thorlabs.ThorlabsClass
        ~ThorlabsUC480.ThorlabsUC480Class


.. _Model-Camera-classes:

Model Camera classes
=====================

Below you will find two examples of properly defined model classes. 

.. autosummary::
    :toctree: _generated
    :nosignatures:
        
        FLIRPySpin.Chameleon3Class
        Thorlabs.ZeluxClass
        
        
        
        
        