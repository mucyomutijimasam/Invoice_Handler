class BillingError(Exception):
    """Base class for all billing exceptions."""
    def __init__(self, message="A billing error occurred"):
        self.message = message
        super().__init__(self.message)

class InsufficientCredits(BillingError):
    def __init__(self, required, available):
        self.required = required
        self.available = available
        self.message = f"Need {required} credits, but only have {available}."
        super().__init__(self.message)

class NoActiveSubscription(BillingError):
    pass


class SubscriptionExpired(BillingError):
    pass
