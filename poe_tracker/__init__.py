

from collections import namedtuple

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(major=0, minor=2, micro=0, releaselevel='alpha', serial=0)

__version__ = f'{version_info.major}.{version_info.minor}.{version_info.micro}'
