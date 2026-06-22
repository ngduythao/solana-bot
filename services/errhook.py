
import os, sys, traceback

SENTRY_DSN = os.getenv("SENTRY_DSN","")
ROLLBAR_TOKEN = os.getenv("ROLLBAR_TOKEN","")

def capture(exc: BaseException):
    msg = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if SENTRY_DSN:
        try:
            import sentry_sdk
            if not getattr(capture, "_sentry_init", False):
                sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.05)
                capture._sentry_init = True
            sentry_sdk.capture_message(msg)
        except Exception:
            pass
    if ROLLBAR_TOKEN:
        try:
            import rollbar
            if not getattr(capture, "_rollbar_init", False):
                rollbar.init(ROLLBAR_TOKEN, environment=os.getenv("REGION","prod"))
                capture._rollbar_init = True
            rollbar.report_message(msg, 'error')
        except Exception:
            pass
