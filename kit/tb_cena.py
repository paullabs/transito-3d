"""Trânsito Brasil 3D: cena, luz, câmera e render (EEVEE por padrão, Cycles opcional)."""
import math
import bpy
from mathutils import Vector
from tb_assets import hexrgb


def limpa():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def motor(eevee=True, amostras=32, w=1080, h=1920, escala=1.0):
    sc = bpy.context.scene
    if eevee:
        for nome in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
            try:
                sc.render.engine = nome; break
            except TypeError:
                continue
        ee = sc.eevee
        ee.taa_render_samples = amostras
        for k, v in (("use_shadows", True), ("use_raytracing", True), ("shadow_ray_count", 2), ("shadow_step_count", 8),
                     ("use_gtao", True), ("gtao_distance", 2.0), ("fast_gi_distance", 6.0)):
            try:
                setattr(ee, k, v)
            except Exception:
                pass
    else:
        sc.render.engine = "CYCLES"; sc.cycles.samples = amostras; sc.cycles.use_denoising = True
        try:
            bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "METAL"; sc.cycles.device = "GPU"
        except Exception:
            pass
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = int(escala * 100)
    sc.render.fps = 24
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    sc.render.film_transparent = False
    return sc


def mundo(cor="#dfe6ee", forca=1.0, ceu=False):
    w = bpy.data.worlds.new("mundo"); bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    if ceu:
        sk = w.node_tree.nodes.new("ShaderNodeTexSky")
        try:
            sk.sky_type = "NISHITA"
        except TypeError:
            pass
        w.node_tree.links.new(sk.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = forca
    else:
        bg.inputs[0].default_value = hexrgb(cor); bg.inputs[1].default_value = forca
    return w


def sol(elev=52, azim=-35, forca=4.0, cor="#fff4e2", angulo=2.5):
    d = bpy.data.lights.new("sol", "SUN"); d.energy = forca; d.color = hexrgb(cor)[:3]; d.angle = math.radians(angulo)
    o = bpy.data.objects.new("sol", d); bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim))
    return o


def camera(alvo, dist, elev=55, azim=-30, lente=50, nome="cam", sensor=36):
    """clip_start proporcional à distância: é isso que dá a precisão de profundidade para as camadas finas do mapa não piscarem"""
    """câmera que olha para o alvo de uma distância; elev = graus acima do horizonte; azim = de onde olha (0 = do sul)"""
    c = bpy.data.cameras.new(nome); c.lens = lente; c.sensor_width = sensor; c.clip_end = max(dist * 8, 200); c.clip_start = max(0.5, dist * 0.15)
    o = bpy.data.objects.new(nome, c); bpy.context.scene.collection.objects.link(o)
    poe_camera(o, alvo, dist, elev, azim)
    bpy.context.scene.camera = o
    return o


def poe_camera(o, alvo, dist, elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    alvo = Vector(alvo)
    o.location = alvo + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    o.rotation_euler = (alvo - o.location).to_track_quat("-Z", "Y").to_euler()


def largura_vista(dist, lente, sensor=36, w=1080, h=1920):
    """largura (m) que a câmera vê no alvo; no quadro vertical o sensor vale para a altura"""
    lado = dist * sensor / lente
    return lado * (w / h) if h > w else lado


def render(caminho):
    sc = bpy.context.scene; sc.render.filepath = caminho
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
