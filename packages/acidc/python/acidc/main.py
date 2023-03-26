"""ACI Scalability Monitoring Service."""
import ncs
from . import acidc_vrf_subscriber


class Main(ncs.application.Application):
    """Main class."""

    def setup(self):
        """Register service and actions."""
        self.log.info('Main RUNNING')

        # Acidc Vrf TwoPhaseSubscriber
        self.vrf_two_phase_subscriber = acidc_vrf_subscriber.AcidcVrfTwoPhaseSubscriber(name='acidc', app=self)
        self.vrf_two_phase_subscriber.start()

        # Acidc Vrf Subscriber
        self.vrf_subscriber = acidc_vrf_subscriber.AcidcVrfSubscriber(app=self)
        self.vrf_subscriber.start()

    def teardown(self):
        """Teardown."""
        self.log.info('Main FINISHED')
        self.vrf_two_phase_subscriber.stop()
        self.vrf_subscriber.stop()
