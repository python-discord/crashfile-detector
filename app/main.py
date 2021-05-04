import asyncio
import logging

import aiohttp
from fastapi import FastAPI, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from app import models

log = logging.getLogger(__name__)

app = FastAPI(
    title="Discord crasher file detector",
    version="0.0.1",
    docs_url=None,
    redoc_url=None
)
templates = Jinja2Templates(directory="app/templates")

MAX_LENGTH = 10 * 1024 * 1024  # multiply by 1024 twice to get Bytes


@app.on_event("startup")
async def startup() -> None:
    """Create a aiohttp session and setup logging."""
    app.state.http_session = aiohttp.ClientSession(raise_for_status=True)


@app.on_event("shutdown")
async def shutdown() -> None:
    """Close down the app."""
    await app.state.http_session.close()


@app.get("/", include_in_schema=False)
def docs() -> HTMLResponse:
    """Return the API docs."""
    template = templates.get_template("docs.html")
    return HTMLResponse(template.render())


@app.get("/ping", tags=["General Endpoints"], response_model=models.Pong)
def ping() -> models.Pong:
    """A simple ping/pong endpoint for aliveness checks."""
    return models.Pong()


@app.post("/detectfile", tags=["General Endpoints"], response_model=models.FileInfo)
async def detect_file(url: models.SuspectUrl) -> models.FileInfo:
    """Stream the file to ffprobe to check if it would crash Discord."""
    async with app.state.http_session.get(url.url) as resp:
        try:
            length = int(resp.headers["Content-Length"])
        except KeyError:
            raise HTTPException(status_code=400, detail=models.ErrorMessages.NO_CONTENT_HEADER)
        except ValueError:
            raise HTTPException(status_code=400, detail=models.ErrorMessages.NON_INT_CONTENT_HEADER)
        if length > MAX_LENGTH:
            raise HTTPException(status_code=413, detail=models.ErrorMessages.CONTENT_TOO_BIG)

    proc = await asyncio.create_subprocess_exec(
        "/usr/bin/ffprobe",
        "-i", url.url,
        "-v", "error",
        "-show_entries", "frame=pkt_pts_time,width,height,pix_fmt",
        "-select_streams", "v",
        "-of", "csv=p=0",
        stdout=asyncio.subprocess.PIPE
    )

    w, h, fmt = None, None, None

    scanned_frames = 0
    safe = True
    async for line in proc.stdout:
        scanned_frames += 1
        line = line.decode().strip()

        _pkt_time, frame_w, frame_h, frame_fmt = line.split(",")

        if w is None:
            w = frame_w

        if h is None:
            h = frame_h

        if fmt is None:
            fmt = frame_fmt

        if w != frame_w or h != frame_h or fmt != frame_fmt:
            safe = False
            proc.terminate()
            break

    await proc.wait()

    return {
        "safe": safe,
        "scanned_count": scanned_frames,
        "dimensions": {
            "width": w,
            "height": h
        },
        "format": str(fmt)
    }
