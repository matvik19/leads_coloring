from typing import Any, Callable, Dict
from gunicorn.app.base import BaseApplication
from app.core.settings import config
from .base import cli


class GunicornApplication(BaseApplication):
    def __init__(self, application: Callable, options: Dict[str, Any] = None):
        self.options = options or {}
        self.application = application
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


@cli.command()
def run_prod_server():
    GunicornApplication(
        "app.web_app:application",
        {
            "bind": f"{config.web_cfg.BIND_IP}:{config.web_cfg.PORT}",
            "workers": config.web_cfg.WORKERS,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "pidfile": config.web_cfg.GUNICORN_PID_LOCATION,
            "max_requests": config.web_cfg.MAX_REQUESTS,
            "max_requests_jitter": config.web_cfg.MAX_REQUESTS_JITTER,
        },
    ).run()
