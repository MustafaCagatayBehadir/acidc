"""NSO Service Discovery Abstraction Module."""

import argparse
from time import sleep
from discovery.nso.services import Nso
from discovery.nso.models import clear_db


def parseargs():
    """Argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", help="NSO protocol", default="https")
    parser.add_argument("--nso_ip", help="NSO IP address", required=True)
    parser.add_argument("--port", help="NSO port", default="8443")
    parser.add_argument("--username", help="NSO username", required=True)
    parser.add_argument("--password", help="NSO password", required=True)
    parser.add_argument("--fabric", help="ACI site fabric information. Ex. 'BTS-FABRIC-001,10.0.0.1'", required=True)
    return parser.parse_args()


def clear_all_tables():
    """Clear all table records in postgres db."""
    clear_db()


def acidc(args):
    """Acidc global function."""
    nso = Nso(protocol=args.protocol,
              host=args.nso_ip,
              port=args.port,
              username=args.username,
              password=args.password,
              cert_verify=False,
              fabric=args.fabric)
    nso.download_acidc_vrf_cdb()
    nso.write_acidc_vrfs_to_database()


def infinite_loop():
    """Prevent container to exit."""
    while True:
        sleep(1)


if __name__ == "__main__":
    clear_all_tables()
    acidc(parseargs())
    infinite_loop()
