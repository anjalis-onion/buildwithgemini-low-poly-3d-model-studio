"""Procedural 3D Low-Poly Model Generator.

Generates Wavefront .obj models and .mtl material files for Blender,
packages them into downloadable ZIP archives, and converts them to base64 Data URLs.
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
    r = int(hex_str[0:2], 16) / 255.0
    g = int(hex_str[2:4], 16) / 255.0
    b = int(hex_str[4:6], 16) / 255.0
    return (r, g, b)


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
    """Writes vertices, normals, and faces to an .obj file and materials to an .mtl file, and creates a .zip bundle.

    Args:
        output_dir: Output directory path.
        base_name: Filename without extension.
        vertices: List of (x, y, z) 3D coordinate tuples.
        faces_by_material: Dictionary mapping material_name to list of face vertex indices (1-indexed).
        materials: Dictionary mapping material_name to hex color string.

    Returns:
        Tuple of (obj_filepath, mtl_filepath, zip_filepath, vertex_count, face_count)
    """
    os.makedirs(output_dir, exist_ok=True)
    obj_filename = f"{base_name}.obj"
    mtl_filename = f"{base_name}.mtl"

    obj_path = os.path.join(output_dir, obj_filename)
    mtl_path = os.path.join(output_dir, mtl_filename)

    # 1. Write .mtl file with explicit d 1.0 (opacity) for Blender
    with open(mtl_path, "w", encoding="utf-8") as mf:
        mtl_lines = [f"# Material Library for {base_name}\n"]
        for mat_name, hex_color in materials.items():
            r, g, b = _hex_to_rgb(hex_color)
            mtl_lines.append(f"newmtl {mat_name}\n")
            mtl_lines.append("Ka 0.200000 0.200000 0.200000\n")
            mtl_lines.append(f"Kd {r:.6f} {g:.6f} {b:.6f}\n")
            mtl_lines.append("Ks 0.100000 0.100000 0.100000\n")
            mtl_lines.append("Ns 10.000000\n")
            mtl_lines.append("d 1.000000\n")  # Fully Opaque (Alpha = 1.0)
            mtl_lines.append("illum 2\n\n")
        mf.writelines(mtl_lines)

    # 2. Pre-triangulate all faces and compute normals
    triangulated_faces_by_mat = {}
    normals = []
    total_faces = 0

    for mat_name, raw_faces in faces_by_material.items():
        tri_list = []
        for face in raw_faces:
            # Fan-triangulate any polygon with > 3 vertices
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

        # Write Vertices (x, y, z)
        for v in vertices:
            obj_lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        obj_lines.append("\n")

        # Write Vertex Normals (vn x y z)
        for n in normals:
            obj_lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
        obj_lines.append("\n")

        # Write Faces with Normal Indices (f v1//vn1 v2//vn2 v3//vn3)
        for mat_name, tri_list in triangulated_faces_by_mat.items():
            obj_lines.append(f"usemtl {mat_name}\n")
            obj_lines.append("s off\n")  # Flat shading
            for face_verts, n_idx in tri_list:
                f_str = " ".join(f"{v_idx}//{n_idx}" for v_idx in face_verts)
                obj_lines.append(f"f {f_str}\n")
            obj_lines.append("\n")

        of.writelines(obj_lines)

    # 4. Write .zip bundle
    zip_path = create_model_zip(output_dir, base_name)

    return obj_path, mtl_path, zip_path, len(vertices), total_faces


def generate_low_poly_tree(
    output_dir: str = "./models",
    model_name: str = "low_poly_tree",
    foliage_color: str = "#2e8b57",
    trunk_color: str = "#8b4513",
    sides: int = 7,
    foliage_tiers: int = 3,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly tree .obj, .mtl, and .zip model."""
    vertices = []
    faces_trunk = []
    faces_foliage = []

    # 1. Build Trunk (Prism cylinder)
    trunk_bottom_r = 0.3
    trunk_top_r = 0.2
    trunk_h = 2.0

    # Trunk bottom vertices (1..sides)
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        vertices.append((trunk_bottom_r * math.cos(angle), 0.0, trunk_bottom_r * math.sin(angle)))

    # Trunk top vertices (sides+1..2*sides)
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        vertices.append((trunk_top_r * math.cos(angle), trunk_h, trunk_top_r * math.sin(angle)))

    # Trunk side faces
    for i in range(sides):
        b1 = i + 1
        b2 = (i + 1) % sides + 1
        t1 = b1 + sides
        t2 = b2 + sides
        faces_trunk.append([b1, b2, t2, t1])

    # Trunk bottom cap
    faces_trunk.append([i + 1 for i in range(sides - 1, -1, -1)])

    # 2. Build Foliage Tiers (Cone pyramids)
    base_height = 1.5
    tier_height = 1.6
    base_radius = 1.4

    for t in range(foliage_tiers):
        t_base_y = base_height + t * 1.0
        t_top_y = t_base_y + tier_height
        t_r = base_radius * (1.0 - t * 0.22)

        tier_base_idx = len(vertices) + 1

        # Foliage tier base vertices
        for i in range(sides):
            angle = 2 * math.pi * i / sides + (t * 0.2)
            vertices.append((t_r * math.cos(angle), t_base_y, t_r * math.sin(angle)))

        # Foliage tier top tip vertex
        vertices.append((0.0, t_top_y, 0.0))
        tip_idx = len(vertices)

        # Foliage side faces (triangles)
        for i in range(sides):
            b1 = tier_base_idx + i
            b2 = tier_base_idx + (i + 1) % sides
            faces_foliage.append([b1, b2, tip_idx])

        # Foliage tier bottom cap
        faces_foliage.append([tier_base_idx + i for i in range(sides - 1, -1, -1)])

    materials = {
        "TrunkMaterial": trunk_color,
        "FoliageMaterial": foliage_color,
    }

    faces_by_material = {
        "TrunkMaterial": faces_trunk,
        "FoliageMaterial": faces_foliage,
    }

    return _write_obj_and_mtl(output_dir, model_name, vertices, faces_by_material, materials)


def generate_low_poly_rock(
    output_dir: str = "./models",
    model_name: str = "low_poly_rock",
    rock_color: str = "#708090",
    scale: float = 1.0,
    seed: int = 42,
) -> Tuple[str, str, str, int, int]:
    """Generates a procedural low-poly boulder/rock with jittered vertices."""
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
    """Generates a procedural low-poly house model with walls, roof, and door."""
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

    faces_walls = [
        [1, 2, 3, 4],
        [6, 5, 8, 7],
        [5, 1, 4, 8],
        [2, 6, 7, 3],
        [1, 5, 6, 2],
    ]

    faces_roof = [
        [9, 10, 13],
        [11, 12, 14],
        [10, 11, 14, 13],
        [12, 9, 13, 14],
    ]

    faces_door = [
        [15, 16, 17, 18]
    ]

    materials = {
        "WallMaterial": wall_color,
        "RoofMaterial": roof_color,
        "DoorMaterial": door_color,
    }

    faces_by_material = {
        "WallMaterial": faces_walls,
        "RoofMaterial": faces_roof,
        "DoorMaterial": faces_door,
    }

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
    vertices = []
    faces = []

    vertices.append((0.0, 0.0, 0.0))

    mid_y = height * 0.4
    for i in range(sides):
        angle = 2 * math.pi * i / sides
        vertices.append((radius * math.cos(angle), mid_y, radius * math.sin(angle)))

    vertices.append((0.0, height, 0.0))
    top_idx = sides + 2

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
