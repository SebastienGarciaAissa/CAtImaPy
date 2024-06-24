.. _Andor-SDK-3:

Andor SDK 3
***********

You first need to install `Andor Solis <https://andor.oxinst.com/products/solis-software/>`__ 
or the  `Andor SKD <https://andor.oxinst.com/products/software-development-kit/>`__.

The version 3 of the software development kit (SDK 3) interfaces the newer cameras: Zyla, Neo, Apogee, Sona, Marana, and Balor.

Andor cameras are implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package. 
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on AndorSDK3 in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/Andor.html#cameras-andor-sdk3>`_.

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras/AndorSDK3.py* in an editor. 

#. Copy the definition of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

Andor cameras have not been tested with CAtImaPy.
If you use one and it works, let us know. 
If you use one, it does not work and you find why, let us know. 







