"""Compatibility facade for shared web helpers.

New code should import these helpers from common.web.
"""

from common.web import shell, back, signed_in

__all__ = ['shell', 'back', 'signed_in']
