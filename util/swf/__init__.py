import requests
from pathlib import Path
from typing import Tuple


def download(url: str, dirname: Path) -> Tuple[str, Path]:
    dirname.mkdir(exist_ok=True, parents=True)

    print(f"下载{url}到{dirname}")
    response = requests.get(url)
    name = url.split("/")[-1].split(".")[0].split("_20")[0]
    path = dirname / f"{name}.swf"

    with open(path, "wb") as f:
        f.write(response.content)

    return name, path
