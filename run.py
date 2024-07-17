import json
import shutil
import time
from tqdm import tqdm
from io import StringIO
from hashlib import md5
from pathlib import Path
from xml.dom.minidom import parse
from datetime import datetime, timedelta

import requests
import numpy as np
import pandas as pd
from PIL import Image
from util import decode, download, extract

root = Path(__file__).absolute().parent / "data"
img_root = root / "img"
swf_root = root / "swf"
txt_root = root / "txt"
web_root = root / "web"
bin_root = root / "bin"

appURL = "https://100616028cdn-1251006671.file.myqcloud.com/100616028/res/20120522/flash/config_%s.xml"
storageURL = "https://100616028cdn-1251006671.file.myqcloud.com/100616028/res/20120522/"
swfURL = "https://100616028cdn-1251006671.file.myqcloud.com/100616028/res/20120522/winPanel/"


def get_version():
    current = datetime.now()
    seq_num = 4

    while datetime.now() - current < timedelta(days=5):
        version = f"{current.strftime('%Y%m%d')}{seq_num:02d}"
        print(f"尝试获取版本{version}")

        if seq_num == 1:
            current -= timedelta(days=1)
            seq_num = 4
        else:
            seq_num -= 1

        if "-46628" not in requests.get(appURL % version).text:
            return version

        time.sleep(1)

    return None


def download_xml(version):
    app = requests.get(appURL % version).text

    with open("app.xml", "r+", encoding="utf-8") as f:
        f.seek(0)
        f.truncate(0)
        f.write(app)

    dom = parse("app.xml")
    return dom.documentElement


def download_dat(xml):
    for i in xml.getElementsByTagName("data")[0].childNodes:
        if i.nodeName != "asset":
            continue

        url = i.getAttribute("value").replace("${storageURL}", storageURL)
        name = url.split("/")[-1].split(".")[0]
        name = name.split("_20")[0]

        print(f"获取dat：{name}")

        response = requests.get(url)
        response.encoding = "gbk"
        if response.text.endswith("03a33cd9a31ee58c"):
            res = decode(response.text)
            res = "\n".join(res.split('\n')[:-1])
            res = pd.read_csv(StringIO(res), sep='\t')
            data = res.fillna('')
        else:
            data = pd.read_csv(StringIO(response.text), sep="\t")
        data.to_csv(web_root / f"{name}.csv", index=False)


def download_redwar(xml):
    for i in xml.getElementsByTagName("assets")[0].childNodes:
        if i.nodeName != "asset":
            continue

        if i.getAttribute("name") == "game":
            url = i.getAttribute("value").replace("${storageURL}", storageURL)
            name, path = download(url, swf_root)
            extract(path, img_root / name)


def decode_redwar(path: Path):
    for i in path.iterdir():
        df = pd.read_csv(i, sep="\t", encoding="gbk")
        df.to_csv(bin_root / f"{str(i).split('.')[-2].split('_')[1]}.csv", index=False)


def download_txt(xml):
    for i in xml.getElementsByTagName("assets")[0].childNodes:
        if i.nodeName != "asset":
            continue

        if i.getAttribute("name") == "lang":
            url = i.getAttribute("value").replace("${storageURL}", storageURL)
            res = requests.get(url)
            res.encoding = "utf-8-sig"

            with open(txt_root / f"lang.json", "w", encoding="utf-8") as f:
                json.dump(
                    json.loads(res.text.replace(r"\“", "").replace(r"\”", "")),
                    f,
                    ensure_ascii=False,
                    indent=4,
                )


def download_img():
    panels = pd.read_csv("data/web/WindowResData.csv")
    panels.columns = panels.iloc[0]
    panels = panels.drop(0)
    total, _ = panels.shape

    for k, panel in panels.iterrows():
        _, swf_name = panel
        print(f"({k}/{total})", end="\t")
        name, path = download(swfURL + swf_name, swf_root)
        extract(path, img_root / name)


def rename(path: Path):
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


if __name__ == "__main__":
    version = get_version()

    if not version:
        print("未获取到版本")
        exit()

    if input(f"获取到版本:{version}，是否更新(y/N)>>>:") != "y":
        print("已退出")
        exit()

    refresh()
    app_xml = download_xml(version)
    download_txt(app_xml)
    download_dat(app_xml)
    download_redwar(app_xml)
    decode_redwar(Path(input("输入binary路径>>>:")))
    download_img()
    rename(img_root)
