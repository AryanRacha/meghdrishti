import gradio as gr
from app.main import app as fastapi_app
import uvicorn

# Create a minimal Gradio UI (Required by Hugging Face's Free Tier SDK)
with gr.Blocks() as demo:
    gr.Markdown("# Meghdrishti API is Live!")
    gr.Markdown("FastAPI backend is mounted and routing traffic.")

# Mount the FastAPI app. HF's Uvicorn runner will detect the FastAPI `app` and serve it!
app = gr.mount_gradio_app(fastapi_app, demo, path="/")
