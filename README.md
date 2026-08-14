# 🎨 Low-Poly 3D Model Studio ✨

> **A conversational AI agent that helps 3D creators, indie game developers, and artists procedurally generate low-polygon 3D models (.obj, .mtl, .zip packages), Blender Python (`bpy`) scripts, and custom 3D game assets.**

---

## 🌟 Overview

**Low-Poly 3D Model Studio** is an intelligent agent built with the **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Agent Runtime**. It transforms natural language prompts into fully realized, valid 3D geometry packages with material definitions ready for instant direct download and 1-click import into **Blender**, **Unity**, or **Unreal Engine**.

Whether you need a low-poly pine tree, glowing crystal cluster, cozy alpine cabin, or procedural rock boulder, Low-Poly 3D Model Studio calculates vertex geometry, builds Wavefront `.obj` & `.mtl` files, packages them into a `.zip`, and serves direct browser download links—all while rendering rich visual A2UI cards and live 3D spinning previews!

---

## ✨ Key Features

- 🌲 **Procedural 3D Asset Generation**: Instantly generates low-poly trees, crystals, houses, rocks, and custom props with customizable vertex counts and hex color palettes.
- 📦 **Direct Package Downloads**: Creates complete Wavefront `.obj`, `.mtl`, and `.zip` packages converted into base64 Data URLs for instant direct browser downloads.
- ⚙️ **Studio Dialogue & Swatch Palettes**: Features a cute glassmorphism modal dialogue with preset color swatches (`🌲 Forest Green`, `🔮 Neon Amethyst`, `🔥 Volcanic Gem`, `❄️ Ice Frost`) and custom dual color pickers.
- 📐 **Live 3D Mesh Inspector Canvas**: Interactive spinning 3D wireframe mesh canvas with glowing vertices that renders inside chat responses.
- 🎨 **A2UI Rich Visual UI Cards (v0.8)**: Emits structured A2UI card layouts (`Card`, `Column`, `Row`, `Text`, `Image`) using `A2uiSchemaManager` (v0.8) and `BasicCatalog`.
- ❓ **Blender Import Guide**: Step-by-step interactive cheat sheet modal guiding creators through extracting and applying material viewports in Blender.

---

## 🛠️ Google Cloud Tools & Architecture

This project leverages the full suite of **Google Cloud & Vertex AI** agent infrastructure:

| Google Cloud Tool | Usage in Low-Poly 3D Model Studio |
| :--- | :--- |
| 🧠 **Vertex AI Memory Bank** | Cross-session long-term memory that remembers user art style preferences, target polygon budgets, and favorite color palettes. |
| 🗄️ **Google Cloud Firestore** | Manages persistent conversation session state and context history across turn-by-turn agent interactions. |
| 🪣 **Google Cloud Storage (GCS)** | Stores generated 3D model packages, export archives, and concept art assets. |
| 📚 **Vertex AI RAG Engine** | Retrieval-Augmented Generation grounding for Blender `bpy` Python API documentation, mesh math formulas, and 3D modeling standards. |
| 🎨 **Imagen / Gemini Image Generation** | Generates 2D low-poly concept art and color palette previews prior to 3D mesh procedural compilation. |
| 📱 **A2UI (Agent-to-User Interface v0.8)** | Agent-driven UI rendering engine using `a2ui-agent-sdk` (v0.8) to render rich card layouts natively in client interfaces. |
| 🚀 **Google Cloud Run & Agent Runtime** | Deployed backend proxy server on Cloud Run talking over the A2A protocol to Agent Engine (`reasoningEngines`). |

---

## 🏗️ Project Structure

```
low-poly-3d-model-studio/
├── app/
│   ├── agent.py               # Main ADK Agent with A2UI Schema Manager & callbacks
│   ├── model_generator.py      # Procedural Wavefront .obj/.mtl/.zip geometry generators
│   └── a2ui_utils.py          # A2UI response rewrapper & renderer helper
├── frontend/
│   ├── main.py                # FastAPI proxy server talking A2A protocol
│   ├── requirements.txt       # Frontend proxy dependencies
│   └── static/
│       └── index.html         # Cute candy-pink UI with Studio Dialogue, 3D Canvas, & A2UI renderer
├── pyproject.toml             # Project dependencies (google-adk, a2ui-agent-sdk)
├── deployment_metadata.json   # Cloud Agent Runtime deployment IDs
└── README.md                  # Project documentation
```

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python `3.10+` and `uv` package manager installed.
- Google Cloud SDK (`gcloud`) authenticated with Application Default Credentials (`gcloud auth application-default login`).

### 2. Run Agent Locally
```bash
# Install dependencies
uv sync

# Run ADK Web Agent Playground
uv run adk web . --host 0.0.0.0 --port 8080 --allow_origins '*'
```
Access the Agent Playground at: **[http://localhost:8080/dev-ui/?app=app](http://localhost:8080/dev-ui/?app=app)**

### 3. Run Custom Web Frontend Locally
```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/952105776961/locations/us-east1/reasoningEngines/6464583013555503104"
export PORT=8080
uv run python frontend/main.py
```
Access your app at: **[http://localhost:8080/](http://localhost:8080/)**

---

## 🎨 Importing Generated Models into Blender

1. Click **Download Complete 3D Model Package (.zip)** in the chat response or Studio Dialogue.
2. Extract the `.zip` archive to get your `.obj` geometry and `.mtl` material file.
3. In **Blender**: Go to `File ➔ Import ➔ Wavefront (.obj)`.
4. Select your `.obj` file. Switch Viewport Shading to **Material Preview** to view your colors!

---

## 📄 License

Licensed under the Apache License, Version 2.0.
