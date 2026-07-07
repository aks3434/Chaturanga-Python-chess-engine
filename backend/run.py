"""
Launcher script -- use this instead of the `uvicorn` CLI directly on Windows.

Why this file exists: chess.engine.popen_uci() needs to spawn a subprocess,
which on Windows requires the ProactorEventLoop. Uvicorn's default loop
setup doesn't support subprocesses on Windows, causing a NotImplementedError
the moment we try to launch the engine. Setting the event loop policy here,
before uvicorn creates its loop, fixes it. On macOS/Linux this is a no-op
(those platforms don't have this restriction) so it's safe to use everywhere.
"""
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    # reload=False on purpose: uvicorn's --reload spawns the real server in a
    # separate subprocess, which doesn't reliably inherit the Proactor policy
    # set above on Windows -- bringing back the NotImplementedError. Restart
    # this script manually after code changes for now.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001, reload=False)