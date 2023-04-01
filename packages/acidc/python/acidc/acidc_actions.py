"""Acidc Actions Main Module."""
import ncs
import _ncs
from ncs.dp import Action

from . import utils


class CreateInfluxData(ncs.dp.Action):
    """Acidc Influxdb action class."""

    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
        """Write vrf count to influxdb."""
        self.log.info('Action triggered: ', name)
        _ncs.dp.action_set_timeout(uinfo, 1800)
        with ncs.maapi.single_write_trans('admin', 'system', db=ncs.OPERATIONAL) as t:
            root = ncs.maagic.get_root(t)
            for controller in root.cisco_dc__dc_controller:
                site = root.acidc__aci_site[controller.fabric]
                vrf_count = 0
                for tenant in controller.tenant_service:
                    vrf_count += len(tenant.vrf_config)
                vrf_usage_percent = utils.get_percentage(vrf_count, site.aci_scalability.l3_context)
                site.capacity_dashboard.l3_context = vrf_usage_percent
                utils.create_influxdb_record(site, vrf_usage_percent, self.log)
        output.result = "Success"
        output.message = f"InfluxDB record is created: (VRF_USAGE, {site.fabric}, percent, {vrf_usage_percent})"
