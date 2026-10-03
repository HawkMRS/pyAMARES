License
=======

License for the pyAMARES project:

.. literalinclude:: ../../LICENSE.txt
   :language: text
   :caption: BSD 3-Clause License

Third-Party Licenses
--------------------

This pyAMARES project uses third-party libraries. Below is information about their licenses.

hlsvdpropy
^^^^^^^^^^
The `hlsvdpropy` library is bundled, with modifications, as `pyAMARES/libs/hlsvd.py` under its BSD-3-Clause License. For detailed license information, please visit the `hlsvdpropy GitHub page <https://github.com/bsoher/hlsvdpropy>`_.

loguru
^^^^^^
The library `loguru` is used under its MIT License. For detailed license information, please visit the `loguru GitHub page <https://github.com/Delgan/loguru>`_.

Additional Note on MPFIR Function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The MPFIR function within pyAMARES is inspired by MPFIR function in the Matlab software `SPID <https://homes.esat.kuleuven.be/~sistawww/biomed/etumour/SPID/ManualSPID.pdf>`_, which at the time of this implementation had no clear licensing information available. 
It is important to note that ``pyAMARES.libs.MPFIR`` is an independent implementation developed in Python and does not contain any original SPID code.

This function is included in pyAMARES under the same BSD 3-Clause License, and no claim is made on the original SPID software or its intellectual property. 
Users are advised to ensure their use of the MPFIR function complies with legal and regulatory requirements.

Disclaimer
^^^^^^^^^^

pyAMARES and its MPFIR function are not endorsed by or affiliated with SPID or its creators.


