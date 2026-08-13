# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.model_generator import (
    file_to_data_url,
    generate_low_poly_crystal,
    generate_low_poly_house,
    generate_low_poly_rock,
    generate_low_poly_tree,
)

MODEL = "gemini-3.6-flash"


def generate_3d_model(
    model_type: str,
    output_name: str = "low_poly_model",
    primary_color: str = "#2e8b57",
    secondary_color: str = "#8b4513",
    output_dir: str = "./models",
) -> str:
    """Procedurally generates a low-polygon 3D model and exports it as valid .obj, .mtl, and .zip files with direct browser download links.

    Args:
        model_type: Type of 3D model to generate ('tree', 'rock', 'house', or 'crystal').
        output_name: Name for the output files (e.g. 'oak_tree' creates 'oak_tree.obj', 'oak_tree.mtl', 'oak_tree.zip').
        primary_color: Primary hex color code (e.g. '#2e8b57' for green foliage, '#708090' for rock).
        secondary_color: Secondary hex color code (e.g. '#8b4513' for wood trunk, '#b22222' for roof).
        output_dir: Directory where .obj, .mtl, and .zip files should be saved.

    Returns:
        A detailed summary string with generated file paths, vertex count, face count, direct download URLs, and Blender import instructions.
    """
    os.makedirs(output_dir, exist_ok=True)
    m_type = model_type.lower().strip()

    if "tree" in m_type or "pine" in m_type or "wood" in m_type:
        obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_tree(
            output_dir=output_dir,
            model_name=output_name,
            foliage_color=primary_color,
            trunk_color=secondary_color,
        )
        created_type = "Low-Poly Tree"
    elif "rock" in m_type or "stone" in m_type or "boulder" in m_type:
        obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_rock(
            output_dir=output_dir,
            model_name=output_name,
            rock_color=primary_color,
        )
        created_type = "Low-Poly Rock/Boulder"
    elif "house" in m_type or "building" in m_type or "cabin" in m_type:
        obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_house(
            output_dir=output_dir,
            model_name=output_name,
            wall_color=primary_color,
            roof_color=secondary_color,
        )
        created_type = "Low-Poly House"
    elif "crystal" in m_type or "gem" in m_type or "prism" in m_type:
        obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_crystal(
            output_dir=output_dir,
            model_name=output_name,
            crystal_color=primary_color,
        )
        created_type = "Low-Poly Crystal"
    else:
        obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_tree(
            output_dir=output_dir,
            model_name=output_name,
            foliage_color=primary_color,
            trunk_color=secondary_color,
        )
        created_type = f"Low-Poly Asset ({model_type})"

    abs_obj = os.path.abspath(obj)
    abs_mtl = os.path.abspath(mtl)
    abs_zip = os.path.abspath(zip_p)

    base_obj_name = os.path.basename(abs_obj)
    base_mtl_name = os.path.basename(abs_mtl)
    base_zip_name = os.path.basename(abs_zip)

    # Convert files to Base64 Data URLs for instant direct browser download
    zip_data_url = file_to_data_url(abs_zip, "application/zip")
    obj_data_url = file_to_data_url(abs_obj, "text/plain")

    return (
        f"Successfully generated 3D Model ({created_type})!\n\n"
        f"📥 **Direct Downloads to Your Computer**:\n"
        f"- 📦 <a href=\"{zip_data_url}\" download=\"{base_zip_name}\"><b>Download Complete 3D Model Package ({base_zip_name})</b></a>\n"
        f"- 📄 <a href=\"{obj_data_url}\" download=\"{base_obj_name}\"><b>Download 3D Geometry ({base_obj_name})</b></a>\n\n"
        f"📊 **Model Statistics**:\n"
        f"- Vertices: {v_cnt}\n"
        f"- Faces: {f_count}\n"
        f"- Saved Locally At: `{abs_zip}`\n\n"
        f"🎨 **Blender Import Instructions**:\n"
        f"1. Click the download link above to save `{base_zip_name}` directly to your computer.\n"
        f"2. Extract `{base_zip_name}` to get `{base_obj_name}` and `{base_mtl_name}`.\n"
        f"3. Open Blender ➔ File ➔ Import ➔ Wavefront (.obj).\n"
        f"4. Select `{base_obj_name}`. Blender will automatically load `{base_mtl_name}` and render your materials!"
    )


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=(
        "You are Low-Poly 3D Model Studio, an expert AI assistant for procedural 3D model creation. "
        "You help 3D artists and creators generate low-polygon 3D models (.obj, .mtl, and .zip files) "
        "that can be downloaded directly to their computer and opened in Blender. Always use the `generate_3d_model` tool "
        "to generate 3D models and provide the user with the direct HTML download links."
    ),
    tools=[generate_3d_model],
)

app = App(
    root_agent=root_agent,
    name="app",
)
