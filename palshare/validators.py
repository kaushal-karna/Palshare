"""Compatibility facade for shared upload validation.

New code should import these validators from common.uploads.
"""

from common.uploads import MAX_FILES, MAX_BYTES, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, ALLOWED_EXTENSIONS, kind_for, validate_upload, validate_uploads

__all__ = ['MAX_FILES', 'MAX_BYTES', 'IMAGE_EXTENSIONS', 'VIDEO_EXTENSIONS', 'ALLOWED_EXTENSIONS', 'kind_for', 'validate_upload', 'validate_uploads']
