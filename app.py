# """
# The main entry-point for the Spaces application
# Create a Gradio app and launch it
# """

# from arena.display import make_display
# from arena.display import theme
# import gradio as gr
# from dotenv import load_dotenv
# import os

# if __name__ == "__main__":
#     # Configuration pour le développement local
#     port = int(os.getenv("PORT", 7860))
    
#     local = True
    
#     server_name = "127.0.0.1" if local else "0.0.0.0"
    
#     # Check if there is a env variable server_name
#     if os.getenv("SERVER_NAME"):
#         print("Using SERVER_NAME from environment")
#         server_name = os.getenv("SERVER_NAME")
        
#     print(f"Starting server on {server_name}:{port}")
    
#     load_dotenv(override=True)
#     app = make_display()
#     app.launch(
#         server_name=server_name,
#         server_port=port,
#         share=False,
#         show_error=True,
#     )

# from flask import Flask

# app = Flask(__name__)

# @app.route("/")
# def home():
#     return "Hello from ai.tommygagne.com 🚀 (Hello world)"

"""
WSGI entry point for DirectAdmin / Passenger
"""

import sys
import os
import gradio as gr
from flask import Flask

# Fix path (important sur Passenger)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Flask app (WSGI)
flask_app = Flask(__name__)

# Gradio app
def hello():
    return "Hello Gradio (via Flask + Passenger)"

gradio_app = gr.Interface(fn=hello, inputs=[], outputs="text")

# Monter Gradio dans Flask
app = gr.mount_gradio_app(flask_app, gradio_app, path="/")
