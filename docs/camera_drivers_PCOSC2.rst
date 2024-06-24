.. _PCO-SC2:

PCO SC2
*******

You first need to install the driver ``SC2_Cam.dll``, 
which is installed with the freely available `PCO Camera Control Software <https://www.excelitas.com/product/pco-camera-control-software>`_ 
or `PCO Software Development Kit pco.sdk <https://www.excelitas.com/product/pco-software-development-kits>`_.

PCO cameras are implemented via `PyLabLib <https://pylablib.readthedocs.io/en/latest/>`_ package. 
Thus, you need to `install PyLabLib <https://pylablib.readthedocs.io/en/latest/install.html#standard-install>`_.
The documentation on PCO SC2 driver in PyLabLib is available `here <https://pylablib.readthedocs.io/en/latest/devices/PCO_SC2.html>`_.

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras/PCOSC2.py* in an editor. 

#. Copy the definition of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

PCO cameras have not been tested with CAtImaPy.
If you use one and it works, let us know. 
If you use one, it does not work and you find why, let us know. 







