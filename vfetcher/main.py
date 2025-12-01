import logging

import colorlog
import typer

from vfetcher.commands.channel import channel
from vfetcher.commands.download import download

app = typer.Typer()
app.command()(download)
app.command()(channel)


if __name__ == "__main__":
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            fmt="[%(asctime)s] %(log_color)s%(levelname)8s%(reset)s │ %(message)s",
            datefmt="%y%m%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    logging.getLogger("httpx").setLevel(logging.WARNING)
    app()
