License
=======

License for the pyAMARES project:

.. literalinclude:: ../../LICENSE.txt
   :language: text
   :caption: BSD 3-Clause License

Third-Party Licenses
--------------------

This pyAMARES project uses third-party libraries. Below is information about their licenses.

LMFIT
^^^^^
The `LMFIT <https://lmfit.github.io/lmfit-py/index.html>`_ package is used in the pyAMARES project to provide flexible and robust fitting capabilities. It is licensed under the BSD-3-Clause License. For more detailed license information, please visit the `lmfit page <https://lmfit.github.io/lmfit-py/installation.html#copyright-licensing-and-re-distribution>`_.

HLSVDPRO
^^^^^^^^
The `HLSVDPRO <https://pypi.org/project/hlsvdpro/>`_ package is used under its BSD-3-Clause License. For detailed license information, please visit the `hlsvdpro PyPI page <https://pypi.org/project/hlsvdpro/>`_.

Additional Note on ``MPFIR`` Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MPFIR function within pyAMARES is inspired by ``MPFIR.m`` function in the Matlab software `SPID <https://homes.esat.kuleuven.be/~sistawww/biomed/etumour/SPID/ManualSPID.pdf>`_, which at the time of this implementation had no clear licensing information available. 
It is important to note that ``pyAMARES.libs.MPFIR`` is an independent implementation developed in Python and does not contain any original SPID code.

This function is included in pyAMARES under the same BSD 3-Clause License, and no claim is made on the original SPID software or its intellectual property. 
Users are advised to ensure their use of the MPFIR function complies with legal and regulatory requirements.

Disclaimer
""""""""""

pyAMARES and its ``MPFIR`` function are not endorsed by or affiliated with SPID or its creators.


Additional Note on ``calculateCRB`` Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``pyAMARES.util.crlb.calculateCRB`` function within pyAMARES draws conceptual inspiration from ``estimateCRB.m`` function in the Matlab software `OXSA (Oxford Spectroscopy Analysis) toolbox <https://github.com/OXSAtoolbox/OXSA>`_ developed by the University of Oxford. It is important to note that the implementation of ``pyAMARES.util.crlb.calculateCRB`` in pyAMARES is entirely independent, developed in Python, and does not contain any original OXSA code.

This functionality is included in pyAMARES under the same BSD 3-Clause License. No claim is made on the original OXSA software or its intellectual property. Users are advised to review the `OXSA license <https://raw.githubusercontent.com/OXSAtoolbox/OXSA/master/LICENSE.txt>`_, particularly its stipulations on non-commercial use, to ensure compliance with its terms where applicable.

Disclaimer
""""""""""

pyAMARES and its ``calculateCRB`` function are not endorsed by or affiliated with OXSA or its creators.
