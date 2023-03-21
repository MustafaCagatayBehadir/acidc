"""Acidc VRF subsriber module."""
import ncs
from ncs.cdb import Subscriber
from . import utils
from .modules.influx import Influx


class AcidcVrfSubscriber(Subscriber):
    """This subscriber subscribes to vrfs in the '/aci-site/vrf-config'."""

    def init(self):
        """Specify monitored nodes in CDB.

        Automatically registers all nodes that need to be
        monitored.
        """
        self.register("/acidc:aci-site/acidc:vrf-config")
        self.register("/acidc:aci-site/acidc:aci-scalability/acidc:l3-context")

    def pre_iterate(self):
        """Call just before iteration starts.

        May return a state object which will be passed on to the iterate method. If not implemented,
        the state object will be None.
        """
        return []

    def iterate(self, keypath, operation, oldval, newval, state):
        """Monitor CDB and act.

        Iterate sits on monitored node it was initialized
        with and filters data for post_iterate.
        """
        self.log.info(f"Keypath: {str(keypath)}, Operation: {operation}")
        # /acidc:aci-site{BTS-FABRIC-001 10.0.0.1}/vrf-config{BTS-VRF-004}
        if operation in (ncs.MOP_CREATED, ncs.MOP_DELETED) and str(keypath[1]) == "vrf-config":
            state.append((operation, str(keypath)))
            return ncs.ITER_CONTINUE
        # kp: /acidc:aci-site{BTS-FABRIC-001 10.0.0.1}/aci-scalability/l3-context
        elif operation == ncs.MOP_VALUE_SET and str(keypath[0]) == "l3-context":
            state.append((operation, str(keypath)))
            return ncs.ITER_CONTINUE
        return ncs.ITER_RECURSE

    def post_iterate(self, state):
        """Post iterate.

        As multiple data nodes have to be read from the CDB, all operations
        are done in post_iterate to avoid possible trancastion deadlocks.

        state (list)
            Contains a list of keys and a number corresponding
            to detected operation done on the subscriber monitored
            node.
        """
        if state == []:
            return

        sites = set()
        for entry in state:
            operation, kp = entry[0], entry[1]
            self.log.info(f"Operation: {operation}, Keypath: {kp}")
            sites.add("/acidc:aci-site" +
                      "{" + kp[kp.find('{') + 1: kp.find('}')] + "}")

        with ncs.maapi.single_write_trans('admin', 'system', db=ncs.OPERATIONAL) as t:
            root = ncs.maagic.get_root(t)
            for kp in sites:
                site = ncs.maagic.cd(root, kp)
                vrf_usage_percent = utils.get_percentage(
                    len(site.vrf_config), site.aci_scalability.l3_context)
                site.capacity_dashboard.l3_context = vrf_usage_percent
                _create_influxdb_record(site, vrf_usage_percent, self.log)
            t.apply()

    def should_post_iterate(self, state):
        """Decide post interate."""
        return state != []


def _create_influxdb_record(site, vrf_usage_percent, log) -> None:
    """Create influxdb record.

    Args:
        site: Acidc site node
        vrf_usage_percent: Percentage of VRF usage
        log: Log object(self.log)

    Returns:
        None
    """
    influx = Influx(protocol="http",
                    host="10.56.60.15",
                    port="8086",
                    bucket="btsgrp-bucket",
                    org="btsgrp",
                    token="5H82UVclrkUZvk5I19lrnHNQ2qYeJZIW-kCH0Vc0travRifpZNWhgtLUYHuL9cMefsM_uXZV6ymKfFsOqMK84g==")
    influx.create_record("VRF_USAGE", site.fabric,
                         "percent", vrf_usage_percent)
    log.info(
        f"InfluxDB record is created: (VRF_USAGE, {site.fabric}, percent, {vrf_usage_percent})")
