"""INFLUXDB API MODULE."""

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS


class Influx:
    """Defines influx connection parameters."""

    def __init__(self, protocol: str, host: str, port: str, bucket: str, org: str, token: str) -> None:
        """Initialize attributes for establishing connection to APIC.

        :protocol: Transport protocol can be http | https
        :host: InfluxDB IP address or hostname
        :port: InfluxDB port number
        :bucket: Named location where time series data is stored
        :org: Organization name
        :token: Admin's token
        """
        self.bucket = bucket
        self.org = org
        self.client = influxdb_client.InfluxDBClient(url=f"{protocol}://{host}:{port}", token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def create_record(self, measurement: str, location: str, fieldkey: str, filedvalue: float) -> None:
        """Create record at influxdb.

        Args:
            measurement: The part of the InfluxDB data structure that describes the data stored in the associated
            fields. Measurements are strings.
            location: Data location point
            fieldkey: The key part of the key-value pair that makes up a field. Field keys are strings and they store
            metadata.
            filedvalue: The value part of the key-value pair that makes up a field. Field values are the actual data;
            they can be strings, floats, integers, or booleans. A field value is always associated with a timestamp.

        Returns:
            None
        """
        p = influxdb_client.Point(measurement).tag("location", location).field(fieldkey, filedvalue)
        self.write_api.write(bucket=self.bucket, org=self.org, record=p)
