.. _GUI-code:

GUI code
********

.. currentmodule:: CAtImaPy


GUI implementation
==================

The GUI is designed with Qt and interpreted by :PyQt5:.

The *UI* folder is defined as a module loaded in :ref:`CAtImaPy-main-code`.

The ``ui`` object of class :class:`UI.Ui_MainWindow` control the graphical user interface (GUI). 
The class definition of :class:`UI.Ui_MainWindow` is generated automatically in file *UI/CAtImaPy_UI.py* from the designer file *UI/CAtImaPy_UI.ui*.

The variables and buttons in the GUI are connected respectively to variables and methods of the ``mainWin`` object or its main attributes ``Imaging`` or ``Camera``. 
For most of the variables, the connections are done automatically via ``mainWin`` method :func:`~MainWindow.connectUiVariables`.
The remaining few variable connections go through dedicated ``mainWin`` methods with format ``on_<variable name>_valueChanged()`` or ``on_<variable name>_stateChanged()``.
because a value change needs to trigger other changes in GUI values.
The buttons are connected via ``mainWin`` methods ``on_<button name>_cliked()``.


Changing the GUI
================

#. Open *CAtImaPy_UI.ui* in Qtdesigner.
    With *Anaconda Prompt* run::

        cd <path of CAtImaPy/UI folder>
        designer CAtImaPy_UI.ui

#. Run pyuic5 to translate the ui to python code.
    With *Anaconda Prompt* run::

        pyuic5 CAtImaPy_UI.ui > CAtImaPy_UI.py

#. Change last line of CAtImaPy_UI.py to 
    ::  

        from .matplotlibwidget import MatplotlibWidget
    
    (just add a "." before "matplotlibwidget")

#. Implement feature in code.
    Change :class:`~MainWindow` code and/or other codes to connect and use the new GUI variable or button.  



Ui_MainWindow Class
===================

.. autoclass:: UI.Ui_MainWindow


