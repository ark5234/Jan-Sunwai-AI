import re

filepath = r'c:\Users\Vikra\OneDrive\Desktop\Jan-Sunwai AI\backend\app\rule_engine.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_rules = '''_CATEGORY_RULES: dict[str, list[tuple[list[str], float]]] = {
    "Health Department": [
        (["garbage", "trash", "rubbish", "refuse", "plastic waste", "plastic bags", "debris", "sweeping"], 3.0),
        (["waste pile", "waste dump", "waste heap", "open dump", "illegal dump"], 3.0),
        (["overflowing bin", "overflowing trash", "overflowing garbage", "spilled garbage"], 3.0),
        (["litter", "littered", "littering", "scattered waste"], 2.5),
        (["filthy toilet", "unclean toilet", "public urination", "open defecation", "spitting"], 2.5),
        (["stench", "foul smell", "unhygienic", "rotten"], 1.5),
        (["dead animal", "carcass", "dead dog"], 3.0),
        (["medical waste", "hospital waste", "bio hazard"], 3.0),
        (["pollution", "chemical dump", "toxic waste"], 2.5),
    ],
    "Civil Department": [
        (["pothole", "potholes", "pothole-filled", "crater", "visible potholes"], 3.0),
        (["road damage", "damaged road", "broken road", "cracked road", "uneven road", "dirt road", "peeling asphalt", "bad road condition", "rubble"], 3.0),
        (["damaged pavement", "broken pavement", "cracked pavement", "pavement damage", "road surface", "uneven surface", "road with fallen leaves"], 2.5),
        (["footpath damage", "broken footpath", "damaged footpath"], 2.5),
        (["waterlogging", "waterlogged", "water logging", "puddles", "stagnant water on road"], 3.0),
        (["flooded", "flooding", "flood"], 3.0),
        (["drain overflow", "overflowing drain", "blocked drain", "dirty drain"], 3.0),
        (["sewer overflow", "sewer leak", "sewage"], 3.0),
        (["pipe leak", "water leak", "leaking pipe", "burst pipe"], 2.5),
        (["manhole", "manhole cover", "missing cover", "caved in", "sinkhole"], 2.0),
        (["bridge damage", "damaged bridge", "crack in bridge"], 2.0),
    ],
    "Horticulture": [
        (["fallen tree", "uprooted tree", "collapsed tree", "uprooted"], 3.0),
        (["overgrown", "unmaintained park", "neglected park", "overgrown weeds"], 2.5),
        (["dead plant", "dead plants", "dry plants", "withered", "fallen leaves", "dry leaves", "leaves scattered"], 2.5),
        (["broken branch", "tree branch", "branches blocking"], 2.0),
        (["tree blocking road", "tree fell", "tree on road"], 3.0),
        (["garden", "park", "greenery", "vegetation", "weed"], 0.5),
    ],
    "Electrical Department": [
        (["street light", "streetlight", "street lamp", "lamp post", "lamppost"], 3.0),
        (["broken light", "non-functional light", "damaged light"], 2.5),
        (["unlit road", "dark road", "dark street", "no lighting"], 2.5),
        (["dangling wire", "hanging wire", "loose wire", "fallen wire", "electrical wire"], 3.0),
        (["open transformer", "damaged transformer", "leaking transformer", "electrical box", "fuse box", "circuit breaker", "meter box", "distribution panel"], 3.0),
        (["fallen electric pole", "tilted pole", "broken pole"], 3.0),
        (["exposed wire", "bare wire", "naked cable", "sparking", "live wire", "high voltage", "electrocut"], 2.5),
        (["transformer", "electric pole", "utility pole", "electrical panel"], 1.5),
    ],
    "IT Department": [
        (["app bug", "portal bug", "website down", "app down"], 3.0),
        (["login issue", "server error", "database error", "portal crash", "login failed"], 3.0),
    ],
    "Commercial": [
        (["faulty meter", "broken meter", "meter reading"], 3.0),
        (["billing issue", "wrong bill", "excessive bill", "property tax", "license renewal"], 3.0),
    ],
    "Enforcement": [
        (["illegal parking", "wrong parking", "no parking zone"], 3.0),
        (["encroachment", "footpath encroachment", "pavement encroachment", "commercial encroachment"], 3.0),
        (["illegal occupation", "hawker", "unauthorized vendor", "squatter"], 2.5),
        (["traffic deadlock", "deadlock", "standstill"], 3.5),
        (["traffic jam", "gridlock", "chaotic traffic", "severe accident"], 3.0),
        (["road blockage", "road blocked", "road obstruction"], 2.5),
        (["lane violation", "wrong side driving"], 2.5),
        (["unauthorized", "public nuisance", "illegal hoarding"], 2.0),
    ],
    "VBD Department": [
        (["mosquitoes", "mosquito breeding", "mosquito larvae", "larvae"], 3.0),
        (["stagnant water", "standing water", "water pooling"], 2.5),
        (["dengue", "malaria", "fogging required", "fumigation", "mosquito net"], 3.0),
    ],
    "EBR Department": [
        (["illegal construction", "unauthorized construction", "building violation"], 3.0),
        (["building collapse", "unsafe building", "dangerous structure"], 3.0),
    ],
    "Fire Department": [
        (["fire", "burning", "flames", "smoke emission", "thick smoke", "smoke billow"], 3.0),
        (["fire hazard", "flammable", "explosive", "gas leak"], 3.0),
    ]
}'''

new_content = re.sub(r'_CATEGORY_RULES.*?_NON_CIVIC_KEYWORDS = \[', new_rules + '\n\n# Negative signals: if these appear, suppress civic categories\n_NON_CIVIC_KEYWORDS = [', content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(new_content)
