from arena.nim_game import RED, BLUE
from arena.llm import LLM
from arena.player import HumanTurnException
import gradio as gr
import pandas as pd
from arena.game import Game

css = """
.dataframe-fix .table-wrap {
    min-height: 800px;
    max-height: 800px;
}
.button_hidden {
    display: none;
}
.hidden {
    display: none;
    visibility: hidden;
}
svg {
    height: 100%;
    width: auto;
    display: block;
}

footer{display:none !important}
"""

js = """
function refresh() {
    const url = new URL(window.location);

    if (url.searchParams.get('__theme') !== 'dark') {
        url.searchParams.set('__theme', 'dark');
        window.location.href = url.href;
    }
}
"""

theme = gr.themes.Default(primary_hue="sky")

ALL_MODEL_NAMES = LLM.all_model_names()

def message_html(game) -> str:
    """
    Return the message for the top of the UI
    """
    return f'<div style="text-align: center;font-size:18px">{game.nim_game.message()}</div>'

def format_records_for_table(games):
    """
    Turn the results objects into a pandas DataFrame for the Gradio Dataframe
    """
    df = pd.DataFrame(
        [
            [
                game.date,
                game.variant,
                game.red_player,
                game.blue_player,
                "Rouge" if game.red_won else "Bleu" if game.blue_won else "Nul",
            ]
            for game in reversed(games)
        ],
        columns=["Date", "Variante", "Joueur rouge", "Joueur bleu", "Gagnant"],
    )

    # Remove microseconds while preserving datetime format
    df["Date"] = pd.to_datetime(df["Date"]).dt.floor("s")
    return df

def format_ratings_for_table(ratings):
    """
    Turn the ratings into a List of Lists for the Gradio Dataframe
    """
    items = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    return [[item[0], int(round(item[1]))] for item in items]

def format_combined_ratings_for_table(ratings_global, ratings_normal, ratings_a, ratings_b):
    """
    Combine all ratings (global and by variant) into a single table
    Returns a list of lists with columns: Player, ELO, ELO (Normal), ELO (Variante A), ELO (Variante B)
    """
    # Get all unique players
    all_players = set()
    all_players.update(ratings_global.keys())
    all_players.update(ratings_normal.keys())
    all_players.update(ratings_a.keys())
    all_players.update(ratings_b.keys())
    
    # Create rows for each player
    rows = []
    for player in all_players:
        elo_global = int(round(ratings_global.get(player, 1000)))
        elo_normal = int(round(ratings_normal.get(player, 1000)))
        elo_a = int(round(ratings_a.get(player, 1000)))
        elo_b = int(round(ratings_b.get(player, 1000)))
        rows.append([player, elo_global, elo_normal, elo_a, elo_b])
    
    # Sort by global ELO (descending)
    rows.sort(key=lambda x: x[1], reverse=True)
    return rows


def check_human_turn(game):
    """
    Check if it's a human player's turn and return the appropriate UI updates
    Returns: (show_row, show_btn1, show_btn2, show_btn3, show_btn4)
    """
    if not game.nim_game.is_active():
        return (False, False, False, False, False)
    
    current_player = game.players[game.nim_game.player_to_move]
    if current_player.model == "Humain":
        valid_moves = game.nim_game.valid_moves()
        return (
            True,  # Show row
            1 in valid_moves,
            2 in valid_moves,
            3 in valid_moves,
            4 in valid_moves,
        )
    return (False, False, False, False, False)


def load_callback(red_llm, blue_llm, variant="normal"):
    """
    Callback called when the game is started. Create a new Game object for the state.
    """
    game = Game(red_llm, blue_llm, variant=variant)
    enabled = gr.Button(interactive=True)
    message = message_html(game)
    
    # Check if it's a human's turn
    show_row, show_btn1, show_btn2, show_btn3, show_btn4 = check_human_turn(game)
    
    # Dropdowns are enabled since game hasn't started yet
    dropdowns_enabled = gr.Dropdown(interactive=True)
    
    return (
        game,
        game.display(),
        message,
        "",
        "",
        enabled,
        enabled,
        enabled,
        gr.update(visible=show_row),  # Human buttons row
        gr.update(visible=show_btn1, elem_classes=[] if show_btn1 else ["button_hidden"]),  # human_button_1
        gr.update(visible=show_btn2, elem_classes=[] if show_btn2 else ["button_hidden"]),  # human_button_2
        gr.update(visible=show_btn3, elem_classes=[] if show_btn3 else ["button_hidden"]),  # human_button_3
        gr.update(visible=show_btn4, elem_classes=[] if show_btn4 else ["button_hidden"]),  # human_button_4
        dropdowns_enabled,  # red_dropdown
        dropdowns_enabled,  # blue_dropdown
        dropdowns_enabled,  # variant_dropdown
    )


def leaderboard_callback(game):
    """
    Callback called when the user switches to the Leaderboard tab. Load in the results.
    """
    records_df = format_records_for_table(Game.get_games())
    ratings_global = Game.get_ratings()
    ratings_normal = Game.get_ratings_by_variant('normal')
    ratings_a = Game.get_ratings_by_variant('a')
    ratings_b = Game.get_ratings_by_variant('b')
    combined_ratings = format_combined_ratings_for_table(ratings_global, ratings_normal, ratings_a, ratings_b)
    return records_df, combined_ratings


def move_callback(game):
    """
    Callback called when the user clicks to do a single move.
    """
    try:
        game.pick()
        message = message_html(game)
        if_active = gr.Button(interactive=game.nim_game.is_active())
        if not game.nim_game.is_active():
            game.record()
        
        # Disable dropdowns if game has started
        dropdowns_interactive = gr.Dropdown(interactive=not game.nim_game.game_started())
        
        # Check if it's now a human's turn after the move
        show_row, show_btn1, show_btn2, show_btn3, show_btn4 = check_human_turn(game)
        
        # Disable move/run buttons if it's human's turn
        move_run_interactive = gr.Button(interactive=not show_row and game.nim_game.is_active())
        
        return (
            game,
            game.display(),
            message,
            game.thoughts(RED),
            game.thoughts(BLUE),
            move_run_interactive,
            move_run_interactive,
            gr.update(visible=show_row),  # Show/hide human buttons row based on whose turn it is
            gr.update(visible=show_btn1, elem_classes=[] if show_btn1 else ["button_hidden"]),  # human_button_1
            gr.update(visible=show_btn2, elem_classes=[] if show_btn2 else ["button_hidden"]),  # human_button_2
            gr.update(visible=show_btn3, elem_classes=[] if show_btn3 else ["button_hidden"]),  # human_button_3
            gr.update(visible=show_btn4, elem_classes=[] if show_btn4 else ["button_hidden"]),  # human_button_4
            dropdowns_interactive,  # red_dropdown
            dropdowns_interactive,  # blue_dropdown
            dropdowns_interactive,  # variant_dropdown
        )
    except HumanTurnException as e:
        # Human player needs to make a move - show appropriate buttons
        message = message_html(game)
        valid_moves = e.valid_moves
        
        # Disable dropdowns if game has started
        dropdowns_interactive = gr.Dropdown(interactive=not game.nim_game.game_started())
        
        return (
            game,
            game.display(),
            message,
            game.thoughts(RED),
            game.thoughts(BLUE),
            gr.Button(interactive=False),  # Disable move button
            gr.Button(interactive=False),  # Disable run button
            gr.update(visible=True),  # Show human buttons row
            gr.update(elem_classes=[] if 1 in valid_moves else ["button_hidden"]),  # human_button_1
            gr.update(elem_classes=[] if 2 in valid_moves else ["button_hidden"]),  # human_button_2
            gr.update(elem_classes=[] if 3 in valid_moves else ["button_hidden"]),  # human_button_3
            gr.update(elem_classes=[] if 4 in valid_moves else ["button_hidden"]),  # human_button_4
            dropdowns_interactive,  # red_dropdown
            dropdowns_interactive,  # blue_dropdown
            dropdowns_interactive,  # variant_dropdown
        )


def run_callback(game):
    """
    Callback called when the user runs an entire game. Reset the board, run the game, store results.
    Yield interim results so the UI updates.
    Note: This doesn't support human players - use single move mode for human play.
    """
    enabled = gr.Button(interactive=True)
    disabled = gr.Button(interactive=False)
    dropdowns_disabled = gr.Dropdown(interactive=False)
    
    game.reset()
    message = message_html(game)
    yield (
        game,
        game.display(),
        message,
        game.thoughts(RED),
        game.thoughts(BLUE),
        disabled,
        disabled,
        disabled,
        gr.update(visible=False), 
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_1
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_2
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_3
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_4
        dropdowns_disabled,
        dropdowns_disabled,
        dropdowns_disabled,
    )
    while game.nim_game.is_active():
        try:
            game.pick()
            message = message_html(game)
            yield (
                game,
                game.display(),
                message,
                game.thoughts(RED),
                game.thoughts(BLUE),
                disabled,
                disabled,
                disabled,
                gr.update(visible=False),
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_1
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_2
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_3
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_4
                dropdowns_disabled,
                dropdowns_disabled,
                dropdowns_disabled,
            )
        except HumanTurnException:
            # If a human player is encountered, stop the auto-run
            message = message_html(game) + "<br/><strong>Mode automatique arrêté : joueur humain détecté. Utilisez 'Prochain coup'.</strong>"
            yield (
                game,
                game.display(),
                message,
                game.thoughts(RED),
                game.thoughts(BLUE),
                enabled,
                disabled,
                enabled,
                gr.update(visible=False),
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_1
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_2
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_3
                gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_4
                dropdowns_disabled,
                dropdowns_disabled,
                dropdowns_disabled,
            )
            return
    
    game.record()
    yield (
        game,
        game.display(),
        message,
        game.thoughts(RED),
        game.thoughts(BLUE),
        disabled,
        disabled,
        enabled,
        gr.update(visible=False),
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_1
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_2
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_3
        gr.update(visible=False, elem_classes=["button_hidden"]),  # human_button_4
        dropdowns_disabled,
        dropdowns_disabled,
        dropdowns_disabled,
    )


def model_callback(player_name, game, new_model_name):
    """
    Callback when the user changes the model
    """
    player = game.players[player_name]
    player.switch_model(new_model_name)
    
    # Check if we need to show human buttons after model change
    show_row, show_btn1, show_btn2, show_btn3, show_btn4 = check_human_turn(game)
    
    # Disable dropdowns if game has started
    dropdowns_interactive = gr.Dropdown(interactive=not game.nim_game.game_started())
    
    message = message_html(game)
    return (
        game,
        game.display(),
        message,
        game.thoughts(RED),
        game.thoughts(BLUE),
        gr.update(visible=show_row),  # Human buttons row
        gr.update(visible=show_btn1, elem_classes=[] if show_btn1 else ["button_hidden"]),  # human_button_1
        gr.update(visible=show_btn2, elem_classes=[] if show_btn2 else ["button_hidden"]),  # human_button_2
        gr.update(visible=show_btn3, elem_classes=[] if show_btn3 else ["button_hidden"]),  # human_button_3
        gr.update(visible=show_btn4, elem_classes=[] if show_btn4 else ["button_hidden"]),  # human_button_4
        dropdowns_interactive,  # red_dropdown
        dropdowns_interactive,  # blue_dropdown
        dropdowns_interactive,  # variant_dropdown
    )


def red_model_callback(game, new_model_name):
    """
    Callback when red model is changed
    """
    return model_callback(RED, game, new_model_name)


def blue_model_callback(game, new_model_name):
    """
    Callback when blue model is changed
    """
    return model_callback(BLUE, game, new_model_name)


def variant_callback(game, new_variant):
    """
    Callback when variant is changed
    """
    if not game.nim_game.game_started():
        game.nim_game.variant = new_variant
    
    # Check if we need to show human buttons after variant change
    show_row, show_btn1, show_btn2, show_btn3, show_btn4 = check_human_turn(game)
    
    # Disable dropdowns if game has started
    dropdowns_interactive = gr.Dropdown(interactive=not game.nim_game.game_started())
    
    message = message_html(game)
    
    # Use only elem_classes for visibility control
    return (
        game,
        game.display(),
        message,
        game.thoughts(RED),
        game.thoughts(BLUE),
        gr.update(visible=show_row),  # Human buttons row
        gr.update(visible=show_btn1, elem_classes=[] if show_btn1 else ["button_hidden"]),  # human_button_1
        gr.update(visible=show_btn2, elem_classes=[] if show_btn2 else ["button_hidden"]),  # human_button_2
        gr.update(visible=show_btn3, elem_classes=[] if show_btn3 else ["button_hidden"]),  # human_button_3
        gr.update(visible=show_btn4, elem_classes=[] if show_btn4 else ["button_hidden"]),  # human_button_4
        dropdowns_interactive,  # red_dropdown
        dropdowns_interactive,  # blue_dropdown
        dropdowns_interactive,  # variant_dropdown
    )


def human_move_callback(game, move):
    """
    Callback when a human player makes a move
    """
    current_player = game.players[game.nim_game.player_to_move]
    current_player.make_human_move(game.nim_game, move)
    
    message = message_html(game)
    if_active = gr.Button(interactive=game.nim_game.is_active())
    if not game.nim_game.is_active():
        game.record()
    
    # Check if it's still a human's turn (e.g., human vs human)
    show_row, show_btn1, show_btn2, show_btn3, show_btn4 = check_human_turn(game)
    
    # Disable dropdowns if game has started
    dropdowns_interactive = gr.Dropdown(interactive=not game.nim_game.game_started())
    
    return (
        game,
        game.display(),
        message,
        game.thoughts(RED),
        game.thoughts(BLUE),
        if_active,
        if_active,
        gr.update(visible=show_row),  # Human buttons row
        gr.update(visible=show_btn1, elem_classes=[] if show_btn1 else ["button_hidden"]),  # human_button_1
        gr.update(visible=show_btn2, elem_classes=[] if show_btn2 else ["button_hidden"]),  # human_button_2
        gr.update(visible=show_btn3, elem_classes=[] if show_btn3 else ["button_hidden"]),  # human_button_3
        gr.update(visible=show_btn4, elem_classes=[] if show_btn4 else ["button_hidden"]),  # human_button_4
        dropdowns_interactive,  # red_dropdown
        dropdowns_interactive,  # blue_dropdown
        dropdowns_interactive,  # variant_dropdown
    )


def player_section(name, default):
    """
    Create the left and right sections of the UI
    """
    with gr.Row():
        if name == "Red":
            color = "#8B0000"
            color = f"color:{color};"
            french_name = "🔴 Joueur Rouge"
        elif name == "Blue":
            color = "#00008B"
            color = f"color:{color}"
            french_name = "🔵 Joueur Bleu"
        else:
            color = ""
            french_name = name
            
        gr.HTML(f'<div style="text-align: center;font-size:18px;">{french_name}</div>')
    with gr.Row():
        dropdown = gr.Dropdown(ALL_MODEL_NAMES, value=default, label="LLM", interactive=True)
    with gr.Row():
        gr.HTML('<div style="text-align: center;font-size:16px">Pensées internes</div>')
    with gr.Row():
        thoughts = gr.HTML(label="Pensées")
    return thoughts, dropdown


def make_display():
    """
    The Gradio UI to show the Game, with event handlers
    """
    with gr.Blocks(
        title="La confrontation des LLM au jeu de Nim.",
    ) as blocks:
        game = gr.State()

        with gr.Tabs():
            with gr.TabItem("Partie"):
                with gr.Row():
                    gr.HTML(
                        '<div style="text-align: center;font-size:24px">La confrontation des LLM au jeu de Nim.</div>'
                    )
                with gr.Row():
                    gr.HTML(
                        '<div style="text-align: center;font-size:16px;margin:10px 0px">'
                        '<strong>Règles :</strong> Le jeu de Nim commence avec 21 bâtonnets. '
                        'Chaque joueur retire à tour de rôle un certain nombre de bâtonnets. '
                        'Le joueur qui prend le dernier bâtonnet gagne la partie.<br/>'
                        '<strong>Normal :</strong> Retirer 1 ou 2 bâtonnets.<br/>'
                        '<strong>Variante A :</strong> Si le nombre de bâtonnets est pair: 1, 2 ou 4 bâtonnets ; si impair: 1, 3 ou 4 bâtonnets.<br/>'
                        '<strong>Variante B :</strong> Retirer 1, 2 ou 3 bâtonnets. Il ne peut pas y avoir 2 tours consécutifs où le meme nombre de baguette est retiré.'
                        '</div>'
                    )
                with gr.Row():
                    with gr.Column(scale=1):
                        pass
                    with gr.Column(scale=2):
                        with gr.Row():
                            variant_dropdown = gr.Dropdown(
                                choices=[
                                    ("Normal", "normal"),
                                    ("Variante A", "a"),
                                    ("Variante B", "b"),
                                ],
                                value="normal",
                                label="Variante du jeu",
                                interactive=True
                            )
                    with gr.Column(scale=1):
                        pass
                with gr.Row():
                    with gr.Column(scale=1):
                        pass
                        red_thoughts, red_dropdown = player_section("Red", ALL_MODEL_NAMES[0])
                    with gr.Column(scale=2):
                        with gr.Row():
                            message = gr.HTML(
                                '<div style="text-align: center;font-size:18px">The matchsticks</div>'
                            )
                        with gr.Row():
                            board_display = gr.HTML()
                        # with gr.Row(visible=True) as human_move_label: # Embed Row-Column-Row to be able to show all options in 1 line
                        #     gr.HTML('<strong>Choisissez votre mouvement :</strong>')
                        with gr.Row(visible=False) as human_move_row: # Embed Row-Column-Row to be able to show all options in 1 line
                            with gr.Column():
                                with gr.Row():
                                    gr.HTML('<strong>Choisissez votre mouvement :</strong>')
                                with gr.Row():
                                    human_button_1 = gr.Button("1", variant="primary", scale=1, visible=False)
                                    human_button_2 = gr.Button("2", variant="primary", scale=1, visible=False)
                                    human_button_3 = gr.Button("3", variant="primary", scale=1, visible=False)
                                    human_button_4 = gr.Button("4", variant="primary", scale=1, visible=False)
                                    
                        with gr.Row():
                            move_button = gr.Button("Prochain coup", scale=1)
                            run_button = gr.Button("Lancer la partie", variant="primary", scale=1)
                            reset_button = gr.Button("Recommencer", variant="stop", scale=1)

                        with gr.Row():
                            pass
                            gr.HTML(
                                '<div style="text-align: center;font-size:16px">Voir le <a href="https://github.com/a3jeu/nim-llm-game" style="padding: 0;">dépôt</a></div>'
                            )

                    with gr.Column(scale=1):
                        pass
                        blue_thoughts, blue_dropdown = player_section(
                            "Blue", ALL_MODEL_NAMES[1]
                        )
            with gr.TabItem("Classement") as leaderboard_tab:
                with gr.Row():
                    with gr.Column(scale=1):
                        ratings_df = gr.Dataframe(
                            headers=["Player", "ELO", "Normal", "Variante A", "Variante B"],
                            label="Classements ELO",
                            column_widths=[3, 1, 2, 2, 2],
                            wrap=True,
                            col_count=5, # column_count with gradio 
                            row_count=15,
                            max_height=800,
                            elem_classes=["dataframe-fix"],
                        )
                    with gr.Column(scale=1):
                        results_df = gr.Dataframe(
                            headers=["Date", "Variante", "Joueur rouge", "Joueur bleu", "Gagnant"],
                            label="Historique des parties",
                            column_widths=[2, 2, 2, 2, 1],
                            wrap=True,
                            col_count=5, # column_count with gradio 
                            row_count=10,
                            max_height=800,
                            elem_classes=["dataframe-fix"],
                        )
                with gr.Row():
                    gr.HTML(
                        '<div style="text-align: center;font-size:16px"><a href="https://github.com/a3jeu/nim-llm-game" style="padding: 0;">Cloner</a> le dépôt</div>'
                    )

        blocks.load(
            load_callback,
            inputs=[red_dropdown, blue_dropdown, variant_dropdown],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                reset_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )
        move_button.click(
            move_callback,
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )
        red_dropdown.change(
            red_model_callback, 
            inputs=[game, red_dropdown], 
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ]
        )
        blue_dropdown.change(
            blue_model_callback, 
            inputs=[game, blue_dropdown], 
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ]
        )
        variant_dropdown.change(
            variant_callback,
            inputs=[game, variant_dropdown],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ]
        )
        run_button.click(
            run_callback,
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                reset_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )
        reset_button.click(
            load_callback,
            inputs=[red_dropdown, blue_dropdown, variant_dropdown],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                reset_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )
        
        # Event handlers for human move buttons
        human_button_1.click(
            lambda g: human_move_callback(g, 1),
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )
        
        human_button_2.click(
            lambda g: human_move_callback(g, 2),
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )
        
        human_button_3.click(
            lambda g: human_move_callback(g, 3),
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )
        
        human_button_4.click(
            lambda g: human_move_callback(g, 4),
            inputs=[game],
            outputs=[
                game,
                board_display,
                message,
                red_thoughts,
                blue_thoughts,
                move_button,
                run_button,
                human_move_row,
                human_button_1,
                human_button_2,
                human_button_3,
                human_button_4,
                red_dropdown,
                blue_dropdown,
                variant_dropdown,
            ],
        )

        leaderboard_tab.select(
            leaderboard_callback, inputs=[game], outputs=[results_df, ratings_df]
        )

    return blocks