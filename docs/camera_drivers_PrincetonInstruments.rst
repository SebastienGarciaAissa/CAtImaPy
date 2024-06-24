.. _Princeton-Instruments:

Princeton Instruments
*********************

You first need to install the driver ``picam.dll``, which is installed 
with the freely available `PICam software <https://www.princetoninstruments.com/products/software-family/pi-cam>`_.

Princeton Instruments cameras are implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package. 
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on Princeton Instruments driver in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/Picam.html>`_.

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras\PrincetonInstruments.py* in an editor. 

#. Copy the defintion of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

Princeton Instruments cameras have not been tested with CAtImaPy.
If you use one and it works, let us know. 
If you use one, it does not work and you find why, let us know. 







