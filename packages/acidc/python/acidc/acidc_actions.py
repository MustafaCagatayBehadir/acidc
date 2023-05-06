"""Acidc Actions Main Module."""
import ncs
import _ncs
from ncs.dp import Action
from . import utils
from .modules import models


class CreateInfluxData(ncs.dp.Action):
    """Acidc Influxdb action class."""

    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
        """Write vrf count to influxdb."""
        self.log.info('Action triggered: ', name)
        _ncs.dp.action_set_timeout(uinfo, 1800)
        with ncs.maapi.single_write_trans('admin', 'system', db=ncs.OPERATIONAL) as t:
            root = ncs.maagic.get_root(t)
            for fabric in root.acidc__aci_site:
                site = root.acidc__aci_site[fabric]
                vrf_count = 0
                tenants = root.ncs__devices.device[fabric].config.cisco_apicdc__apic.fvTenant
                for tenant in tenants:
                    vrf_count += len(tenant.fvCtx)
                vrf_usage_percent = utils.get_percentage(vrf_count, site.aci_scalability.l3_context)
                site.capacity_dashboard.l3_context = vrf_usage_percent
                utils.create_influxdb_record(site, vrf_usage_percent, self.log)
        output.result = "Success"
        output.message = f"InfluxDB record is created: (VRF_USAGE, {site.fabric}, percent, {vrf_usage_percent})"


class CreatePostgresData(ncs.dp.Action):
    """Acidc postgresdb action class."""

    @Action.action
    def cb_action(self, uinfo, name, kp, input, output, trans):
        """Write vrf parameters to postgresdb."""
        self.log.info('Action triggered: ', name)
        _ncs.dp.action_set_timeout(uinfo, 1800)
        with ncs.maapi.single_write_trans('admin', 'system', db=ncs.OPERATIONAL) as t:
            root = ncs.maagic.get_root(t)
            for fabric in root.acidc__aci_site:
                vrf_info = list()
                tenants = root.ncs__devices.device[fabric].config.cisco_apicdc__apic.fvTenant
                for tenant in tenants:
                    vrf_info.extend([{
                        "fabric": fabric,
                        "tenant": tenant.name,
                        "vrf_name": vrf.name,
                        "vrf_description": vrf.descr if vrf.descr else "N/A",
                        "enforcement": str(vrf.pcEnfPref),
                    } for vrf in tenant.fvCtx])
                utils.recreate_postgresdb_table(models.AcidcVrf, vrf_info, self.log)
        output.result = "Success"
        output.message = "Postgresdb tables are created."
