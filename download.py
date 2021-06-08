from posixpath import basename
import subprocess
import glob
import os
import shutil
from urllib.parse import urlparse

def aria_download(url, dest):
    subprocess.run(["aria2c", "-Z", *url, "-d", dest], check=True)
    # print(repr(" ".join(["aria2c", *url, "-d", dest])))
    filenames = []
    for u in url:
        filenames.append(
            os.path.basename(urlparse(u).path)
        )
    return filenames


def unzip(filename):
    path_name = filename.replace(".zip", "")
    subprocess.run(["unzip", filename, "-d", path_name], check=True)
    for i in glob.glob(path_name + "/**/*.otf", recursive=True):
        shutil.move(i, path_name)


def download_all():
    if not os.path.exists("fonts"):
        os.mkdir("fonts")
    files = aria_download([
        "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansSC.zip",
        "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansTC.zip",
        "https://github.com/adobe-fonts/source-han-sans/releases/download/2.004R/SourceHanSansJ.zip",
        "https://github.com/welai/glow-sans/releases/download/v0.92/GlowSansJ-Compressed-v0.92.zip",
        "https://github.com/welai/glow-sans/releases/download/v0.92/GlowSansSC-Compressed-v0.92.zip",
        "https://github.com/welai/glow-sans/releases/download/v0.92/GlowSansTC-Compressed-v0.92.zip",
    ], "fonts")

    for i in files:
        unzip(f"fonts/{i}")

if __name__ == "__main__":
    download_all()
