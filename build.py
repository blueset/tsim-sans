import glob
from build import dump_file, build_file
from download import download_all
from convert import convert_all

if __name__ == "__main__":
    print("Downloading files...")
    download_all()

    print("Dumping files...")
    for i in glob.glob("out/*.otf"):
        print(i, "=>")
        print(dump_file(i))

    print("Converting files...")
    convert_all()

    print("Building files...")
    for i in glob.glob("out/*.json"):
        print(i, "=>")
        print(build_file(i))

    print("Done.")
