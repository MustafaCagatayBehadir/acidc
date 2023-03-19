"""NSO CDB MODULE."""

import json
import requests
import urllib3
from . import models

urllib3.disable_warnings()


class Nso:
    """Defines cisco nso connection parameters."""

    def __init__(
        self,
        protocol,
        host,
        port,
        username,
        password,
        cert_verify,
        fabric,
    ):
        """Initialize attributes for establishing connection to NSO.

        :protocol: Transport protocol can be http | https
        :host: NSO IP address
        :port: NSO webui port number
        :username: Username to authenticate against NSO
        :password: Password to authenticate against NSO
        :cert_verify: Certificate verification should be False mostly
        :fabric: ACI fabric information
        """
        self.verify = cert_verify
        self.url = f"{protocol}://{host}:{port}/restconf/data"
        self.auth = (username, password)
        self.headers = {"Accept": "application/yang-data+json"}
        self.fabric = fabric

    def download_acidc_vrf_cdb(self) -> None:
        """Get service JSON data from NSO and save it."""
        url = self.url + f"/acidc:aci-site={self.fabric}/vrf-config"
        rsp = requests.get(url=url, headers=self.headers, auth=self.auth, verify=self.verify, timeout=60)
        with open(file="./data/acidc_vrf.json", mode="w", encoding="utf-8") as json_data:
            json_data.write(rsp.text)

    @staticmethod
    def write_acidc_vrfs_to_database() -> None:
        """Get service JSON data from saved file and write it to database.

        Returns:
            None
        """
        with open(file="./data/acidc_vrf.json", mode="r", encoding="utf-8") as json_data:
            data = json.load(json_data)

        acidc_vrf = [{
            "name": vrf_config.get("name"),
            "description": vrf_config.get("description"),
            "enforcement": vrf_config.get("enforcement"),
            "vrf_type": vrf_config.get("vrf-type")
        } for vrf_config in data["acidc:vrf-config"]]

        with models.Session() as session:
            session.bulk_insert_mappings(models.AcidcVrf, acidc_vrf)
            session.commit()
