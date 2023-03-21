"""Acidc VRF subsriber module."""
import ncs
from ncs.cdb import Subscriber
from . import utils


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
                utils.create_influxdb_record(
                    site, vrf_usage_percent, self.log)
                disable_alarm, vrf_alarm_threshold = site.aci_alarm.disable_alarm.exists(
                ), float(site.aci_alarm.l3_context)
                if not disable_alarm and vrf_usage_percent > vrf_alarm_threshold:
                    self.log.info(
                        f"ACI {site.fabric} fabric icin VRF alarm threshold asilmistir.")
            t.apply()

    def should_post_iterate(self, state):
        """Decide post interate."""
        return state != []
