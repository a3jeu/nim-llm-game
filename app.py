"""
The main entry-point for the Spaces application
Create a Gradio app and launch it
"""

from arena.display import make_display
from arena.display import css, js, theme
import gradio as gr
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    # Configuration pour le développement local
    port = int(os.getenv("PORT", 7860))
    
    load_dotenv(override=True)
    app = make_display()
    app.launch(
        css=css,
        js=js,
        theme=theme,
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
    )