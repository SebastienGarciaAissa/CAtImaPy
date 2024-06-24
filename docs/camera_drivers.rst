.. _Camera-drivers:

Camera drivers
**************

This section provides instruction to install drivers for your camera depending on the manufacturer. 

As most of camera drivers are implemented through `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package, 
most of the pages include a link to PyLabLib documentation.

If you can not find your manufacturer in the list below,  you will need to develop your own driver. 
Following the architecture described in :ref:`Installing-camera-drivers` and :ref:`Cameras-code`,
you will have to write a ``<Driver name>Class`` defined in a new *<Driver name>.py* file in *Cameras* directory.
If you do that, please consider sharing your driver with the community,
by contacting developer or submitting a pull request on github. 


List of implemented drivers
===========================

.. toctree::
   :maxdepth: 2
   
   
   camera_drivers_AndorSDK2
   camera_drivers_AndorSDK3
   camera_drivers_FLIRPySpin
   camera_drivers_HamamatsuDCAM
   camera_drivers_IDSueye
   camera_drivers_NIIMAQdx
   camera_drivers_PCOSC2
   camera_drivers_Photometrics
   camera_drivers_PrincetonInstruments
   camera_drivers_Thorlabs
   camera_drivers_ThorlabsUC480


