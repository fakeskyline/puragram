class ZeedError(Exception):
    pass


class TelegramError(ZeedError):
    def __init__(self, description, error_code=None, response=None):
        msg = f"[{error_code}] {description}" if error_code else description
        super().__init__(msg)
        self.description = description
        self.error_code = error_code
        self.response = response


class SecurityError(ZeedError):
    pass


class ValidationError(ZeedError):
    pass


class WebhookError(ZeedError):
    pass