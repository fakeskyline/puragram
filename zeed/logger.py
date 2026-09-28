import logging
import sys

from .security import redact


class _RedactingFormatter(logging.Formatter):
    def format(self, record):
        try:
            record.msg = redact(str(record.msg))
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: (redact(str(v)) if isinstance(v, str) else v)
                        for k, v in record.args.items()
                    }
                else:
                    record.args = tuple(
                        redact(str(a)) if isinstance(a, str) else a
                        for a in record.args
                    )
        except Exception:
            pass
        return super().format(record)


def get_logger(name="zeed"):
    return logging.getLogger(name)


def setup_logging(level=logging.INFO,
                  fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                  redact_secrets=True):
    handler = logging.StreamHandler(sys.stdout)
    formatter_cls = _RedactingFormatter if redact_secrets else logging.Formatter
    handler.setFormatter(formatter_cls(fmt, datefmt="%H:%M:%S"))
    root = logging.getLogger("zeed")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False
    return root


def quiet():
    logging.getLogger("zeed").setLevel(logging.CRITICAL)