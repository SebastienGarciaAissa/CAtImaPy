.. _Thorlabs-UC480:

Thorlabs UC480
**************

You first need to install the `ThorCam <https://www.thorlabs.com/software_pages/ViewSoftwarePage.cfm?Code=ThorCam>`_,

Thorlabs UC480 cameras (DCC... models) are implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package, 
through the driver uc480, which is common with IDS ueye because Thorlabs sold IDS cameras under the DCC... references. 
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on Uc480/uEye in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/uc480.html>`_.

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras\ThorlabsUC480.py* in an editor. 

#. Copy the defintion of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

Thorlabs UC480 cameras have not been tested with CAtImaPy.
If you use one and it works, let us know. 
If you use one, it does not work and you find why, let us know. 







