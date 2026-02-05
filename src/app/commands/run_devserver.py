import uvicorn
from .base import cli


@cli.command()
def run_dev_server():
    """Запустить dev сервер с автоперезагрузкой"""
    uvicorn.run("app.web_app:application", port=8000, reload=True, host="0.0.0.0")
