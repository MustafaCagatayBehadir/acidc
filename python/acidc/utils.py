"""Helpers module for acidc service."""
import _ncs


def get_basic_authentication(root, auth_group):
    """Get basic authentication tuple.

    Args:
        root: Maagic object pointing to the root of the CDB
        auth_group: Authentication group name

    Returns:
        Tuple: username, password
    """
    default_map = root.ncs__devices.authgroups.group[auth_group].default_map
    username = default_map.remote_name
    password = default_map.remote_password
    password = _ncs.decrypt(password)
    return username, password


def get_percentage(count: int, limit: int) -> float:
    """Get percentage with two fractional digits.

    Args:
        count: Total number of object configured in ACI
        limit: Verified limit for the object in ACI

    Returns:
        Percentage: count/limit
    """
    return round(((count/limit) * 100), 2)
