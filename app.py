import gradio as gr
from game import NimGame

game = NimGame()

def reset_game(n, k):
    global game
    game = NimGame(n, k)
    return f"Bâtonnets restants: {game.n}"

def human_move(move):
    global game

    if game.is_over():
        return "Partie terminée"

    try:
        game.play(move)
    except ValueError as e:
        return str(e)

    if game.is_over():
        return f"Partie terminée. Perdant: {game.loser()}"

    return f"Bâtonnets restants: {game.n}"

with gr.Blocks() as demo:
    gr.Markdown("## Nim – Misère (le dernier perd)")

    n = gr.Slider(5, 30, value=15, step=1, label="Bâtonnets initiaux")
    k = gr.Slider(2, 5, value=3, step=1, label="Max par coup")

    reset_btn = gr.Button("Nouvelle partie")
    output = gr.Textbox(label="État du jeu")

    with gr.Row():
        b1 = gr.Button("Retirer 1")
        b2 = gr.Button("Retirer 2")
        b3 = gr.Button("Retirer 3")

    reset_btn.click(reset_game, [n, k], output)
    b1.click(lambda: human_move(1), output, output)
    b2.click(lambda: human_move(2), output, output)
    b3.click(lambda: human_move(3), output, output)

demo.launch()
