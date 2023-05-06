"""Acidc VRF subsriber module."""
from collections import defaultdict
import ncs
from ncs.cdb import Subscriber, TwoPhaseSubscriber
from . import utils
from . import acidc_exceptions
from .modules import models


class AcidcVrfTwoPhaseSubscriber(TwoPhaseSubscriber):
    """This subscriber subscribes to vrfs in the '/devices/device/config/cisco-apicdc:apic/fvTenant/fvCtx'."""

    def init(self):
        """Specify monitored nodes in CDB.

        Automatically registers all nodes that need to be
        monitored.
        """
        self.register("/devices/device/config/cisco-apicdc:apic/fvTenant/fvCtx")

    def pre_iterate(self):
        """Call just before iteration starts.

        May return a state object which will be passed on to the iterate method. If not implemented,
        the state object will be None.
        """
        return []

    def prepare(self, keypath, operation, oldv, newv, state):
        """Call in the transaction prepare phase.

        If an exception occurs during the invocation of prepare the transaction is aborted.
        """
        self.log.info(f"Keypath: {str(keypath)}, Operation: {operation}, Method: prepare")
        # /devices/device{apic1-1}/config/cisco-apicdc:apic/fvTenant{TENANT_0001}/fvCtx{VRF_0001}
        fabric = defaultdict(list)
        if operation in (ncs.MOP_CREATED,) and str(keypath[1]) == "fvCtx":
            apic, vrf = str(keypath[6][0]), str(keypath[0][0])
            state.append((apic, vrf))
        for apic, vrf in state:
            fabric[apic].append(vrf)
        self.log.info("State: ", state)
        self.log.info("Fabric: ", fabric)
        with ncs.maapi.single_write_trans('admin', 'system') as t:
            root = ncs.maagic.get_root(t)
            for apic, vrf in fabric.items():
                site = root.acidc__aci_site[apic]
                vrf_count = 0
                tenants = root.ncs__devices.device[fabric].config.cisco_apicdc__apic.fvTenant
                for tenant in tenants:
                    vrf_count += len(tenant.fvCtx)
                vrf_usage_percent = utils.get_percentage(vrf_count + len(vrf), site.aci_scalability.l3_context)
                disable_alarm, vrf_alarm_threshold = site.aci_alarm.disable_alarm.exists(), float(
                    site.aci_alarm.l3_context)
                self.log.info(f"Method: prepare, Site: {site.fabric}, Current VRF Count: {vrf_count}, " +
                              f"Calculated VRF Count: {vrf_count + len(vrf)}, " +
                              f"VRF Usage Percent: {vrf_usage_percent}, VRF Alarm Threshold: {vrf_alarm_threshold}")
                if not disable_alarm and vrf_usage_percent > vrf_alarm_threshold:
                    raise acidc_exceptions.VrfThresholdError(
                        threshold=vrf_alarm_threshold,
                        message=f"ACI {site.fabric} fabric icin VRF alarm threshold asilmaktadir.")
        return ncs.ITER_CONTINUE

    def cleanup(self, state):
        """Call after a prepare failure if available. Use to cleanup resources allocated by prepare."""
        state = []
        self.log.info(f"State: {state}, Method: cleanup")

    def abort(self, kp, op, oldv, newv, state):
        """Call if another subscriber aborts the transaction and this transaction has been prepared."""
        return ncs.ITER_STOP

    def iterate(self, keypath, operation, oldval, newval, state):
        """Monitor CDB and act.

        Iterate sits on monitored node it was initialized
        with and filters data for post_iterate.
        """
        return ncs.ITER_STOP


class AcidcVrfSubscriber(Subscriber):
    """This subscriber subscribes to vrfs in the '/aci-site/vrf-config' and 'aci-site/aci-scalability/l3-context'."""

    def init(self):
        """Specify monitored nodes in CDB.

        Automatically registers all nodes that need to be
        monitored.
        """
        self.register("/devices/device/config/cisco-apicdc:apic/fvTenant/fvCtx")
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
        self.log.info(f"Keypath: {str(keypath)}, Operation: {operation}, Method: iterate")
        # /devices/device{apic1-1}/config/cisco-apicdc:apic/fvTenant{TENANT_0001}/fvCtx{VRF_0001}
        if operation in (ncs.MOP_CREATED, ncs.MOP_DELETED, ncs.MOP_MODIFIED) and str(keypath[1]) == "fvCtx":
            state.append(str(keypath[6][0]))
            return ncs.ITER_CONTINUE
        # kp: /acidc:aci-site{BTS-FABRIC-001 10.0.0.1}/aci-scalability/l3-context
        elif operation == ncs.MOP_VALUE_SET and str(keypath[0]) == "l3-context":
            state.append(str(keypath[2][0]))
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

        self.log.info("State: ", state)
        sites = set(state)

        with ncs.maapi.single_write_trans('admin', 'system', db=ncs.OPERATIONAL) as t:
            root = ncs.maagic.get_root(t)
            for fabric in sites:
                site = root.acidc__aci_site[fabric]
                vrf_info = list()
                tenants = root.ncs__devices.device[fabric].config.cisco_apicdc__apic.fvTenant
                for tenant in tenants:
                    vrf_info.extend([{
                        "vrf_name": vrf.name,
                        "vrf_description": vrf.descr if vrf.descr else "N/A",
                        "enforcement": str(vrf.pcEnfPref),
                        "tenant": tenant.name,
                        "fabric": fabric
                    } for vrf in tenant.fvCtx])
                vrf_usage_percent = utils.get_percentage(len(vrf_info), site.aci_scalability.l3_context)
                site.capacity_dashboard.l3_context = vrf_usage_percent
                utils.create_influxdb_record(site, vrf_usage_percent, self.log)
                utils.recreate_postgresdb_table(models.AcidcVrf, vrf_info, self.log)
                disable_alarm, vrf_alarm_threshold = site.aci_alarm.disable_alarm.exists(), float(
                    site.aci_alarm.l3_context)
                if not disable_alarm and vrf_usage_percent > vrf_alarm_threshold:
                    self.log.info(f"***ACI {site.fabric} fabric icin VRF alarm threshold asilmistir.***")
            t.apply()

    def should_post_iterate(self, state):
        """Decide post interate."""
        return state != []
