import os
import re
from pathlib import Path
from subprocess import Popen, PIPE
from multiprocessing import Pool, cpu_count


def check_command(command):
    result = True
    try:
        p = Popen([command], stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
    except:
        result = False
    finally:
        pass

    return result


class SWFExtractor:
    def __init__(self):
        self.tool_name = 'swf.exe'
        self.is_available = check_command(self.tool_name)

    @staticmethod
    def get_ids(raw: str):
        value_list = [int(x.group()) for x in re.finditer(r' \d+(?=[,x])', raw)]
        range_list = [x.group() for x in re.finditer(r'\d+-\d+', raw)]

        for range_value in range_list:
            start, end = [int(x.group()) for x in re.finditer(r'\d+', range_value)]
            end = end + 1
            value_list.extend(range(start, end))

        value_list.sort()

        return value_list

    def get_images(self, package):
        command = [self.tool_name, package]

        p = Popen(command, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        outputs = out.decode("utf-8").splitlines()

        jpgs = []
        pngs = []

        for output in outputs:
            if output.startswith(' [-j]'):
                jpgs = self.get_ids(output)
            elif output.startswith(' [-p]'):
                pngs = self.get_ids(output)

        return jpgs, pngs

    def extract_jpg(self, swf: Path, jpg_dir: Path, jpg_id: str):
        jpg_path = jpg_dir / f"{jpg_id}.png"

        command = [self.tool_name, '-j', jpg_id, '-o', jpg_path, swf]
        p = Popen(command, stderr=PIPE, stdout=PIPE)
        out, err = p.communicate()

        if err:
            print(err)

    def extract_png(self, swf: Path, png_dir: Path, png_id: str):
        png_path = png_dir / f"{png_id}.png"

        command = [self.tool_name, '-p', png_id, '-o', png_path, swf]
        p = Popen(command, stderr=PIPE, stdout=PIPE)
        out, err = p.communicate()

        if err:
            print(err)

    def process_image(self, image_id, swf, output, image_type):
        if image_type == 'jpg':
            self.extract_jpg(swf, output, image_id)
        elif image_type == 'png':
            self.extract_png(swf, output, image_id)

    def process_task(self, task):
        image_id, swf, output, image_type = task
        self.process_image(image_id, Path(swf), Path(output), image_type)

    def extract_images(self, swf: Path, output: Path, p):
        if not os.path.exists(swf):
            print(f"[导出图片 {swf.name}] 文件不存在：{swf}")
            return

        jpg_list, png_list = self.get_images(swf)

        if not len(jpg_list) and not len(png_list):
            print(f"[导出图片 {swf.name}] 无图片资源")
            return

        print(f"[导出图片 {swf.name}] JPG图片{len(jpg_list)}张，PNG图片{len(png_list)}张，导出至{output}")

        output.mkdir(parents=True, exist_ok=True)

        if p:
            tasks = []
            if len(jpg_list):
                tasks.extend((str(jpg_id), str(swf), str(output), 'jpg') for jpg_id in jpg_list)

            if len(png_list):
                tasks.extend((str(png_id), str(swf), str(output), 'png') for png_id in png_list)

            with Pool(cpu_count() * 2) as pool:
                for _ in pool.imap_unordered(self.process_task, tasks):
                    pass
                pool.close()
                pool.join()
        else:
            if len(jpg_list):
                for jpg_id in jpg_list:
                    self.extract_jpg(swf, output, str(jpg_id))

            if len(png_list) != 0:
                for png_id in png_list:
                    self.extract_png(swf, output, str(png_id))


def extract(swf: Path, output: Path, p):
    extractor = SWFExtractor()
    extractor.extract_images(swf, output / swf.name.split(".")[0], p)
