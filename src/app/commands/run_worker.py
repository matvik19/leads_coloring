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
@click.option("-d", "--devel", type=bool)
def run_worker(devel: bool = False):
    global exit_signal

    signal.signal(signal.SIGINT, sigterm_handler)
    signal.signal(signal.SIGTERM, sigterm_handler)

    args = ["taskiq", "worker", "app.broker_app:broker"]
    if devel:
        args.append("--reload")
    else:
        args.append("--workers")
        args.append(str(config.tasks_cfg.WORKERS))
        args.append("--max-tasks-per-child")
        args.append(str(config.tasks_cfg.MAX_TASKS_PER_CHILD))
    proc = subprocess.Popen(args)
    while not exit_signal:
        try:
            proc.wait(0.25)
        except subprocess.TimeoutExpired:
            pass
    proc.send_signal(signal.SIGINT)
    proc.wait()
