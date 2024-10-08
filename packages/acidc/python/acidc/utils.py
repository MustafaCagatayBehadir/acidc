"""Helpers module for acidc service."""
from typing import List, Dict
import _ncs
from .modules.aci import Aci
from .modules.influx import Influx


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
    return round(((count / limit) * 100), 2)


def _create_aci_capacity_dashboard(root, acidc, log) -> float:
    """Set capacity dashboard leaves.

    Args:
        root: Maagic object pointing to the root of the CDB
        acidc: Acidc service node
        log: Log object(self.log)

    Returns:
        Percentage of VRF usage
    """
    username, password = get_basic_authentication(root, "APIC")
    aci = Aci(protocol="https", host=acidc.host, port="443", username=username, password=password, cert_verify=False)
    aci.get_cookies()
    vrf_count = aci.get_vrf_count()
    log.info(f"{acidc.host} VRF count: ", vrf_count)
    vrf_usage_percent = get_percentage(vrf_count, acidc.aci_scalability.l3_context)
    acidc.capacity_dashboard.l3_context = vrf_usage_percent
    log.info(f"{acidc.host} VRF usage: ", vrf_usage_percent)
    return vrf_usage_percent


def create_influxdb_record(site, vrf_usage_percent, log) -> None:
    """Create influxdb record.

    Args:
        site: Acidc site node
        vrf_usage_percent: Percentage of VRF usage
        log: Log object(self.log)

    Returns:
        None
    """
    influx = Influx(protocol="http",
                    host="10.1.182.6",
                    port="8086",
                    bucket="nso",
                    org="acidc",
                    token="5H82UVclrkUZvk5I19lrnHNQ2qYeJZIW-kCH0Vc0travRifpZNWhgtLUYHuL9cMefsM_uXZV6ymKfFsOqMK84g==")
    influx.create_record("vrf-usage", site.fabric, "percent", vrf_usage_percent)
    log.info(f"InfluxDB record is created: (vrf-usage, {site.fabric}, percent, {vrf_usage_percent})")


def recreate_postgresdb_table(model, data: List[Dict], log) -> None:
    """Delete the postgresdb table records and make bulk write operation postgresdb table with the data."""
    model.clear_db()
    model.write_db(data)
    log.info(f"NSO database table {model.__table__.name} is recreated.")