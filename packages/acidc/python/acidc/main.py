"""ACI Scalability Monitoring Service."""
import ncs
from ncs.application import Service
from . import acidc_vrf_subscriber


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
