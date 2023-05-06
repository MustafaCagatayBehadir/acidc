"""acidc exception module."""


class VrfThresholdError(Exception):
    """Exception raised for vrf threshold errors.

    Attributes:
        threshold: vrf threshold value
        message: explanation of the error
    """

    def __init__(self, threshold, message):
        """Exception initialization method."""
        self.threshold = threshold
        self.message = message
        super().__init__(self.message)
