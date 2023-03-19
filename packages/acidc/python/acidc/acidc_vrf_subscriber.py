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
        self.register('/acidc:aci-site/acidc:vrf-config', priority=100)

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
        if operation != ncs.MOP_VALUE_SET:
            state.append([operation, str(keypath)])
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
        for entry in state:
            operation, kp = entry[0], entry[1]
            self.log.info(f"Operation: {operation}, Keypath: {kp}")
            if operation in (1, 2):
                self.log.info("Vrf was created." if operation == 1 else "Vrf was deleted.")
                with ncs.maapi.single_write_trans('admin', 'system', db=ncs.OPERATIONAL) as t:
                    root = ncs.maagic.get_root(t)
                    site = ncs.maagic.cd(root, f"/acidc:aci-site{{{kp[kp.find('{') + 1 : kp.find('}')]}}}")
                    vrf_count = len(site.vrf_config)
                    vrf_usage_percent = utils.get_percentage(vrf_count, site.aci_scalability.l3_context)

    def should_post_iterate(self, state):
        """Decide post interate."""
        return state != []
