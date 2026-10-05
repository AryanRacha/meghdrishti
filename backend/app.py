import gradio as gr
from app.main import app as fastapi_app
import spaces # Required for ZeroGPU
import uvicorn

# Create a dummy Gradio interface just to satisfy Hugging Face
@spaces.GPU # Request ZeroGPU allocation when this function runs
def status():
    return "Meghdrishti V2 API is live and running on ZeroGPU!"

demo = gr.Interface(fn=status, inputs=[], outputs="text")

# Mount the FastAPI app directly onto the Gradio space
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
