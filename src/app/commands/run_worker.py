import asyncio
import signal
import click
from .base import cli

exit_signal = False


def sigterm_handler(signum, frame):
    global exit_signal
    exit_signal = True


@cli.command()
@click.option("-d", "--devel", is_flag=True, help="Development mode with reload")
def run_worker(devel: bool = False):
    """Запустить FastStream worker"""

    # Импортируем app из broker_app
    from app.broker_app import app

    # Запускаем FastStream app напрямую через asyncio
    # Это обходит необходимость в faststream[cli]
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
