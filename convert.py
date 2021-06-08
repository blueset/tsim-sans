import json
import os
from timeit import default_timer as timer


def contour_offset(contour, x, y):
    for path in contour:
        for pt in path:
            pt["x"] += x
            pt["y"] += y
    return contour


def apply_palt(data, glyphs_modified):
    palt_key = [i for i in data["GPOS"]["lookups"].keys() if i.startswith("lookup_palt")][0]
    palt = data["GPOS"]["lookups"][palt_key]
    for t in palt["subtables"]:
        for glyph, param in t.items():
            if glyph not in data["glyf"]:
                continue
            glyph_data = data["glyf"][glyph]
            if "dx" in param:
                glyph_data["contours"] = contour_offset(glyph_data["contours"], param["dx"], 0)
            if "dWidth" in param:
                glyph_data["advanceWidth"] += param["dWidth"]
            data["glyf"][glyph] = glyph_data
            glyphs_modified.add(glyph)

    # drop palt table refs
    for i in data["GPOS"]["languages"].values():
        i["features"] = [j for j in i["features"] if not j.startswith("palt_")]
    
    features_to_delete = [i for i in data["GPOS"]["features"].keys() if i.startswith("palt_")]
    for f in features_to_delete:
        del data["GPOS"]["features"][f]

    lookups_to_delete = [i for i in data["GPOS"]["lookups"].keys() if i.startswith("lookup_palt_")]
    for l in lookups_to_delete:
        del data["GPOS"]["lookups"][l]

    data["GPOS"]["lookupOrder"] = [
        j for j in data["GPOS"]["lookupOrder"] if not j.startswith("lookup_palt_")]
    
    return data


def dup_vpal_glyph(data, source, gmap_subtable, cid):
    """make a new glyph for vpal."""
    dest = f"glyph{cid}"
    data["glyf"][dest] = data["glyf"][source].copy()

    gmap_subtable[source] = dest
    for k, v in data["GPOS"]["lookups"].items():
        if k.startswith("lookup_vpal_"):
            for t in v["subtables"]:
                if source in t:
                    t[dest] = t[source]
                    del t[source]
                    return



def dup_vpal_glyphs(data):
    vpal_common_glyphs = []
    vpal_key = [i for i in data["GPOS"]["lookups"].keys() if i.startswith("lookup_vpal")][0]
    vpal = data["GPOS"]["lookups"][vpal_key]
    for t in vpal["subtables"]:
        for glyph in t.keys():
            if glyph.startswith("uni3"):
                vpal_common_glyphs.append(glyph)
    
    subtable = None
    for k, v in data["GSUB"]["lookups"].items():
        if k.startswith("lookup_vert_"):
            for t in v["subtables"]:
                if "uni3042" in t:
                    subtable = t
                    break
        if subtable:
            break
    
    max_cid = 0
    for i in data["glyf"].values():
        max_cid = max(max_cid, i["CFF_CID"])

    for glyph in vpal_common_glyphs:
        max_cid += 1
        dup_vpal_glyph(data, glyph, subtable, max_cid)
    
    return data


def apply_vpal(data, glyphs_to_avoid):
    vpal_key = [i for i in data["GPOS"]["lookups"].keys() if i.startswith("lookup_vpal")][0]
    vpal = data["GPOS"]["lookups"][vpal_key]
    for t in vpal["subtables"]:
        for glyph, param in t.items():
            if glyph not in data["glyf"]:
                continue
            if glyph in glyphs_to_avoid:
                # skip 々〒、。 shared in both layouts
                continue
            glyph_data = data["glyf"][glyph]
            if "dy" in param:
                glyph_data["contours"] = contour_offset(glyph_data["contours"], 0, param["dy"])
            if "dHeight" in param:
                glyph_data["advanceHeight"] += param["dHeight"]
            data["glyf"][glyph] = glyph_data

    # drop vpal table refs
    for i in data["GPOS"]["languages"].values():
        i["features"] = [j for j in i["features"] if not j.startswith("vpal_")]
    
    features_to_delete = [i for i in data["GPOS"]["features"].keys() if i.startswith("vpal_")]
    for f in features_to_delete:
        del data["GPOS"]["features"][f]

    lookups_to_delete = [i for i in data["GPOS"]["lookups"].keys() if i.startswith("lookup_vpal_")]
    for l in lookups_to_delete:
        del data["GPOS"]["lookups"][l]

    data["GPOS"]["lookupOrder"] = [
        j for j in data["GPOS"]["lookupOrder"] if not j.startswith("lookup_vpal_")]
    
    return data


def change_name(data, use_ui):
    name = "Tsim"
    family_name = f"{name} Sans"
    ui_suffix = " UI" if use_ui else ""
    sub_family_name = family_name + ui_suffix
    sub_family_ID = f"{name}SansUI" if use_ui else f"{name}Sans"
    ja_name = "源幅ゴシック" + ui_suffix
    hans_name = "源幅黑体" + ui_suffix
    hant_name = "源幅黑體" + ui_suffix

    version = 0.001
    for i in data["name"]:
        name_id = (i["languageID"], i["nameID"])
        if name_id == (1033, 0):
            i["nameString"] = f"{family_name} © 2021 Eana Hufwe"
        if name_id in ((1033, 1), (1033, 4), (1033, 16)):
            i["nameString"] = i["nameString"].replace("Source Han Sans", sub_family_name)
        elif name_id in ((2052, 1), (2052, 4), (2052, 16)):
            i["nameString"] = i["nameString"].replace("思源黑体", hans_name)
        elif name_id in ((1041, 1), (1041, 4), (1041, 16)):
            i["nameString"] = i["nameString"].replace("源ノ角ゴシック", ja_name)
        elif name_id in ((1028, 1), (1028, 4), (1028, 16)):
            i["nameString"] = i["nameString"].replace("思源黑體", hant_name)
        elif name_id == (1033, 3):
            i["nameString"] = i["nameString"]\
                .replace("SourceHanSans", sub_family_ID)\
                .replace("ADBO", "1A23")\
                .replace("ADOBE", "EanaHufwe")\
                .replace("2.001", str(version))
        elif name_id == (1033, 5):
            i["nameString"] = f"Version {version}"
        elif name_id == (1033, 6):
            i["nameString"] = i["nameString"].replace("SourceHanSans", sub_family_ID)
        elif name_id == (1033, 8):
            i["nameString"] = "Eana Hufwe"
        elif name_id == (1033, 9):
            i["nameString"] = i["nameString"] + \
                ("; Glow Sans is built by Celestial Phineas" if use_ui else "") + \
                f"; {sub_family_name} is built by Eana Hufwe."
        elif name_id == (1033, 11):
            i["nameString"] = "https://1a23.com"
    data["OS_2"]["achVendID"] = ""
    data["CFF_"]["notice"] = (
        f"{family_name} (c) 2021 Eana Hufwe. " + 
        ("Glow Sans (c) 2020 Project Welai. " if use_ui else "") + 
        "Source Han Sans (c) 2014-2019 Adobe (http://www.adobe.com/)."
    )
    data["CFF_"]["fontName"] = data["CFF_"]["fontName"].replace("SourceHanSans", sub_family_ID)
    data["CFF_"]["fullName"] = data["CFF_"]["fullName"].replace("Source Han Sans", sub_family_name)
    data["CFF_"]["familyName"] = data["CFF_"]["familyName"].replace("Source Han Sans", sub_family_name)
    data["CFF_"]["cidRegistry"] = "Eana Hufwe"
    data["CFF_"]["version"] = str(version)
    data["head"]["fontRevision"] = version

    # fdArray
    nArray = {}
    for k, v in data["CFF_"]["fdArray"].items():
        nArray[k.replace("SourceHanSans", sub_family_ID)] = v
    data["CFF_"]["fdArray"] = nArray
    for v in data["glyf"].values():
        v["CFF_fdSelect"] = v["CFF_fdSelect"].replace(
            "SourceHanSans", sub_family_ID)

    return data


def kern_mapping(lookups):
    result = {}
    for k, v in lookups.items():
        if k.startswith("lookup_kern_"):
            for table in v["subtables"]:
                for a, aid in table["first"].items():
                    for b, bid in table["second"].items():
                        result[a, b] = table["matrix"][aid][bid]
    return result


def flattern_palt(lookups):
    result = {}
    for k, v in lookups.items():
        if k.startswith("lookup_palt_"):
            for table in v["subtables"]:
                result = result | table
    return result


def swap_kana(source, glow):
    kana_glyphs = set(i.split("\t")[0] for i in open("kana.tsv").readlines())
    # glyph definition
    for glyph in kana_glyphs:
        if glyph in source["glyf"] and glyph in glow["glyf"]:
            for param in ("advanceWidth", "advanceHeight", "verticalOrigin", "contours"):
                source["glyf"][glyph][param] = glow["glyf"][glyph][param]

    # GPOS definitions
    glow_kern = kern_mapping(glow["GPOS"]["lookups"])
    glow_palt = flattern_palt(glow["GPOS"]["lookups"])
    for k, v in source["GPOS"]["lookups"].items():
        if k.startswith("lookup_kern_"):
            # kern
            for table in v["subtables"]:
                for a, aid in table["first"].items():
                    for b, bid in table["second"].items():
                        if (a in kana_glyphs or b in kana_glyphs) and ((a, b) in glow_kern):
                            table["matrix"][aid][bid] = glow_kern[a, b]
        elif k.startswith("lookup_palt_"):
            # palt
            for table in v["subtables"]:
                for k in table:
                    if k in kana_glyphs and k in glow_palt:
                        table[k] = glow_palt[k]
    return source
            

def build_font(source_weight, source_fn, glow_weight, glow_fn, is_ui, out_fn):
    print(f"==== building s{source_weight} g{glow_weight} ui{is_ui} ====")
    print("loading json...")
    start = timer()
    with open(source_fn) as f:
        source = json.load(f)
    glow = None
    if is_ui:
        with open(glow_fn) as f:
            glow = json.load(f)
    print("time:", timer() - start)

    print("making changes...")
    start = timer()
    if is_ui:
        source = swap_kana(source, glow)
    palt_changed_glyphs = set()
    source = apply_palt(source, palt_changed_glyphs)
    # source = dup_vpal_glyphs(source)
    source = apply_vpal(source, palt_changed_glyphs)
    source = change_name(source, is_ui)
    print("time:", timer() - start)

    print("exporting json...")
    start = timer()
    with open(out_fn, "w") as f:
        # json.dump(source, f, indent=4)
        json.dump(source, f)
    print("time:", timer() - start)

    print("OK")


def convert_all():
    if not os.path.exists("out"):
        os.mkdir("out")
    for lang in ["J", "SC", "TC"]:
        shs_lang = "" if lang == "J" else lang
        for (shs_w, glow_w) in (
            ("ExtraLight", "ExtraLight"),
            ("Light", "Light"),
            ("Regular", "Book"),
            ("Normal", "Book"),
            ("Medium", "Medium"),
            ("Bold", "Bold"),
            ("Heavy", "ExtraBold"),
        ):
            shs_path = f"fonts/SourceHanSans{lang}/SourceHanSans{shs_lang}-{shs_w}.json"
            glow_path = f"fonts/GlowSans{lang}-Compressed-v0.92/GlowSans{lang}-Compressed-{glow_w}.json"
            build_font(shs_w, shs_path, None, None, False, f"out/TsimSans-{lang}-{shs_w}.json")
            build_font(shs_w, shs_path, glow_w, glow_path, True, f"out/TsimSansUI-{lang}-{shs_w}.json")


if __name__ == "__main__":
    convert_all()
