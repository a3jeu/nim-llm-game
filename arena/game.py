from arena.nim_game import NimGame, RED, BLUE
from arena.player import Player
from arena.record import get_games, Result, record_game, ratings, ratings_by_variant
from datetime import datetime
from typing import List
from arena.llm import LLM

class Game:
    """
    A Game consists of a bunch of matchsticks and 2 players
    """
    
    def __init__(self, model_red: str, model_BLUE: str, variant="normal", n=21):
        """
        Initialize this Game; a new nim_game, and new Player objects
        """
        self.variant = variant
        self.n = n
        self.nim_game = NimGame(variant=variant, n=n)
        self.players = {
            RED: Player(model_red, RED),
            BLUE: Player(model_BLUE, BLUE),
        }
        
    def reset(self):
        """
        Restart the game by resetting the nim_game; keep players the same
        """
        self.nim_game = NimGame(variant=self.variant, n=self.n)
        
    def pick(self):
        """
        Let the current player pick a move
        """
        current_player = self.players[self.nim_game.player_to_move]
        current_player.pick(self.nim_game)
        
    def is_active(self):
        """
        Return whether the game is still ongoing
        """
        return not self.nim_game.is_active()
    
    def thoughts(self, player):
        """
        Return the thoughts of the player of the given color
        """
        return self.players[player].thoughts()
    
    def display(self):
        """
        Return HTML to display the current board state
        """
        return self.nim_game.__repr__()
    
    @staticmethod
    def get_games() -> List:
        """
        Return all the games stored in the db
        """
        return get_games()
    
    @staticmethod
    def get_ratings():
        """
        Return the ELO ratings of all players - filter out any models that are not supported
        """
        return {
            model: rating
            for model, rating in ratings().items()
            if model in LLM.all_supported_model_names()
        }
    
    @staticmethod
    def get_ratings_by_variant(variant: str):
        """
        Return the ELO ratings of all players for a specific variant - filter out any models that are not supported
        """
        return {
            model: rating
            for model, rating in ratings_by_variant(variant).items()
            if model in LLM.all_supported_model_names()
        }

    def record(self):
        """
        Store the results of this game in the DB
        """
        red_player = self.players[RED].llm.model_name
        blue_player = self.players[BLUE].llm.model_name
        variant = self.nim_game.variant
        red_won = self.nim_game.winner == RED
        blue_won = self.nim_game.winner == BLUE
        result = Result(red_player, blue_player, variant, red_won, blue_won, datetime.now())
        record_game(result)

    def run(self):
        """
        If being used outside gradio; move and print in a loop
        """
        while self.is_active():
            self.pick()
            print(self.nim_game)