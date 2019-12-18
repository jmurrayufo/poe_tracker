
__version__ = '0.0.0'

from collections import namedtuple

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=0, micro=0, releaselevel='final', serial=0)
