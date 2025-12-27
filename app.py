"""
Flask entry-point for the Nim LLM game.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

from arena.game import Game
from arena.llm import LLM
from arena.nim_game import BLUE, RED
from arena.player import HumanTurnException

load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")

_GAMES: dict[str, Game] = {}


def _session_id() -> str:
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid
    return sid


def _get_game() -> Game | None:
    return _GAMES.get(_session_id())


def _set_game(game: Game) -> None:
    _GAMES[_session_id()] = game


def _default_models() -> tuple[str, str]:
    models = LLM.all_model_names()
    if not models:
        return ("Humain", "Humain")
    if len(models) == 1:
        return (models[0], models[0])
    return (models[0], models[1])


def _message_html(game: Game) -> str:
    return f'<div class="status">{game.nim_game.message()}</div>'


def _human_turn(game: Game) -> tuple[bool, list[int]]:
    if not game.nim_game.is_active():
        return False, []
    current_player = game.players[game.nim_game.player_to_move]
    if current_player.model == "Humain":
        return True, game.nim_game.valid_moves()
    return False, []


def _state_payload(game: Game) -> dict:
    show_human, valid_moves = _human_turn(game)
    dropdowns_enabled = not game.nim_game.game_started()
    can_move = game.nim_game.is_active() and not show_human
    can_run = game.nim_game.is_active() and not show_human
    return {
        "board_html": game.display(),
        "message_html": _message_html(game),
        "red_thoughts": game.thoughts(RED),
        "blue_thoughts": game.thoughts(BLUE),
        "show_human": show_human,
        "valid_moves": valid_moves,
        "can_move": can_move,
        "can_run": can_run,
        "dropdowns_enabled": dropdowns_enabled,
        "game_over": not game.nim_game.is_active(),
        "red_model": game.players[RED].model,
        "blue_model": game.players[BLUE].model,
        "variant": game.nim_game.variant,
    }


def _create_game(red_model: str | None, blue_model: str | None, variant: str) -> Game:
    if not red_model or not blue_model:
        default_red, default_blue = _default_models()
        red_model = red_model or default_red
        blue_model = blue_model or default_blue
    return Game(red_model, blue_model, variant=variant)


def _combined_ratings(
    ratings_global: dict[str, float],
    ratings_normal: dict[str, float],
    ratings_a: dict[str, float],
    ratings_b: dict[str, float],
) -> list[list]:
    all_players = set()
    all_players.update(ratings_global.keys())
    all_players.update(ratings_normal.keys())
    all_players.update(ratings_a.keys())
    all_players.update(ratings_b.keys())

    rows = []
    for player in all_players:
        elo_global = int(round(ratings_global.get(player, 1000)))
        elo_normal = int(round(ratings_normal.get(player, 1000)))
        elo_a = int(round(ratings_a.get(player, 1000)))
        elo_b = int(round(ratings_b.get(player, 1000)))
        rows.append([player, elo_global, elo_normal, elo_a, elo_b])

    rows.sort(key=lambda x: x[1], reverse=True)
    return rows


@app.route("/")
def index():
    models = LLM.all_model_names()
    default_red, default_blue = _default_models()
    return render_template(
        "index.html",
        models=models,
        default_red=default_red,
        default_blue=default_blue,
        default_variant="normal",
    )


@app.route("/api/init", methods=["POST"])
def api_init():
    payload = request.get_json(silent=True) or {}
    red_model = payload.get("red_model")
    blue_model = payload.get("blue_model")
    variant = payload.get("variant", "normal")
    game = _create_game(red_model, blue_model, variant)
    _set_game(game)
    return jsonify(_state_payload(game))


@app.route("/api/move", methods=["POST"])
def api_move():
    game = _get_game()
    if not game:
        red_model, blue_model = _default_models()
        game = _create_game(red_model, blue_model, "normal")
        _set_game(game)
    try:
        game.pick()
        if not game.nim_game.is_active():
            game.record()
    except HumanTurnException:
        pass
    return jsonify(_state_payload(game))


@app.route("/api/run", methods=["POST"])
def api_run():
    game = _get_game()
    if not game:
        red_model, blue_model = _default_models()
        game = _create_game(red_model, blue_model, "normal")
        _set_game(game)

    game.reset()
    message_override = ""
    while game.nim_game.is_active():
        try:
            game.pick()
        except HumanTurnException:
            message_override = (
                _message_html(game)
                + "<br/><strong>Auto-run stopped: human player detected. Use single move.</strong>"
            )
            break

    if not game.nim_game.is_active():
        game.record()

    payload = _state_payload(game)
    if message_override:
        payload["message_html"] = message_override
    return jsonify(payload)


@app.route("/api/human-move", methods=["POST"])
def api_human_move():
    payload = request.get_json(silent=True) or {}
    move = int(payload.get("move", 0))
    game = _get_game()
    if not game:
        red_model, blue_model = _default_models()
        game = _create_game(red_model, blue_model, "normal")
        _set_game(game)
    current_player = game.players[game.nim_game.player_to_move]
    if current_player.model == "Humain" and move in game.nim_game.valid_moves():
        current_player.make_human_move(game.nim_game, move)
        if not game.nim_game.is_active():
            game.record()
    return jsonify(_state_payload(game))


@app.route("/api/reset", methods=["POST"])
def api_reset():
    payload = request.get_json(silent=True) or {}
    red_model = payload.get("red_model")
    blue_model = payload.get("blue_model")
    variant = payload.get("variant", "normal")
    game = _create_game(red_model, blue_model, variant)
    _set_game(game)
    return jsonify(_state_payload(game))


@app.route("/api/model", methods=["POST"])
def api_model():
    payload = request.get_json(silent=True) or {}
    player = payload.get("player")
    model = payload.get("model")
    game = _get_game()
    if not game:
        game = _create_game(None, None, "normal")
        _set_game(game)

    if not game.nim_game.game_started() and model:
        if player == "red":
            game.players[RED].switch_model(model)
        elif player == "blue":
            game.players[BLUE].switch_model(model)

    return jsonify(_state_payload(game))


@app.route("/api/variant", methods=["POST"])
def api_variant():
    payload = request.get_json(silent=True) or {}
    variant = payload.get("variant", "normal")
    game = _get_game()
    if not game:
        game = _create_game(None, None, variant)
        _set_game(game)

    if not game.nim_game.game_started():
        game.variant = variant
        game.nim_game.variant = variant

    return jsonify(_state_payload(game))


@app.route("/api/leaderboard", methods=["GET"])
def api_leaderboard():
    records = Game.get_games()
    results_rows = []
    for game in reversed(records):
        if game.red_won:
            winner = "Rouge"
        elif game.blue_won:
            winner = "Bleu"
        else:
            winner = "Nul"
        results_rows.append(
            [
                game.date.replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S"),
                game.variant,
                game.red_player,
                game.blue_player,
                winner,
            ]
        )

    ratings_global = Game.get_ratings()
    ratings_normal = Game.get_ratings_by_variant("normal")
    ratings_a = Game.get_ratings_by_variant("a")
    ratings_b = Game.get_ratings_by_variant("b")
    ratings_rows = _combined_ratings(
        ratings_global, ratings_normal, ratings_a, ratings_b
    )

    return jsonify(
        {
            "results": results_rows,
            "ratings": ratings_rows,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    server_name = os.getenv("SERVER_NAME", "127.0.0.1")
    app.run(host=server_name, port=port, debug=False)
