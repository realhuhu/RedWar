import re
import asyncio
from typing import Tuple

import aiohttp
from pathlib import Path

sem = asyncio.Semaphore(10)


async def fetch_file(session: aiohttp.ClientSession, url: str, dirname: Path):
    async with sem:
        name = url.split("/")[-1].split(".")[0]
        name = re.sub(r'_\d{8,10}$', '', name)
        path = dirname / f"{name}.swf"

        print(f"[下载文件 {name}] {url.split('/')[-1]} 到 {path}")

        dirname.mkdir(exist_ok=True, parents=True)
        async with session.get(url) as response:
            with open(path, "wb") as f:
                f.write(await response.read())


async def fetch_txt(session: aiohttp.ClientSession, url, name, encoding="utf-8") -> Tuple[str, str]:
    async with sem:
        print(f"[下载文本 {name}] {url.split('/')[-1]}")
        async with session.get(url) as res:
            return await res.text(encoding=encoding), name
