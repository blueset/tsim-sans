import subprocess
import glob

def dump_file(source):
    out = source.replace(".otf", ".json")
    subprocess.run([
        "otfccdump", 
        source, 
        "--pretty", "--ignore-glyph-order", "--hex-cmap", 
        "-o", out
    ], check=True)
    return out

def build_file(source):
    out = source.replace(".json", ".otf")
    subprocess.run([
        "otfccbuild", 
        "-q", "--dummy-dsig", "--merge-features",
        "--merge-lookups", "--subroutinize",
        source, "-o", out
    ], check=True)
    return out


if __name__ == "__main__":
    for i in glob.glob("out/*.json"):
        print(i, "=>")
        print(build_file(i))