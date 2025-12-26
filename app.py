"""
The main entry-point for the Spaces application
Create a Gradio app and launch it
"""

from arena.display import make_display
from arena.display import theme
import gradio as gr
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    # Configuration pour le développement local
    port = int(os.getenv("PORT", 7860))
    
    local = True
    
    server_name = "127.0.0.1" if local else "0.0.0.0"
    
    load_dotenv(override=True)
    app = make_display()
    app.launch(
        theme=theme,
        server_name=server_name,
        server_port=port,
        share=False,
        show_error=True,
    )