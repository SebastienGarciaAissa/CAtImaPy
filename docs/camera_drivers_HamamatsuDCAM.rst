.. _Hamamatsu-DCAM:

Hamamatsu DCAM
**************

You first need to install the driver ``dcamapi.dll``, 
which is installed with most of Hamamatsu camera softwares, 
as well as with the freely available `DCAM API <https://www.hamamatsu.com/eu/en/product/cameras/software/driver-software.html>`_

Hamamatsu cameras are implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package. 
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on HamamatsuDCAM in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/DCAM.html>`_.

Finally, you should create a dedicated model class for your model  
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras\HamamatsuDCAM.py* in an editor. 

#. Copy the defintion of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

Hamamatsu cameras have not been tested with CAtImaPy.
If you use one and it works, let us know. 
If you use one, it does not work and you find why, let us know. 







