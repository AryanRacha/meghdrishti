import gradio as gr
from app.main import app as fastapi_app
import spaces # Required for ZeroGPU

# Create a dummy Gradio interface just to satisfy Hugging Face
@spaces.GPU # Request ZeroGPU allocation when this function runs (though FastAPI handles the actual inference)
def status():
    return "Meghdrishti V2 API is live and running on ZeroGPU!"

demo = gr.Interface(fn=status, inputs=[], outputs="text")

# Mount the FastAPI app directly onto the Gradio space
# The FastAPI app will handle all routes, while the Gradio UI sits at /gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")
