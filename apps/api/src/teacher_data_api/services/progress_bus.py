from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import AsyncIterator


_queues: dict[str, list[asyncio.Queue]] = defaultdict(list)


def subscribe(job_id: str) -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _queues[job_id].append(q)
    return q


def unsubscribe(job_id: str, q: asyncio.Queue) -> None:
    try:
        _queues[job_id].remove(q)
    except ValueError:
        pass


async def publish(job_id: str, event: str, data: dict) -> None:
    for q in list(_queues.get(job_id, [])):
        await q.put({"event": event, "data": data})


async def stream(job_id: str) -> AsyncIterator[str]:
    q = subscribe(job_id)
    try:
        while True:
            msg = await asyncio.wait_for(q.get(), timeout=30)
            yield f"event: {msg['event']}\ndata: {__import__('json').dumps(msg['data'], ensure_ascii=False)}\n\n"
            if msg["event"] in ("completed", "failed"):
                break
    except asyncio.TimeoutError:
        yield "event: heartbeat\ndata: {}\n\n"
    finally:
        unsubscribe(job_id, q)
