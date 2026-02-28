from diffusers import StableDiffusionPipeline
import torch

# Load the pipeline without torch_dtype=float16 (works better on CPU)
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float32,
)

# Use CPU explicitly (remove if you want to run on GPU)
pipe = pipe.to("cpu")

# Set a descriptive prompt and generate an image with decent quality
prompt = "a beautiful landscape with mountains and a lake, vivid colors, high detail"

image = pipe(
    prompt,
    height=512,
    width=512,
    num_inference_steps=50,
    guidance_scale=7.5,
).images[0]

# Show the generated image
image.show()

# Optionally save the image locally
image.save("generated_image.png")