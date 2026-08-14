"""Procedural 3D Low-Poly Model Generator.

Generates Wavefront .obj models and .mtl material files for Blender,
packages them into downloadable ZIP archives, and converts them to base64 Data URLs.
Includes automated ZIP archive verification to guarantee 100% unzippable models.
"""

import base64
import math
import os
import random
import zipfile
from typing import Dict, List, Tuple


def _hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Converts a hex color string (e.g. '#2e8b57' or '2e8b57') to normalized RGB floats (0.0 - 1.0)."""
    hex_str = hex_color.lstrip("#")
    if len(hex_str) != 6:
        return (0.5, 0.5, 0.5)
    try:
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return (r, g, b)
    except ValueError:
        return (0.5, 0.5, 0.5)


def file_to_data_url(filepath: str, mime_type: str = "application/octet-stream") -> str:
    """Reads a file and converts it into a browser-downloadable Base64 Data URL."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def create_model_zip(output_dir: str, base_name: str) -> str:
    """Bundles .obj and .mtl files into a single downloadable .zip archive.

    Args:
        output_dir: Path to directory containing the model files.
        base_name: Base filename without extension.

    Returns:
        Path to the generated .zip file.
    """
    obj_path = os.path.join(output_dir, f"{base_name}.obj")
    mtl_path = os.path.join(output_dir, f"{base_name}.mtl")
    zip_path = os.path.join(output_dir, f"{base_name}.zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        if os.path.exists(obj_path):
            zipf.write(obj_path, arcname=f"{base_name}.obj")
        if os.path.exists(mtl_path):
            zipf.write(mtl_path, arcname=f"{base_name}.mtl")

    return zip_path


def verify_zip_archive(zip_path: str) -> bool:
    """Verifies that the generated .zip archive exists, is non-empty, and can be unzipped cleanly without corruption."""
    if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
        return False
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            corrupt = zf.testzip()
            if corrupt is not None:
                return False
            names = zf.namelist()
            if not any(n.endswith(".obj") for n in names) or not any(n.endswith(".mtl") for n in names):
                return False
        return True
    except Exception:
        return False


def _compute_face_normal(
    v1: Tuple[float, float, float],
    v2: Tuple[float, float, float],
    v3: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Calculates the normalized surface normal vector for a face triangle."""
    u = (v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2])
    v = (v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2])
    nx = u[1] * v[2] - u[2] * v[1]
    ny = u[2] * v[0] - u[0] * v[2]
    nz = u[0] * v[1] - u[1] * v[0]
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length > 1e-6:
        return (nx / length, ny / length, nz / length)
    return (0.0, 1.0, 0.0)


def _write_obj_and_mtl(
    output_dir: str,
    base_name: str,
    vertices: List[Tuple[float, float, float]],
    faces_by_material: Dict[str, List[List[int]]],
    materials: Dict[str, str],
) -> Tuple[str, str, str, int, int]:
    """Writes vertices, normals, and faces to an .obj file and materials to an .mtl file, and creates a verified .zip bundle."""
    os.makedirs(output_dir, exist_ok=True)
    obj_filename = f"{base_name}.obj"
    mtl_filename = f"{base_name}.mtl"

    obj_path = os.path.join(output_dir, obj_filename)
    mtl_path = os.path.join(output_dir, mtl_filename)

    # 1. Write .mtl file
    with open(mtl_path, "w", encoding="utf-8") as mf:
        mtl_lines = [f"# Material Library for {base_name}\n"]
        for mat_name, hex_color in materials.items():
            r, g, b = _hex_to_rgb(hex_color)
            mtl_lines.append(f"newmtl {mat_name}\n")
            mtl_lines.append("Ka 0.200000 0.200000 0.200000\n")
            mtl_lines.append(f"Kd {r:.6f} {g:.6f} {b:.6f}\n")
            mtl_lines.append("Ks 0.100000 0.100000 0.100000\n")
            mtl_lines.append("Ns 10.000000\n")
            mtl_lines.append("d 1.000000\n")  # Opaque
            mtl_lines.append("illum 2\n\n")
        mf.writelines(mtl_lines)

    # 2. Triangulate faces and compute normals
    triangulated_faces_by_mat = {}
    normals = []
    total_faces = 0

    for mat_name, raw_faces in faces_by_material.items():
        tri_list = []
        for face in raw_faces:
            if len(face) == 3:
                sub_faces = [face]
            else:
                sub_faces = [[face[0], face[i], face[i + 1]] for i in range(1, len(face) - 1)]

            for tf in sub_faces:
                v1 = vertices[tf[0] - 1]
                v2 = vertices[tf[1] - 1]
                v3 = vertices[tf[2] - 1]
                norm = _compute_face_normal(v1, v2, v3)
                normals.append(norm)
                norm_idx = len(normals)
                tri_list.append((tf, norm_idx))
                total_faces += 1

        triangulated_faces_by_mat[mat_name] = tri_list

    # 3. Write .obj file
    with open(obj_path, "w", encoding="utf-8") as of:
        obj_lines = [
            f"# Wavefront .obj file for {base_name}\n",
            f"mtllib {mtl_filename}\n",
            f"o {base_name}\n\n",
        ]

        for v in vertices:
            obj_lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        obj_lines.append("\n")

        for n in normals:
            obj_lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
        obj_lines.append("\n")

        for mat_name, tri_list in triangulated_faces_by_mat.items():
            obj_lines.append(f"usemtl {mat_name}\n")
            obj_lines.append("s off\n")
            for face_verts, n_idx in tri_list:
                f_str = " ".join(f"{v_idx}//{n_idx}" for v_idx in face_verts)
                obj_lines.append(f"f {f_str}\n")
            obj_lines.append("\n")

        of.writelines(obj_lines)

    # 4. Write .zip bundle
    zip_path = create_model_zip(output_dir, base_name)

    # 5. Strict verification check
    if not verify_zip_archive(zip_path):
        raise ValueError(f"Generated ZIP archive '{zip_path}' failed integrity verification!")

    return obj_path, mtl_path, zip_path, len(vertices), total_faces


# =====================================================================
# PROCEDURAL MESH GENERATORS
# =====================================================================


def generate_low_poly_tree(
    output_dir: str = "./models",
    model_name: str = "low_poly_tree",
    foliage_color: str = "#2e8b57",
    trunk_color: str = "#8b4513",
    sides: int = 7,
    foliage_tiers: int = 3,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly tree model."""
    vertices = []
    faces_trunk = []
    faces_foliage = []

    trunk_bottom_r = 0.3
    trunk_top_r = 0.2
    trunk_h = 2.0

    for i in range(sides):
        angle = 2 * math.pi * i / sides
        vertices.append((trunk_bottom_r * math.cos(angle), 0.0, trunk_bottom_r * math.sin(angle)))

    for i in range(sides):
        angle = 2 * math.pi * i / sides
        vertices.append((trunk_top_r * math.cos(angle), trunk_h, trunk_top_r * math.sin(angle)))

    for i in range(sides):
        b1 = i + 1
        b2 = (i + 1) % sides + 1
        t1 = b1 + sides
        t2 = b2 + sides
        faces_trunk.append([b1, b2, t2, t1])

    faces_trunk.append([i + 1 for i in range(sides - 1, -1, -1)])

    base_height = 1.5
    tier_height = 1.6
    base_radius = 1.4

    for t in range(foliage_tiers):
        t_base_y = base_height + t * 1.0
        t_top_y = t_base_y + tier_height
        t_r = base_radius * (1.0 - t * 0.22)

        tier_base_idx = len(vertices) + 1

        for i in range(sides):
            angle = 2 * math.pi * i / sides + (t * 0.2)
            vertices.append((t_r * math.cos(angle), t_base_y, t_r * math.sin(angle)))

        vertices.append((0.0, t_top_y, 0.0))
        tip_idx = len(vertices)

        for i in range(sides):
            b1 = tier_base_idx + i
            b2 = tier_base_idx + (i + 1) % sides
            faces_foliage.append([b1, b2, tip_idx])

        faces_foliage.append([tier_base_idx + i for i in range(sides - 1, -1, -1)])

    materials = {"TrunkMaterial": trunk_color, "FoliageMaterial": foliage_color}
    faces_by_material = {"TrunkMaterial": faces_trunk, "FoliageMaterial": faces_foliage}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_rock(
    output_dir: str = "./models",
    model_name: str = "low_poly_rock",
    rock_color: str = "#708090",
    scale: float = 1.0,
    seed: int = 42,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly boulder/rock."""
    random.seed(seed)
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    raw_verts = [
        (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
        (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1),
        (0, -1/phi, -phi), (0, 1/phi, -phi), (0, -1/phi, phi), (0, 1/phi, phi),
        (-1/phi, -phi, 0), (1/phi, -phi, 0), (-1/phi, phi, 0), (1/phi, phi, 0),
        (-phi, 0, -1/phi), (phi, 0, -1/phi), (-phi, 0, 1/phi), (phi, 0, 1/phi)
    ]

    vertices = []
    for x, y, z in raw_verts:
        length = math.sqrt(x*x + y*y + z*z)
        factor = scale * (0.8 + random.uniform(-0.25, 0.25)) / length
        vertices.append((x * factor, (y * factor) + scale * 0.5, z * factor))

    raw_faces = [
        [1, 9, 10, 4, 17], [2, 18, 3, 10, 9], [18, 2, 6, 20, 17],
        [17, 20, 7, 8, 4], [9, 2, 14, 13, 1], [10, 3, 16, 15, 4],
        [18, 17, 4, 15, 3], [6, 2, 9, 3, 18], [11, 12, 8, 7, 20],
        [11, 12, 16, 15, 5], [13, 14, 6, 5, 12], [10, 9, 14, 13, 15]
    ]

    faces = []
    for f in raw_faces:
        faces.append([f[0], f[1], f[2]])
        faces.append([f[0], f[2], f[3]])
        faces.append([f[0], f[3], f[4]])

    materials = {"RockMaterial": rock_color}
    faces_by_material = {"RockMaterial": faces}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_house(
    output_dir: str = "./models",
    model_name: str = "low_poly_house",
    wall_color: str = "#f5f5dc",
    roof_color: str = "#b22222",
    door_color: str = "#5c4033",
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly house model."""
    w, h, d = 2.0, 1.8, 2.5
    roof_h = 1.0
    overhang = 0.2

    vertices = [
        (-w/2, 0, -d/2), (w/2, 0, -d/2), (w/2, h, -d/2), (-w/2, h, -d/2),
        (-w/2, 0, d/2),  (w/2, 0, d/2),  (w/2, h, d/2),  (-w/2, h, d/2),
        (-w/2 - overhang, h, -d/2 - overhang),
        (w/2 + overhang, h, -d/2 - overhang),
        (w/2 + overhang, h, d/2 + overhang),
        (-w/2 - overhang, h, d/2 + overhang),
        (0, h + roof_h, -d/2 - overhang),
        (0, h + roof_h, d/2 + overhang),
        (-0.3, 0, d/2 + 0.02), (0.3, 0, d/2 + 0.02),
        (0.3, 1.1, d/2 + 0.02), (-0.3, 1.1, d/2 + 0.02)
    ]

    faces_walls = [[1, 2, 3, 4], [6, 5, 8, 7], [5, 1, 4, 8], [2, 6, 7, 3], [1, 5, 6, 2]]
    faces_roof = [[9, 10, 13], [11, 12, 14], [10, 11, 14, 13], [12, 9, 13, 14]]
    faces_door = [[15, 16, 17, 18]]

    materials = {"WallMaterial": wall_color, "RoofMaterial": roof_color, "DoorMaterial": door_color}
    faces_by_material = {"WallMaterial": faces_walls, "RoofMaterial": faces_roof, "DoorMaterial": faces_door}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_crystal(
    output_dir: str = "./models",
    model_name: str = "low_poly_crystal",
    crystal_color: str = "#00ffff",
    sides: int = 6,
    height: float = 2.5,
    radius: float = 0.8,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly crystal/gem pyramid model."""
    vertices = [(0.0, 0.0, 0.0)]
    mid_y = height * 0.4

    for i in range(sides):
        angle = 2 * math.pi * i / sides
        vertices.append((radius * math.cos(angle), mid_y, radius * math.sin(angle)))

    vertices.append((0.0, height, 0.0))
    top_idx = sides + 2

    faces = []
    for i in range(sides):
        b1 = 2 + i
        b2 = 2 + (i + 1) % sides
        faces.append([1, b2, b1])

    for i in range(sides):
        b1 = 2 + i
        b2 = 2 + (i + 1) % sides
        faces.append([b1, b2, top_idx])

    materials = {"CrystalMaterial": crystal_color}
    faces_by_material = {"CrystalMaterial": faces}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_mushroom(
    output_dir: str = "./models",
    model_name: str = "low_poly_mushroom",
    cap_color: str = "#9d50bb",
    stem_color: str = "#f7f1e3",
    sides: int = 8,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly glowing mushroom model."""
    vertices = []
    faces_stem = []
    faces_cap = []

    # Stem cylinder
    stem_r = 0.25
    stem_h = 1.2
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((stem_r * math.cos(a), 0.0, stem_r * math.sin(a)))
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((stem_r * 0.8 * math.cos(a), stem_h, stem_r * 0.8 * math.sin(a)))

    for i in range(sides):
        b1 = i + 1
        b2 = (i + 1) % sides + 1
        t1 = b1 + sides
        t2 = b2 + sides
        faces_stem.append([b1, b2, t2, t1])

    # Cap wide dome/cone
    cap_r = 1.2
    cap_base_y = stem_h * 0.8
    cap_apex_y = stem_h + 0.8

    cap_base_idx = len(vertices) + 1
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((cap_r * math.cos(a), cap_base_y, cap_r * math.sin(a)))

    vertices.append((0.0, cap_apex_y, 0.0))
    apex_idx = len(vertices)

    for i in range(sides):
        b1 = cap_base_idx + i
        b2 = cap_base_idx + (i + 1) % sides
        faces_cap.append([b1, b2, apex_idx])

    # Cap underside cap
    faces_cap.append([cap_base_idx + i for i in range(sides - 1, -1, -1)])

    materials = {"StemMaterial": stem_color, "CapMaterial": cap_color}
    faces_by_material = {"StemMaterial": faces_stem, "CapMaterial": faces_cap}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_obelisk(
    output_dir: str = "./models",
    model_name: str = "low_poly_obelisk",
    stone_color: str = "#263238",
    rune_color: str = "#00e5ff",
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly ancient runestone obelisk model."""
    vertices = [
        # Base pedestal (1..8)
        (-0.7, 0.0, -0.7), (0.7, 0.0, -0.7), (0.7, 0.0, 0.7), (-0.7, 0.0, 0.7),
        (-0.5, 0.4, -0.5), (0.5, 0.4, -0.5), (0.5, 0.4, 0.5), (-0.5, 0.4, 0.5),
        # Mid pillar (9..12)
        (-0.4, 2.2, -0.4), (0.4, 2.2, -0.4), (0.4, 2.2, 0.4), (-0.4, 2.2, 0.4),
        # Pyramid Tip Apex (13)
        (0.0, 2.8, 0.0),
        # Rune band ring (14..17)
        (-0.42, 1.2, -0.42), (0.42, 1.2, -0.42), (0.42, 1.2, 0.42), (-0.42, 1.2, 0.42),
        (-0.42, 1.4, -0.42), (0.42, 1.4, -0.42), (0.42, 1.4, 0.42), (-0.42, 1.4, 0.42)
    ]

    faces_stone = [
        [1, 2, 6, 5], [2, 3, 7, 6], [3, 4, 8, 7], [4, 1, 5, 8],
        [5, 6, 15, 14], [6, 7, 16, 15], [7, 8, 17, 16], [8, 5, 14, 17],
        [18, 19, 10, 9], [19, 20, 11, 10], [20, 21, 12, 11], [21, 18, 9, 12],
        [9, 10, 13], [10, 11, 13], [11, 12, 13], [12, 9, 13]
    ]

    faces_rune = [
        [14, 15, 19, 18], [15, 16, 20, 19], [16, 17, 21, 20], [17, 14, 18, 21]
    ]

    materials = {"StoneMaterial": stone_color, "RuneMaterial": rune_color}
    faces_by_material = {"StoneMaterial": faces_stone, "RuneMaterial": faces_rune}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_potion(
    output_dir: str = "./models",
    model_name: str = "low_poly_potion",
    liquid_color: str = "#ff1744",
    cork_color: str = "#a1887f",
    sides: int = 8,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly magic potion flask model."""
    vertices = []
    faces_liquid = []
    faces_cork = []

    body_r = 0.7
    neck_r = 0.25
    body_h = 0.9
    neck_h = 0.5
    cork_h = 0.25

    # Flask Base Body (1..sides)
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((body_r * math.cos(a), 0.2, body_r * math.sin(a)))

    # Flask Neck Base (sides+1..2*sides)
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((neck_r * math.cos(a), body_h, neck_r * math.sin(a)))

    # Flask Neck Top (2*sides+1..3*sides)
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((neck_r * math.cos(a), body_h + neck_h, neck_r * math.sin(a)))

    for i in range(sides):
        b1 = i + 1
        b2 = (i + 1) % sides + 1
        t1 = b1 + sides
        t2 = b2 + sides
        faces_liquid.append([b1, b2, t2, t1])

    for i in range(sides):
        b1 = sides + i + 1
        b2 = sides + (i + 1) % sides + 1
        t1 = b1 + sides
        t2 = b2 + sides
        faces_liquid.append([b1, b2, t2, t1])

    # Cork Stopper Top
    cork_base = len(vertices) + 1
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((neck_r * 1.1 * math.cos(a), body_h + neck_h, neck_r * 1.1 * math.sin(a)))
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((neck_r * 1.1 * math.cos(a), body_h + neck_h + cork_h, neck_r * 1.1 * math.sin(a)))

    for i in range(sides):
        b1 = cork_base + i
        b2 = cork_base + (i + 1) % sides
        t1 = b1 + sides
        t2 = b2 + sides
        faces_cork.append([b1, b2, t2, t1])

    faces_cork.append([cork_base + sides + i for i in range(sides - 1, -1, -1)])

    materials = {"LiquidMaterial": liquid_color, "CorkMaterial": cork_color}
    faces_by_material = {"LiquidMaterial": faces_liquid, "CorkMaterial": faces_cork}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_chest(
    output_dir: str = "./models",
    model_name: str = "low_poly_chest",
    wood_color: str = "#4a2c2a",
    gold_color: str = "#ffd700",
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly treasure chest model."""
    w, h, d = 1.4, 0.8, 1.0

    vertices = [
        # Box Base (1..8)
        (-w/2, 0.0, -d/2), (w/2, 0.0, -d/2), (w/2, h, -d/2), (-w/2, h, -d/2),
        (-w/2, 0.0, d/2),  (w/2, 0.0, d/2),  (w/2, h, d/2),  (-w/2, h, d/2),
        # Arched Lid Ridge (9..10)
        (0.0, h + 0.4, -d/2), (0.0, h + 0.4, d/2),
        # Gold Lock Plate (11..14)
        (-0.15, h - 0.2, d/2 + 0.02), (0.15, h - 0.2, d/2 + 0.02),
        (0.15, h + 0.1, d/2 + 0.02), (-0.15, h + 0.1, d/2 + 0.02)
    ]

    faces_wood = [
        [1, 2, 3, 4], [6, 5, 8, 7], [5, 1, 4, 8], [2, 6, 7, 3], [1, 5, 6, 2],
        [4, 3, 9], [7, 8, 10], [3, 7, 10, 9], [8, 4, 9, 10]
    ]

    faces_gold = [
        [11, 12, 13, 14]
    ]

    materials = {"WoodMaterial": wood_color, "GoldMaterial": gold_color}
    faces_by_material = {"WoodMaterial": faces_wood, "GoldMaterial": faces_gold}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_sword_in_stone(
    output_dir: str = "./models",
    model_name: str = "low_poly_sword_in_stone",
    stone_color: str = "#546e7a",
    blade_color: str = "#cfd8dc",
    gold_color: str = "#ffc107",
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly sword stuck in stone model."""
    # Stone Base
    stone_gen = generate_low_poly_rock(output_dir=output_dir, model_name="temp_stone", rock_color=stone_color)

    vertices = [
        # Stone center apex top at y=0.8
        # Blade (1..8)
        (0.0, 0.6, -0.15), (0.08, 0.6, 0.0), (0.0, 0.6, 0.15), (-0.08, 0.6, 0.0),
        (0.0, 2.2, -0.10), (0.06, 2.2, 0.0), (0.0, 2.2, 0.10), (-0.06, 2.2, 0.0),
        # Crossguard (9..16)
        (-0.4, 2.2, -0.08), (0.4, 2.2, -0.08), (0.4, 2.2, 0.08), (-0.4, 2.2, 0.08),
        (-0.4, 2.3, -0.08), (0.4, 2.3, -0.08), (0.4, 2.3, 0.08), (-0.4, 2.3, 0.08),
        # Hilt Top Pommel (17)
        (0.0, 2.8, 0.0)
    ]

    faces_blade = [
        [1, 2, 6, 5], [2, 3, 7, 6], [3, 4, 8, 7], [4, 1, 5, 8]
    ]

    faces_guard = [
        [9, 10, 14, 13], [10, 11, 15, 14], [11, 12, 16, 15], [12, 9, 13, 16],
        [13, 14, 17], [14, 15, 17], [15, 16, 17], [16, 13, 17]
    ]

    materials = {"BladeMaterial": blade_color, "GuardMaterial": gold_color, "StoneMaterial": stone_color}
    faces_by_material = {"BladeMaterial": faces_blade, "GuardMaterial": faces_guard}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_windmill(
    output_dir: str = "./models",
    model_name: str = "low_poly_windmill",
    tower_color: str = "#d35400",
    roof_color: str = "#f1c40f",
    blade_color: str = "#5d4037",
    sides: int = 8,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly windmill model."""
    vertices = []
    faces_tower = []
    faces_roof = []
    faces_blades = []

    # Tower (Truncated octagonal pyramid)
    b_r, t_r, h = 1.2, 0.8, 2.8
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((b_r * math.cos(a), 0.0, b_r * math.sin(a)))
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((t_r * math.cos(a), h, t_r * math.sin(a)))

    for i in range(sides):
        b1 = i + 1
        b2 = (i + 1) % sides + 1
        t1 = b1 + sides
        t2 = b2 + sides
        faces_tower.append([b1, b2, t2, t1])

    # Conical Roof
    roof_apex_y = h + 1.2
    vertices.append((0.0, roof_apex_y, 0.0))
    apex_idx = len(vertices)

    for i in range(sides):
        t1 = sides + i + 1
        t2 = sides + (i + 1) % sides + 1
        faces_roof.append([t1, t2, apex_idx])

    # 4 Blades attached to front (z = t_r)
    blade_hub_idx = len(vertices) + 1
    hub_y = h * 0.8
    hub_z = t_r + 0.1
    vertices.append((0.0, hub_y, hub_z))

    blade_len = 1.4
    vertices.extend([
        (-blade_len, hub_y - 0.1, hub_z), (-blade_len, hub_y + 0.1, hub_z),
        (blade_len, hub_y - 0.1, hub_z),  (blade_len, hub_y + 0.1, hub_z),
        (0.1, hub_y - blade_len, hub_z),  (-0.1, hub_y - blade_len, hub_z),
        (0.1, hub_y + blade_len, hub_z),  (-0.1, hub_y + blade_len, hub_z),
    ])

    faces_blades = [
        [blade_hub_idx + 1, blade_hub_idx + 2, blade_hub_idx],
        [blade_hub_idx + 3, blade_hub_idx + 4, blade_hub_idx],
        [blade_hub_idx + 5, blade_hub_idx + 6, blade_hub_idx],
        [blade_hub_idx + 7, blade_hub_idx + 8, blade_hub_idx],
    ]

    materials = {"TowerMaterial": tower_color, "RoofMaterial": roof_color, "BladeMaterial": blade_color}
    faces_by_material = {"TowerMaterial": faces_tower, "RoofMaterial": faces_roof, "BladeMaterial": faces_blades}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_campfire(
    output_dir: str = "./models",
    model_name: str = "low_poly_campfire",
    pot_color: str = "#37474f",
    fire_color: str = "#ff3d00",
    wood_color: str = "#6d4c41",
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly campfire with cooking pot model."""
    vertices = [
        # Tripod Logs (1..6)
        (-0.8, 0.0, -0.5), (0.0, 1.6, 0.0),
        (0.8, 0.0, -0.5),  (0.0, 1.6, 0.0),
        (0.0, 0.0, 0.8),   (0.0, 1.6, 0.0),
        # Cooking Pot (7..10)
        (-0.4, 0.8, -0.4), (0.4, 0.8, -0.4), (0.4, 0.8, 0.4), (-0.4, 0.8, 0.4),
        # Flame Pyramids (11..13)
        (-0.2, 0.0, -0.2), (0.2, 0.0, -0.2), (0.0, 0.6, 0.0)
    ]

    faces_wood = [[1, 2], [3, 4], [5, 6]]
    faces_pot = [[7, 8, 9, 10]]
    faces_fire = [[11, 12, 13]]

    materials = {"WoodMaterial": wood_color, "PotMaterial": pot_color, "FireMaterial": fire_color}
    faces_by_material = {"WoodMaterial": faces_wood, "PotMaterial": faces_pot, "FireMaterial": faces_fire}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_iceberg(
    output_dir: str = "./models",
    model_name: str = "low_poly_iceberg",
    glacier_color: str = "#a8edea",
    deep_color: str = "#2193b0",
    sides: int = 7,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly iceberg glacier model."""
    vertices = [(0.0, -1.2, 0.0)]  # Submerged apex bottom

    # Waterline middle ring
    mid_r = 1.6
    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((mid_r * math.cos(a), 0.0, mid_r * math.sin(a)))

    vertices.append((0.0, 1.5, 0.0))  # Top apex
    top_idx = sides + 2

    faces_deep = []
    for i in range(sides):
        b1 = 2 + i
        b2 = 2 + (i + 1) % sides
        faces_deep.append([1, b2, b1])

    faces_glacier = []
    for i in range(sides):
        b1 = 2 + i
        b2 = 2 + (i + 1) % sides
        faces_glacier.append([b1, b2, top_idx])

    materials = {"GlacierMaterial": glacier_color, "DeepIceMaterial": deep_color}
    faces_by_material = {"GlacierMaterial": faces_glacier, "DeepIceMaterial": faces_deep}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_hover_pod(
    output_dir: str = "./models",
    model_name: str = "low_poly_hover_pod",
    chassis_color: str = "#1a1a2e",
    canopy_color: str = "#00f5d4",
    thruster_color: str = "#ff007f",
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly sci-fi hover pod model."""
    vertices = [
        # Nose Tip (1)
        (0.0, 0.3, 1.8),
        # Flared Side Pods (2..5)
        (-0.9, 0.2, -0.5), (0.9, 0.2, -0.5), (0.9, 0.5, -0.5), (-0.9, 0.5, -0.5),
        # Canopy Glass (6..9)
        (-0.4, 0.5, 0.2), (0.4, 0.5, 0.2), (0.3, 0.8, -0.3), (-0.3, 0.8, -0.3),
        # Thruster Nozzles (10..13)
        (-0.5, 0.3, -1.0), (0.5, 0.3, -1.0), (0.5, 0.5, -1.0), (-0.5, 0.5, -1.0)
    ]

    faces_chassis = [[1, 2, 5], [1, 3, 4], [2, 3, 4, 5]]
    faces_canopy = [[6, 7, 8, 9]]
    faces_thruster = [[10, 11, 12, 13]]

    materials = {"ChassisMaterial": chassis_color, "CanopyMaterial": canopy_color, "ThrusterMaterial": thruster_color}
    faces_by_material = {"ChassisMaterial": faces_chassis, "CanopyMaterial": faces_canopy, "ThrusterMaterial": faces_thruster}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_balloon(
    output_dir: str = "./models",
    model_name: str = "low_poly_balloon",
    balloon_color: str = "#ff1744",
    basket_color: str = "#6d4c41",
    sides: int = 8,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly hot air balloon model."""
    vertices = []
    faces_balloon = []
    faces_basket = []

    # Teardrop Balloon Sphere
    b_r = 1.6
    b_h = 2.4
    vertices.append((0.0, b_h + 1.2, 0.0))  # Top cap (1)

    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((b_r * math.cos(a), b_h, b_r * math.sin(a)))  # Upper ring (2..sides+1)

    for i in range(sides):
        a = 2 * math.pi * i / sides
        vertices.append((b_r * 0.5 * math.cos(a), b_h * 0.4, b_r * 0.5 * math.sin(a)))  # Lower neck ring

    for i in range(sides):
        b1 = 2 + i
        b2 = 2 + (i + 1) % sides
        faces_balloon.append([1, b1, b2])

    # Basket Box
    basket_base = len(vertices) + 1
    w = 0.5
    vertices.extend([
        (-w, -0.8, -w), (w, -0.8, -w), (w, -0.2, -w), (-w, -0.2, -w),
        (-w, -0.8, w),  (w, -0.8, w),  (w, -0.2, w),  (-w, -0.2, w),
    ])

    faces_basket = [
        [basket_base, basket_base+1, basket_base+2, basket_base+3],
        [basket_base+5, basket_base+4, basket_base+7, basket_base+6]
    ]

    materials = {"BalloonMaterial": balloon_color, "BasketMaterial": basket_color}
    faces_by_material = {"BalloonMaterial": faces_balloon, "BasketMaterial": faces_basket}

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)
