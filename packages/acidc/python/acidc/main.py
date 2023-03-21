"""ACI Scalability Monitoring Service."""
import ncs
from ncs.application import Service

from . import utils
from . import acidc_vrf_subscriber
from .modules.aci import Aci
from .modules.influx import Influx


# ------------------------
# SERVICE CALLBACK EXAMPLE
# ------------------------
class AcidcCallbacks(Service):
    """Acidc callback handler."""

    @Service.create
    def cb_create(self, tctx, root, service, proplist):
        """Create callback."""
        self.log.info('Service create(service=', service._path, ')')
        vrf_usage_percent = _create_aci_capacity_dashboard(root, service, self.log)
        _create_influxdb_record(service, vrf_usage_percent, self.log)
        proplist.append(("vrf-usage-percent", str(vrf_usage_percent)))
        return proplist

    @Service.post_modification
    def cb_post_modification(self, tctx, op, kp, root, proplist):
        """Service postmod."""
        self.log.info('Postmod for service: ', kp)
        self.log.info('Proplist: ', proplist)
        if op != ncs.dp.NCS_SERVICE_DELETE:
            acidc = ncs.maagic.cd(root, kp)
            disable_alarm, vrf_alarm_threshold, vrf_usage_percent = acidc.aci_alarm.disable_alarm.exists(
            ), float(acidc.aci_alarm.l3_context), float(proplist[0][1])
            if not disable_alarm and vrf_usage_percent > vrf_alarm_threshold:
                self.log.info(f"ACI {acidc.fabric} fabric icin VRF alarm threshold asilmistir.")
        return proplist


def _create_aci_capacity_dashboard(root, acidc, log) -> float:
    """Set capacity dashboard leaves.

    Args:
        root: Maagic object pointing to the root of the CDB
        acidc: Acidc service node
        log: Log object(self.log)

    Returns:
        Percentage of VRF usage
    """
    username, password = utils.get_basic_authentication(root, "APIC")
    aci = Aci(protocol="https", host=acidc.host, port="443", username=username, password=password, cert_verify=False)
    aci.get_cookies()
    vrf_count = aci.get_vrf_count()
    log.info(f"{acidc.host} VRF count: ", vrf_count)
    vrf_usage_percent = utils.get_percentage(vrf_count, acidc.aci_scalability.l3_context)
    acidc.capacity_dashboard.l3_context = vrf_usage_percent
    log.info(f"{acidc.host} VRF usage: ", vrf_usage_percent)
    return vrf_usage_percent


def _create_influxdb_record(acidc, vrf_usage_percent, log) -> None:
    """Create influxdb record.

    Args:
        acidc: Acidc service node
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
    influx.create_record("VRF_USAGE", acidc.fabric, "percent", vrf_usage_percent)
    log.info(f"InfluxDB record is created: (VRF_USAGE, {acidc.fabric}, percent, {vrf_usage_percent})")


# ---------------------------------------------
# COMPONENT THREAD THAT WILL BE STARTED BY NCS.
# ---------------------------------------------
class Main(ncs.application.Application):
    """Main class."""

    def setup(self):
        """Register service and actions."""
        self.log.info('Main RUNNING')

        # Acidc Vrf Subscriber
        self.vrf_subscriber = acidc_vrf_subscriber.AcidcVrfSubscriber(self)
        self.vrf_subscriber.start()


    def teardown(self):
        """Teardown."""
        self.log.info('Main FINISHED')
        self.vrf_subscriber.stop()
