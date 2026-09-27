"""Business rules for Connections."""

from .models import Follow



def set_follow(user, target, on):
    """`ValueError` rather than letting the CheckConstraint fire.

    The constraint is the guarantee and this is the error message: a database
    constraint firing is a 500, and a check first turns it into a sentence.
    You want both — the check for the ninety-nine per cent, the constraint for
    the race the check cannot see.
    """
    if user == target:
        raise ValueError("You cannot follow yourself.")
    if on:
        Follow.objects.get_or_create(follower=user, following=target)
    else:
        Follow.objects.filter(follower=user, following=target).delete()
    return on


def toggle_follow(user, target):
    return set_follow(user, target,
                        not Follow.objects.filter(follower=user, following=target).exists())
