import subprocess
from app.core.settings import config
from .base import cli


@cli.command()
def run_prod_server():
    """Запустить production сервер через Gunicorn"""
    args = [
        "gunicorn",
        "-w", str(config.web_cfg.WORKERS),
        "-k", "uvicorn.workers.UvicornWorker",
        "-b", f"{config.web_cfg.BIND_IP}:{config.web_cfg.PORT}",
        "--max-requests", str(config.web_cfg.MAX_REQUESTS),
        "--max-requests-jitter", str(config.web_cfg.MAX_REQUESTS_JITTER),
        "app.web_app:application"
    ]
    subprocess.run(args)
