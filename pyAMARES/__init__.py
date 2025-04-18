__author__ = "Jia Xu, MR Research Facility, University of Iowa"
__version__ = "0.3.27dev"

# print("Current pyAMARES version is %s" % __version__)
# print("Author: %s" % __author__)

from .kernel import *  # noqa: F403
from .util import *  # noqa: F403
from .libs import *  # noqa: F403
from .fileio import *  # noqa: F403

__all__ = []

from .kernel import __all__ as kernel_all
from .util import __all__ as util_all
from .libs import __all__ as libs_all
from .fileio import __all__ as fileio_all

__all__.extend(kernel_all)
__all__.extend(util_all)
__all__.extend(libs_all)
__all__.extend(fileio_all)
