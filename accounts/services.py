from django.core.exceptions import ValidationError

from palshare.validators import validate_upload


def set_avatar(profile, upload):
    """Store a profile picture, through the same allowlist as post media.

        Deliberately the same `validate_upload`: a second, looser rule for avatars
        is how the one place that checks uploads becomes the one place that used
        to. Videos are rejected here because a moving avatar is not a feature
        anybody asked for.
        """
    kind = validate_upload(upload)

    if kind != "image":
        raise ValidationError("A profile picture has to be an image.")
    # The old file is not deleted: it may be the default, and unlinking a file
    # a database row still points at is how you get a broken image everywhere
    # it was cached. Cleaning up storage is its own job, with its own
    # management command.

    profile.avatar = upload
    profile.save(update_fields=["avatar"])

    return profile
