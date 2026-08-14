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
import sys
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.model_generator import (
    file_to_data_url,
    generate_low_poly_balloon,
    generate_low_poly_campfire,
    generate_low_poly_chest,
    generate_low_poly_crystal,
    generate_low_poly_house,
    generate_low_poly_hover_pod,
    generate_low_poly_iceberg,
    generate_low_poly_mushroom,
    generate_low_poly_obelisk,
    generate_low_poly_potion,
    generate_low_poly_rock,
    generate_low_poly_sword_in_stone,
    generate_low_poly_tree,
    generate_low_poly_windmill,
    verify_zip_archive,
)

MODEL = "gemini-3.6-flash"


def generate_3d_model(
    model_type: str,
    output_name: str = "low_poly_model",
    primary_color: str = "#2e8b57",
    secondary_color: str = "#8b4513",
    output_dir: str = "./models",
) -> str:
    """Procedurally generates a verified low-polygon 3D model (.obj, .mtl, .zip) with direct browser download links.

    Supported model_type values:
    'tree', 'rock', 'house', 'crystal', 'mushroom', 'obelisk', 'potion',
    'chest', 'sword', 'windmill', 'campfire', 'iceberg', 'hover_pod', 'balloon'.

    Args:
        model_type: Type of 3D model to generate.
        output_name: Name for the output files (e.g. 'magic_potion').
        primary_color: Primary hex color code (e.g. '#ff1744').
        secondary_color: Secondary hex color code (e.g. '#a1887f').
        output_dir: Output directory path.

    Returns:
        Summary string with vertex count, face count, direct download URLs, and Blender import steps.
    """
    os.makedirs(output_dir, exist_ok=True)
    m_type = model_type.lower().strip()

    try:
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
            created_type = "Low-Poly Rock"
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
        elif "shroom" in m_type or "fungi" in m_type or "mushroom" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_mushroom(
                output_dir=output_dir,
                model_name=output_name,
                cap_color=primary_color,
                stem_color=secondary_color,
            )
            created_type = "Low-Poly Glow Mushroom"
        elif "obelisk" in m_type or "rune" in m_type or "monolith" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_obelisk(
                output_dir=output_dir,
                model_name=output_name,
                stone_color=primary_color,
                rune_color=secondary_color,
            )
            created_type = "Low-Poly Runestone Obelisk"
        elif "potion" in m_type or "flask" in m_type or "elixir" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_potion(
                output_dir=output_dir,
                model_name=output_name,
                liquid_color=primary_color,
                cork_color=secondary_color,
            )
            created_type = "Low-Poly Magic Potion"
        elif "chest" in m_type or "treasure" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_chest(
                output_dir=output_dir,
                model_name=output_name,
                wood_color=primary_color,
                gold_color=secondary_color,
            )
            created_type = "Low-Poly Treasure Chest"
        elif "sword" in m_type or "excalibur" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_sword_in_stone(
                output_dir=output_dir,
                model_name=output_name,
                stone_color=primary_color,
                gold_color=secondary_color,
            )
            created_type = "Low-Poly Sword in Stone"
        elif "windmill" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_windmill(
                output_dir=output_dir,
                model_name=output_name,
                tower_color=primary_color,
                roof_color=secondary_color,
            )
            created_type = "Low-Poly Windmill"
        elif "campfire" in m_type or "camp" in m_type or "pot" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_campfire(
                output_dir=output_dir,
                model_name=output_name,
                fire_color=primary_color,
                wood_color=secondary_color,
            )
            created_type = "Low-Poly Campfire & Pot"
        elif "iceberg" in m_type or "glacier" in m_type or "ice" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_iceberg(
                output_dir=output_dir,
                model_name=output_name,
                glacier_color=primary_color,
                deep_color=secondary_color,
            )
            created_type = "Low-Poly Iceberg Glacier"
        elif "hover" in m_type or "pod" in m_type or "spaceship" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_hover_pod(
                output_dir=output_dir,
                model_name=output_name,
                chassis_color=primary_color,
                canopy_color=secondary_color,
            )
            created_type = "Low-Poly Sci-Fi Hover Pod"
        elif "balloon" in m_type or "airship" in m_type:
            obj, mtl, zip_p, v_cnt, f_count = generate_low_poly_balloon(
                output_dir=output_dir,
                model_name=output_name,
                balloon_color=primary_color,
                basket_color=secondary_color,
            )
            created_type = "Low-Poly Hot Air Balloon"
        else:
            # Fallback to Tree
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

        # Strictly verify ZIP archive integrity
        if not verify_zip_archive(abs_zip):
            return f"⚠️ Error: Asset '{model_type}' failed ZIP verification and was omitted."

        base_obj_name = os.path.basename(abs_obj)
        base_mtl_name = os.path.basename(abs_mtl)
        base_zip_name = os.path.basename(abs_zip)

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
            f"- ZIP Verified: ✅ Unzippable\n"
            f"- Saved Locally At: `{abs_zip}`\n\n"
            f"🎨 **Blender Import Instructions**:\n"
            f"1. Click the download link above to save `{base_zip_name}` directly to your computer.\n"
            f"2. Extract `{base_zip_name}` to get `{base_obj_name}` and `{base_mtl_name}`.\n"
            f"3. Open Blender ➔ File ➔ Import ➔ Wavefront (.obj).\n"
            f"4. Select `{base_obj_name}`. Blender will automatically load `{base_mtl_name}` and render your materials!"
        )

    except Exception as e:
        return f"⚠️ Error creating asset '{model_type}': {str(e)}. Skipped asset generation."


# Build A2UI system prompt schema manager (version 0.8) with Basic Catalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Low-Poly 3D Model Studio, an expert AI assistant for procedural 3D model creation. "
        "You can generate 14 distinct low-poly 3D models: Tree, Rock, House, Crystal, Glow Mushroom, "
        "Runestone Obelisk, Magic Potion, Treasure Chest, Sword in Stone, Windmill, Campfire & Pot, "
        "Iceberg Glacier, Sci-Fi Hover Pod, and Hot Air Balloon (.obj, .mtl, and verified .zip files) "
        "that can be downloaded directly to their computer and opened in Blender. Always use `generate_3d_model` "
        "to create 3D models and provide direct HTML download links."
    ),
    workflow_description="Analyze the user request, execute `generate_3d_model` when requested, and return structured A2UI visual cards when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[generate_3d_model],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
