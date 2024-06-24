.. _FLIR-PySpin:

FLIR PySpin
***********

You first need to install the freely available (upon registration) `Spinnaker SDK <https://www.flir.eu/products/spinnaker-sdk/>`_,
 
Then you need to install the Python Spinnaker *PySpin* package (download link just below the one of the SDK) that matches your Python version. 
By clicking on the download link, you should get the file *spinnaker_python-XXX-cpYYY-cpYYY-win_amd64.whl*,
where *XXX* is the Spinnaker SDK version and *YYY* is your python version. 
With *Anaconda Prompt* run::

    cd <Path of the downloaded file>
    pip install spinnaker_python-XXX-cpYYY-cpYYY-win_amd64.whl

This will install the *PySpin* package in your base Anaconda environment. 
You should then be able to import the package with::

    import PySpin

Finally, you should create a dedicated model class for your model 
by applying the following procedure (unless model class was already impelmented):

#. Open file *Cameras/FLIRPySpin.py* in an editor. 

#. Copy the definition of the ``ExampleModelClass`` class, and paste it at the end of the file.

#. In the pasted text, replace "ExampleModel" in the name of the class and the "..." in the docstring below 
   by your model name (the exact same as in the Config files).

#. Save your file and test. 

Only Chameleon3 model has been extensively tested with CAtImaPy.
If you use another model and it works, let us know. 
If you use another model, it does not work and you find why, let us know. 







