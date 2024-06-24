.. _NI-IMAQdx:

NI IMAQdx
*********

You first need to install the driver ``imaqdx.dll``, which is installed 
with the freely available `Vision Acquisition Software <https://www.ni.com/fr/support/downloads/drivers/download.vision-acquisition-software.html>`_. 
However, the IMAQdx part of the software is proprietary, and requires purchase to use.

National Instruments IMAQdx camera interface is  implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package.
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on NI IMAQdx in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/IMAQdx.html>`_.

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras\NIIMAQdx.py* in an editor. 

#. Copy the defintion of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

NI IMAQdx has not been tested with CAtImaPy.
If you use it and it works, let us know. 
If you use it, it does not work and you find why, let us know. 







