.. _IDS-ueye:

IDS ueye
********

You first need to install the  `IDS Software Suite <https://en.ids-imaging.com/ids-software-suite.html>`_.

IDS ueye cameras are implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package, 
through the driver uc480, which is common with Thorlabs *DCC..* cameras produced by IDS. 
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on Uc480/uEye in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/uc480.html>`_.

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras\IDSueye.py* in an editor. 

#. Copy the defintion of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

IDS ueye cameras have not been tested with CAtImaPy.
If you use one and it works, let us know. 
If you use one, it does not work and you find why, let us know. 







