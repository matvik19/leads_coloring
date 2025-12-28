import signal
import subprocess
import click
from app.core.settings import config
from .base import cli

exit_signal = False


def sigterm_handler(signum, frame):
    global exit_signal
    exit_signal = True


@cli.command()
@click.option("-d", "--devel", is_flag=True, help="Development mode with reload")
def run_worker(devel: bool = False):
    """Запустить FastStream worker"""
    global exit_signal

    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    args = ["faststream", "run", "app.broker_app:app"]
    if devel:
        args.append("--reload")
    else:
        args.append("--workers")
        args.append(str(config.tasks_cfg.WORKERS))

    proc = subprocess.Popen(args)
    while not exit_signal:
        try:
            proc.wait(0.25)
        except subprocess.TimeoutExpired:
            pass
    proc.send_signal(signal.SIGINT)
    proc.wait()
