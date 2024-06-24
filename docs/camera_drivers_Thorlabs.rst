.. _Thorlabs:

Thorlabs
********

You first need to install the freely available `ThorCam <https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam>`_,
which include the required drivers :
``thorlabs_tsi_camera_sdk.dll``, ``thorlabs_unified_sdk_kernel.dll``, ``thorlabs_unified_sdk_main.dll``, ``thorlabs_tsi_usb_driver.dll``, 
``thorlabs_tsi_usb_hotplug_monitor.dll``, ``thorlabs_tsi_cs_camera_device.dll``, ``tsi_sdk.dll``, ``tsi_usb.dll``.

The *Thorlabs* driver manage new thorlabs models (as Kirealux or Zelux). 
Old model with name *DCC* were produced by IDS and are controlled by the :ref:`Thorlabs-UC480` driver.

Thorlabs cameras are implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package. 
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on Thorlabs driver in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/Thorlabs_TLCamera.html>`_.

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras\Thorlabs.py* in an editor. 

#. Copy the defintion of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

Only Zelux model has been quickly tested with CAtImaPy.
If you use another model and it works, let us know. 
If you use another model, it does not work and you find why, let us know. 







