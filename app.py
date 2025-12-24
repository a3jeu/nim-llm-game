"""
The main entry-point for the Spaces application
Create a Gradio app and launch it
"""

from arena.display import make_display
from arena.display import css, js, theme
import gradio as gr
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv(override=True)
    app = make_display()
    app.launch(
        css=css,
        js=js,
        theme=theme,
    )