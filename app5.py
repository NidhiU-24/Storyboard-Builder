import streamlit as st
import requests
import os
import io
from PIL import Image
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import time

# ── Load token ─────────────────────────────────────────────
load_dotenv()
HF_TOKEN = os.getenv("HF_API_KEY")

# ── Style options — applied to EVERY panel ─────────────────
STYLES = {
    "🎨 Anime / Studio Ghibli": "studio ghibli anime style, hand-drawn, soft watercolor, warm lighting, highly detailed, consistent character design",
    "🖼️ Cinematic / Realistic": "cinematic photograph, realistic, 35mm film, dramatic lighting, sharp focus, high detail, consistent color grading",
    "✏️ Comic Book": "comic book illustration, bold outlines, flat colors, consistent art style, graphic novel, professional illustration",
    "🖌️ Oil Painting": "oil painting, classical art style, rich colors, painterly brushstrokes, dramatic chiaroscuro lighting, consistent style",
    "🌑 Dark Fantasy": "dark fantasy digital art, moody atmosphere, dramatic shadows, highly detailed, consistent dark color palette, cinematic",
}

# ── Image generation ───────────────────────────────────────
def generate_image(prompt: str, style_suffix: str):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    url = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"

    # Prepend and append style to every prompt for consistency
    full_prompt = f"{style_suffix}, {prompt}, {style_suffix}"

    payload = {
        "inputs": full_prompt,
        "parameters": {
            "num_inference_steps": 30,
            "guidance_scale": 8.5,   # higher = sticks closer to prompt/style
            "width": 768,
            "height": 512,
        }
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=180)

    if resp.status_code == 503:
        wait = resp.json().get("estimated_time", 20)
        st.info(f"Model warming up, waiting {int(wait)}s…")
        time.sleep(int(wait) + 5)
        resp = requests.post(url, headers=headers, json=payload, timeout=180)

    if resp.status_code != 200:
        st.error(f"API error {resp.status_code}: {resp.text[:300]}")
        return None

    if "image" not in resp.headers.get("content-type", ""):
        st.error(f"Unexpected response: {resp.text[:300]}")
        return None

    return Image.open(io.BytesIO(resp.content))


# ── Auto panel descriptions via Ollama ─────────────────────
def generate_scene_description(idea: str, style_name: str, panel_num: int, total: int) -> str:
    prompt = f"""You are a storyboard artist working in {style_name} style.
Story idea: "{idea}"
Write a single vivid image prompt for panel {panel_num} of {total}.
Output ONLY the image prompt. No explanation, no numbering.
Include: lighting, mood, camera angle, key objects.
Keep the same main character and setting throughout all panels."""
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "llama3", "prompt": prompt, "stream": False},
            timeout=60,
        )
        return resp.json()["response"].strip()
    except:
        return f"Panel {panel_num} scene from story: {idea}"


# ── PDF builder ────────────────────────────────────────────
def build_pdf(panels, style_name):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    pw, ph = A4

    # Cover page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(pw/2, ph/2 + 20, "AI Storyboard")
    c.setFont("Helvetica", 14)
    c.drawCentredString(pw/2, ph/2 - 20, f"Style: {style_name}")
    c.showPage()

    for idx, (desc, img) in enumerate(panels):
        img_buf = io.BytesIO()
        img.save(img_buf, format="PNG")
        img_buf.seek(0)

        draw_w = pw - 80
        draw_h = draw_w * (img.height / img.width)
        x = (pw - draw_w) / 2
        y = ph - 60 - draw_h

        c.drawImage(ImageReader(img_buf), x, y, width=draw_w, height=draw_h)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(40, y - 22, f"Panel {idx + 1}")
        c.setFont("Helvetica", 10)

        words, line, lines = desc.split(), "", []
        for w in words:
            test = f"{line} {w}".strip()
            if c.stringWidth(test, "Helvetica", 10) < pw - 80:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)

        ty = y - 38
        for ln in lines[:5]:
            c.drawString(40, ty, ln)
            ty -= 14

        c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════
st.set_page_config(page_title="AI Storyboard Builder", layout="wide")
st.title("Storyboard Builder")
st.caption("All panels share the same visual style for a consistent storyboard look.")

if not HF_TOKEN:
    st.error("❌ HF_API_KEY not found in .env file.")
    st.stop()

# ── Style picker ───────────────────────────────────────────
st.subheader("1. Choose a visual style")
style_name = st.selectbox("All panels will use this style:", list(STYLES.keys()))
style_suffix = STYLES[style_name]
st.caption(f"Style prompt: `{style_suffix}`")

# ── Mode ───────────────────────────────────────────────────
st.subheader("2. Describe your panels")
mode = st.radio(
    "How do you want to fill in the panels?",
    ["✍️ I'll write each panel myself", "🤖 Auto-generate from a story idea (uses Ollama)"],
    horizontal=True,
)

num_panels = st.slider("Number of panels", 1, 6, 3)
panel_prompts = []

if mode.startswith("✍️"):
    cols = st.columns(2)
    for i in range(num_panels):
        with cols[i % 2]:
            txt = st.text_area(
                f"Panel {i+1}",
                placeholder="e.g. A girl with brown hair runs through a misty forest, overhead shot, golden light",
                key=f"p{i}",
                height=90,
            )
            panel_prompts.append(txt.strip())
else:
    story_idea = st.text_input(
        "Your story idea",
        placeholder="e.g. A young girl discovers a magical forest and befriends its creatures",
    )
    panel_prompts = [story_idea] * num_panels

# ── Generate ───────────────────────────────────────────────
st.subheader("3. Generate")
if st.button("🖼️ Generate Storyboard", type="primary"):

    if mode.startswith("🤖"):
        if not story_idea.strip():
            st.warning("Please enter a story idea first.")
            st.stop()
        st.info("Generating panel descriptions with Ollama…")
        panel_prompts = [
            generate_scene_description(story_idea, style_name, i+1, num_panels)
            for i in range(num_panels)
        ]
        # Show what Ollama generated
        with st.expander("📝 Generated panel descriptions"):
            for i, p in enumerate(panel_prompts):
                st.write(f"**Panel {i+1}:** {p}")

    filled = [(i, p) for i, p in enumerate(panel_prompts) if p]
    if not filled:
        st.warning("Please fill in at least one panel.")
        st.stop()

    st.subheader("Your Storyboard")
    progress = st.progress(0, text="Starting…")
    generated = []

    for step, (idx, prompt) in enumerate(filled):
        progress.progress(step / len(filled), text=f"Generating panel {idx+1} of {len(filled)}…")
        with st.spinner(f"Panel {idx+1}…"):
            img = generate_image(prompt, style_suffix)
        if img:
            generated.append((prompt, img))
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(img, caption=f"Panel {idx+1}", use_column_width=True)
            with c2:
                st.markdown(f"**Panel {idx+1}**")
                st.write(prompt)

    progress.progress(1.0, text="✅ Done!")

    if generated:
        pdf_bytes = build_pdf(generated, style_name)
        st.success("Storyboard complete!")
        st.download_button(
            "Download PDF Storyboard",
            data=pdf_bytes,
            file_name="storyboard.pdf",
            mime="application/pdf",
        )