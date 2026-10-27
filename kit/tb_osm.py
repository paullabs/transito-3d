"""Trânsito Brasil 3D: converte um recorte do OpenStreetMap (.osm em XML, da API 0.6) num JSON limpo em metros.
x = leste, y = norte, origem no centro do recorte. Roda fora do Blender:
    python3 -I kit3d/tb_osm.py transito/dados_osm/estaiada.osm transito/dados_osm/estaiada.json
Classes que saem: vias (com tipo, faixas, mão única, ponte, nome), prédios (altura), água, verde, trilhos."""
import json, math, sys
import xml.etree.ElementTree as ET

VIAS = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
        "tertiary", "tertiary_link", "residential", "service", "living_street", "unclassified", "busway", "cycleway"}
VERDE_LEISURE = {"park", "garden", "pitch", "village_green", "sports_centre"}
VERDE_LANDUSE = {"grass", "village_green", "greenfield", "forest", "meadow", "recreation_ground"}


def converte(src, dst):
    raiz = ET.parse(src).getroot()
    b = raiz.find("bounds")
    lat0 = (float(b.get("minlat")) + float(b.get("maxlat"))) / 2
    lon0 = (float(b.get("minlon")) + float(b.get("maxlon"))) / 2
    kx = 111320.0 * math.cos(math.radians(lat0)); ky = 110540.0
    nos = {n.get("id"): ((float(n.get("lon")) - lon0) * kx, (float(n.get("lat")) - lat0) * ky) for n in raiz.iter("node")}
    vias_por_id = {}
    out = {"centro": [lat0, lon0], "limites": [(float(b.get("minlon")) - lon0) * kx, (float(b.get("minlat")) - lat0) * ky,
                                                (float(b.get("maxlon")) - lon0) * kx, (float(b.get("maxlat")) - lat0) * ky],
           "vias": [], "predios": [], "agua": [], "rio": [], "verde": [], "trilhos": []}
    for w in raiz.iter("way"):
        t = {x.get("k"): x.get("v") for x in w.iter("tag")}
        pts = [nos[nd.get("ref")] for nd in w.iter("nd") if nd.get("ref") in nos]
        pts = [(round(x, 2), round(y, 2)) for x, y in pts]
        vias_por_id[w.get("id")] = pts
        if len(pts) < 2:
            continue
        hw = t.get("highway")
        if hw in VIAS:
            try:
                faixas = int(t.get("lanes", "0").split(";")[0])
            except ValueError:
                faixas = 0
            out["vias"].append({"id": w.get("id"), "tipo": hw, "nome": t.get("name", ""), "faixas": faixas,
                                "mao_unica": t.get("oneway") in ("yes", "1") or t.get("junction") == "roundabout" or hw.startswith("motorway"),
                                "ponte": t.get("bridge") in ("yes", "viaduct"), "estaiada": t.get("bridge:structure") == "cable-stayed",
                                "velmax": t.get("maxspeed", ""), "nivel": int(t.get("layer", "0") or 0) if t.get("layer", "0").lstrip("-").isdigit() else 0,
                                "pts": pts})
        elif "building" in t and len(pts) >= 4:
            alt = None
            if t.get("height"):
                try: alt = float(t["height"].replace("m", "").strip())
                except ValueError: pass
            if alt is None and t.get("building:levels"):
                try: alt = float(t["building:levels"]) * 3.1
                except ValueError: pass
            out["predios"].append({"alt": alt, "tipo": t["building"], "pts": pts[:-1] if pts[0] == pts[-1] else pts})
        elif t.get("natural") == "water" or t.get("waterway") == "riverbank":
            out["agua"].append(pts)
        elif t.get("waterway") in ("river", "canal"):
            out["rio"].append({"nome": t.get("name", ""), "pts": pts})
        elif t.get("leisure") in VERDE_LEISURE or t.get("landuse") in VERDE_LANDUSE or t.get("natural") in ("wood", "scrub"):
            out["verde"].append({"tipo": t.get("leisure") or t.get("landuse") or t.get("natural"), "pts": pts})
        elif t.get("railway") in ("rail", "monorail", "subway"):
            out["trilhos"].append({"tipo": t["railway"], "nome": t.get("name", ""), "ponte": t.get("bridge") in ("yes", "viaduct"), "pts": pts})
    # rios e lagos em relação (multipolígono): só os anéis externos que vieram no recorte
    for r in raiz.iter("relation"):
        t = {x.get("k"): x.get("v") for x in r.iter("tag")}
        if t.get("natural") == "water" or t.get("waterway") == "riverbank":
            for m in r.iter("member"):
                if m.get("type") == "way" and m.get("role") == "outer" and len(vias_por_id.get(m.get("ref"), [])) > 2:
                    out["agua"].append(vias_por_id[m.get("ref")])
    json.dump(out, open(dst, "w"), ensure_ascii=False)
    print(f"vias {len(out['vias'])}, prédios {len(out['predios'])}, água {len(out['agua'])}, rio {len(out['rio'])}, verde {len(out['verde'])}, trilhos {len(out['trilhos'])}")
    print("limites (m):", [round(v) for v in out["limites"]])


if __name__ == "__main__":
    converte(sys.argv[1], sys.argv[2])
