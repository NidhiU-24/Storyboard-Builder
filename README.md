# 🎬  Storyboard Builder
An AI-powered storyboard generator that creates consistent, styled images for each panel of your story — and exports them as a downloadable PDF.
Built with Streamlit, Hugging Face Inference API, and Ollama (Llama 3).

## Features

🖼️ Generate AI images for each storyboard panel
🎨 Choose from 5 consistent visual styles across all panels
✍️ Write your own panel descriptions or auto-generate them from a story idea
🤖 Uses local Ollama (Llama 3) to turn story ideas into detailed image prompts
📥 Export your complete storyboard as a PDF
💸 Runs on Hugging Face's free API — no GPU required on your machine


## 🎨 Available Styles

### StyleDescription
 - 🎨 Anime / Studio GhibliSoft watercolor, hand-drawn, warm lighting
 - 🖼️ Cinematic / Realistic35mm film look, dramatic lighting, sharp focus
 - ✏️ Comic BookBold outlines, flat colors, graphic novel feel
 - 🖌️ Oil PaintingClassical brushstrokes, rich colors, chiaroscuro
 - 🌑 Dark FantasyMoody atmosphere, dramatic shadows, dark palette

## 🛠️ Tech Stack

 - Streamlit — Web UI
 - Hugging Face Router API — Image generation (Stable Diffusion XL)
 - Ollama + Llama 3 — Local LLM for auto-generating panel descriptions
 - ReportLab — PDF export
 - Pillow — Image handling


## 📋 Prerequisites

 - Python 3.12+
 - Ollama installed and running
 - A free Hugging Face account and API token

