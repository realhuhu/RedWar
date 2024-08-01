import re
import json
import shutil
import asyncio
from tqdm import tqdm
from io import StringIO
from hashlib import md5
from pathlib import Path
from xml.dom.minidom import parse
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import numpy as np
import pandas as pd
from PIL import Image

from util import decode, extract, fetch_file, fetch_txt

root = Path(__file__).absolute().parent / "data"
img_root = root / "img"
swf_root = root / "swf"
txt_root = root / "txt"
web_root = root / "web"
bin_root = root / "bin"

appURL = "https://100616028cdn-1251006671.file.myqcloud.com/100616028/res/20120522/flash/config_%s.xml"
storageURL = "https://100616028cdn-1251006671.file.myqcloud.com/100616028/res/20120522/"
swfURL = "https://100616028cdn-1251006671.file.myqcloud.com/100616028/res/20120522/winPanel/"


async def download_xml(session: aiohttp.ClientSession, version):
    version = version.split("_")[-1]

    if version:
        app, _ = await fetch_txt(session, appURL % version, "app.xml")

        with open("app.xml", "r+", encoding="utf-8") as f:
            f.seek(0)
            f.truncate(0)
            f.write(app)

    dom = parse("app.xml")
    return dom.documentElement


async def download_txt(session: aiohttp.ClientSession, xml):
    for i in xml.getElementsByTagName("assets")[0].childNodes:
        if i.nodeName != "asset":
            continue

        if i.getAttribute("name") == "lang":
            url = i.getAttribute("value").replace("${storageURL}", storageURL)
            txt, _ = await fetch_txt(session, url, i.getAttribute("name"), encoding='utf-8-sig')

            with open(txt_root / f"lang.json", "w", encoding="utf-8") as f:
                json.dump(
                    json.loads(txt.replace(r"\“", "").replace(r"\”", "")),
                    f,
                    ensure_ascii=False,
                    indent=4,
                )


async def download_dat(session: aiohttp.ClientSession, xml):
    tasks = []
    for i in xml.getElementsByTagName("data")[0].childNodes:
        if i.nodeName != "asset":
            continue

        url = i.getAttribute("value").replace("${storageURL}", storageURL)
        name = url.split("/")[-1].split(".")[0]
        name = re.sub(r'_\d+$', '', name)
        tasks.append(fetch_txt(session, url, name, encoding="gbk"))

    results = await asyncio.gather(*tasks)
    for txt, name in results:
        if txt.endswith("03a33cd9a31ee58c"):
            res = decode(txt)
            res = "\n".join(res.split('\n')[:-1])
            res = pd.read_csv(StringIO(res), sep='\t')
            data = res.fillna('')
        else:
            data = pd.read_csv(StringIO(txt), sep="\t")
        data.to_csv(web_root / f"{name}.csv", index=False)


async def download_swf(session: aiohttp.ClientSession, xml):
    tasks = []

    for i in xml.getElementsByTagName("assets")[0].childNodes:
        if i.nodeName != "asset":
            continue

        if i.getAttribute("name") == "game":
            url = i.getAttribute("value").replace("${storageURL}", storageURL)
            tasks.append(fetch_file(session, url, swf_root))

    panels = pd.read_csv("data/web/WindowResData.csv")
    panels.columns = panels.iloc[0]
    panels = panels.drop(0)
    total, _ = panels.shape

    for k, panel in panels.iterrows():
        _, swf_name = panel
        tasks.append(fetch_file(session, swfURL + swf_name, swf_root))

    await asyncio.gather(*tasks)


def decode_bin(path: Path):
    for i in path.iterdir():
        try:
            df = pd.read_csv(i, sep="\t", encoding="gbk")
            df.to_csv(bin_root / f"{str(i).split('.')[-2].split('_')[1]}.csv", index=False)
        except:
            print(f"跳过{i}")


def extract_image(source: Path, output: Path):
    print("导出图片")
    red_war = None
    with ThreadPoolExecutor(max_workers=12) as executor:
        for i in source.iterdir():
            if i.name == 'RedWar.swf':
                red_war = i
                continue

            executor.submit(extract, i, output, False)

    return red_war


def rename_image(path: Path):
    print("重命名图片")
    for i in tqdm(list(path.iterdir())):
        for j in i.iterdir():
            try:
                img = Image.fromarray(np.asarray(Image.open(j)))
                img.save(i / f"img{md5(img.tobytes()).hexdigest()}{j.suffix}")
            except FileExistsError:
                pass
            except Exception as e:
                print(f"{e}:{j}")
            finally:
                j.unlink()


def refresh():
    if root.exists():
        shutil.rmtree(root)

    img_root.mkdir(exist_ok=True, parents=True)
    swf_root.mkdir(exist_ok=True, parents=True)
    txt_root.mkdir(exist_ok=True, parents=True)
    web_root.mkdir(exist_ok=True, parents=True)
    bin_root.mkdir(exist_ok=True, parents=True)


async def main():
    async with aiohttp.ClientSession() as session:
        app_xml = await download_xml(session, input('输入version:>>>'))
        refresh()

        await download_txt(session, app_xml)
        await download_dat(session, app_xml)
        await download_swf(session, app_xml)

        red_war = extract_image(swf_root, img_root)
        extract(red_war, img_root, True)
        rename_image(img_root)

        decode_bin(Path(input("输入binary路径:>>>")))


if __name__ == "__main__":
    asyncio.run(main())
