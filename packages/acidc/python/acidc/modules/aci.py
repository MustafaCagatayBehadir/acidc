"""ACI REST API MODULE."""

import json
import requests
import urllib3

urllib3.disable_warnings()


class Aci:
    """Defines cisco aci connection parameters."""

    def __init__(
        self,
        protocol: str,
        host: str,
        port: str,
        username: str,
        password: str,
        cert_verify: bool,
    ):
        """Initialize attributes for establishing connection to APIC.

        :protocol: Transport protocol can be http | https
        :host: APIC IP address or hostname
        :port: APIC webui port number
        :username: Username to authenticate against NSO
        :password: Password to authenticate against NSO
        :cert_verify: Certificate verification should be False mostly
        """
        self.verify = cert_verify
        self.url = f"{protocol}://{host}:{port}/api"
        self.cookies_string = ""
        self.user = username
        self.passwd = password
        self.headers = {}

    def get_cookies(self):
        """Get cookie from APIC and assign it to instance variable cookies_string."""
        url = self.url + "/aaaLogin.json"
        payload = {"aaaUser": {"attributes": {"name": self.user, "pwd": self.passwd}}}
        rsp = requests.post(url, data=json.dumps(payload), verify=self.verify, timeout=5).json()
        token = rsp['imdata'][0]['aaaLogin']['attributes']['token']
        self.headers.update({"Cookie": f"APIC-Cookie={token}"})

    def get_vrf_count(self):
        """Get total VRF number from ACI."""
        url = self.url + "/node/class/fvCtx.json?rsp-subtree-include=count&query-target-filter= \
            and(not(wcard(fvCtx.dn,%22__ui_%22)),not(wcard(fvCtx.annotation,%22shadow:yes%22)))"

        rsp = requests.get(url, headers=self.headers, verify=self.verify, timeout=5).json()
        vrf_count = int(rsp["imdata"][0]["moCount"]["attributes"]["count"])
        return vrf_count
