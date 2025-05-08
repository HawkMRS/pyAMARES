==================
Installation Guide
==================

.. image:: https://img.shields.io/badge/Python->%3D3.6%2C%203.8+-blue.svg
   :target: https://python.org
   :alt: Python Version

.. note::
   PyAMARES requires Python 3.6 or newer. We recommend using Python 3.8 or newer. If you are using an older version of Python, you will need to upgrade to use pyAMARES.


PIP installation
__________________

.. tabs:: 
   .. tab:: Prepare Python Environment

      It is recommended to create a Python environment using `Anaconda or Miniconda <https://docs.anaconda.com/anaconda/install/index.html>`_.

      PyAMARES requires Python 3.6 or higher. To create a new ``conda`` environment with Python 3.8, follow these steps:

      1. Open a terminal window.

      2. Run the command:

         .. code-block:: bash

            conda create -n env_name python=3.8

         Here, replace ``env_name`` with the desired name for your PyAMARES environment.

      3. After the environment has been created, activate it by running:

         .. code-block:: bash

            conda activate env_name

      4. Now, you can proceed to install PyAMARES using the ``pip`` command. See the next tab **Use pip**.

   .. tab:: Use pip

      After creating the Python environment using ``conda``, PyAMARES can be installed with the ``pip`` command directly:

      .. code-block:: bash

         conda activate env_name 
         pip install pyamares

      If you do not have system-wide installation permissions:

      .. code-block:: bash

         python3 -m pip install pyamares --user

      To install the most recent version of pyAMARES from source code, use:

      .. code-block:: bash

         pip install git+https://github.com/HawkMRS/pyAMARES

      Now, you have successfully installed pyAMARES in the Python environment ``env_name``. In the future, **always activate this environment with:**

      .. code-block:: bash

         conda activate env_name

      .. note:: **Setting up Jupyter notebook (optional)**

      If you do not already have Jupyter notebook installed in another conda environment, you can first activate your environment with ``conda activate my_env`` and then install the classic Jupyter notebook with:

      .. code-block:: bash

         pip install notebook

      Alternatively, you can install the more modern `JupyterLab <https://jupyter.org/install>`_ with:

      .. code-block:: bash

         pip install jupyterlab


      If you are an experienced user who already has Jupyter Notebook installed under another conda environment, you can 
      add the environment where pyAMARES was just installed (``env_name``) as one of the kernels of your Jupyter 
      Notebook with the display name ``Python (env_name)`` (or any other name you choose):

      .. code-block:: bash

         pip install ipykernel
         python -m ipykernel install --user --name env_name --display-name "Python (env_name)"

   .. tab:: Google Colab 
      Google Colab is a free Google service that allows users to write and execute
      Python entirely in the cloud. You just need a Google Account to launch a Jupyter
      notebook on `Colab <https://colab.research.google.com/>`_.

      To use pyAMARES on Colab, simply create a new notebook, and in a new cell, type:

      .. code-block:: bash

         !pip install pyamares

      After installation, execute the following in another new cell:

      .. code-block:: bash

         import pyAMARES

      You can then start using pyAMARES online or proceed to the "Getting Started" section.

   .. tab:: Install Dev Version Directly from GitHub

      .. note::
         Please note that the development version might be unstable, so it is primarily for testing and development purposes.

      If you want to install the latest development version of ``pyAMARES`` directly from GitHub, use the following command:

      .. code-block:: bash

         conda activate env_name
         python -m pip install git+https://github.com/HawkMRS/pyAMARES.git@dev#egg=pyAMARES

      This command tells ``pip`` to install the package directly from the ``dev`` branch of the Github repository. 

   .. tab:: Install Web Interface Locally (New!)

      If you want to install the `web interface of pyAMARES <https://pyamares.streamlit.app/>`_ locally, you can do so by running the following command:

      .. code-block:: bash

         conda activate env_name
         python -m pip install git+https://github.com/HawkMRS/pyAMARES.git@gui#egg=pyAMARES[streamlit]

      After installation, you can run one of these commands to launch the web interface locally:

      .. code-block:: bash

         # Launch pyAMARES and automatically open in your default browser
         streamlit run https://raw.githubusercontent.com/HawkMRS/pyAMARES/refs/heads/gui/pyAMARES/script/amaresfit_gui.py

         # Launch the web server only (access via http://localhost:8501 in your browser)
         streamlit run https://raw.githubusercontent.com/HawkMRS/pyAMARES/refs/heads/gui/pyAMARES/script/amaresfit_gui.py --server.headless true


      For more information about running Streamlit apps, please visit the `Streamlit documentation <https://docs.streamlit.io/develop/concepts/architecture/run-your-app>`_.


Update Installed pyAMARES
_________________________

PyAMARES is under active development. You can update the installed version of pyAMARES using the following command:

.. code-block:: bash

   pip install --upgrade pyAMARES

Alternatively, you can install the development version directly from GitHub as previously mentioned:

.. code-block:: bash

   python -m pip install git+https://github.com/HawkMRS/pyAMARES.git@dev#egg=pyAMARES

Please refer to the installation details in the `Install Dev Version Directly from GitHub` section above.
