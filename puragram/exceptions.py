class GrambotError(Exception):
    pass


class TelegramError(GrambotError):
    def __init__(self, description, error_code=None, response=None):
        msg = f"[{error_code}] {description}" if error_code else description
        super().__init__(msg)
        self.description = description
        self.error_code = error_code
        self.response = response


class SecurityError(GrambotError):
    pass


class ValidationError(GrambotError):
    pass


class WebhookError(GrambotError):
    pass