import signal
import subprocess
from .base import cli

exit_signal = False


def sigterm_handler(signum, frame):
    global exit_signal
    exit_signal = True


@cli.command()
def run_scheduler():
    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)
    args = ["taskiq", "scheduler", "app.broker_app:scheduler", "--skip-first-run"]

    proc = subprocess.Popen(args)
    while not exit_signal:
        try:
            proc.wait(0.25)
        except subprocess.TimeoutExpired:
            pass
    proc.send_signal(signal.SIGINT)
    proc.wait()
