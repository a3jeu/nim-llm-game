import json
import random
from arena.llm import LLM

from arena.nim_game import RED, BLUE


class HumanTurnException(Exception):
    """Exception raised when it's a human player's turn"""
    def __init__(self, valid_moves):
        """
        Store valid moves and build the exception message.
        """
        self.valid_moves = valid_moves
        super().__init__(f"Human player needs to choose from: {valid_moves}")


class Player:
    def __init__(self, model, color):
        """
        Initialize a player and its LLM client.
        """
        self.model = model
        self.color = color
        self.llm = LLM.create(self.model)
        
        # Handle llm response
        self.evaluation = ""
        self.threats = ""
        self.opportunities = ""
        self.strategy = ""
        self.move_remove = None
        
    def system(self, nim_game):
        """
        Build the system prompt for the LLM.
        """
        legal_moves_str = ", ".join(map(str, nim_game.valid_moves()))
        prompt = f"""You are an expert player in the game of Nim.
There is a single pile of sticks. On your turn, you must remove between {legal_moves_str} sticks.
You MUST remove at least 1 stick.
The player who takes the LAST stick WINS.
You play optimally and rationally to maximize your chance of winning.
You should respond in JSON, and only in JSON, according to this spec:

{{
    "evaluation": "brief assessment of the current game state",
    "threats": "any immediate risks if you play poorly",
    "opportunities": "any winning patterns or advantages in the current position",
    "strategy": "concise reasoning behind the chosen move",
    "move_remove": "number of sticks to remove, must be one of: {legal_moves_str}"
}}
"""
        return prompt
    
    def user(self, nim_game):
        """
        Build the user prompt for the LLM.
        """
        legal_moves_str = ", ".join(map(str, nim_game.valid_moves()))
        prompt = f"""It is your turn to play. Choose your move. 
There are {nim_game.n} sticks remaining.

Now with this in mind, make your decision. Respond only in JSON strictly according to this spec:
{{
    "evaluation": "brief assessment of the current game state",
    "threats": "any immediate risks if you play poorly",
    "opportunities": "any winning patterns or advantages in the current position",
    "strategy": "concise reasoning behind the chosen move",
    "move_remove": "number of sticks to remove, must be one of: {legal_moves_str}"
}}

For example, the following could be a response:

{{
  "evaluation": "The pile size allows forcing a losing position for the opponent.",
  "threats": "Removing the wrong number of sticks would allow the opponent to control the endgame.",
  "opportunities": "By leaving a multiple of 3, the opponent is forced into a losing sequence.",
  "strategy": "Remove 2 sticks to leave 3, which is a losing position for the next player.",
  "move_remove": "{random.choice(nim_game.valid_moves())}"
}}

Now make your decision.
You must remove a number of sticks from the pile between {legal_moves_str}.
"""
        return prompt
    
    def pick(self, nim_game):
        """
        Get a move from the player and apply it to the game.
        """
        # Check if this is a human player
        if self.model == "Humain":
            # Raise exception so the UI can handle human input
            raise HumanTurnException(nim_game.valid_moves())
        
        system_prompt = self.system(nim_game)
        user_prompt = self.user(nim_game)
        
        response = self.llm.send(system_prompt, user_prompt)
        
        try:
            self.process_move(response, nim_game)
        except Exception as e:
            print(f"Exception during move processing: {e}")
            # Print Prompts for debugging
            print("System Prompt:")
            print(system_prompt)
            print("User Prompt:")
            print(user_prompt)
        
    def process_move(self, response, nim_game):
        """
        Parse the model response and update game state.
        """
        print(response)
        try:
            result = json.loads(response)
            move_remove = int(result.get("move_remove"))
            
            # Check if move is valid
            if move_remove not in nim_game.valid_moves():
                raise ValueError(f"Invalid move: {move_remove}")
            nim_game.pick(move_remove)
            
            self.evaluation = result.get("evaluation", "")
            self.threats = result.get("threats", "")
            self.opportunities = result.get("opportunities", "")
            self.strategy = result.get("strategy", "")
            self.move_remove = move_remove
        except Exception as e:
            print(f"Exception {e}")
            # If invalid, set user who just played as loser
            nim_game.forfeited = True
            nim_game.winner = BLUE if self.color == RED else RED
            
    def thoughts(self):
        """
        Return HTML to describe the inner thoughts
        """
        result = '<div style="text-align: left;font-size:14px"><br/>'
        result += f"<b>Évaluation:</b><br/>{self.evaluation}<br/><br/>"
        result += f"<b>Menaces:</b><br/>{self.threats}<br/><br/>"
        result += f"<b>Opportunités:</b><br/>{self.opportunities}<br/><br/>"
        result += f"<b>Stratégie:</b><br/>{self.strategy}<br/><br/>"
        result += f"<b>Nombre de bâtonnets retirés:</b><br/>{self.move_remove}<br/>"
        result += "</div>"
        return result
    
    def switch_model(self, new_model_name: str):
        """
        Change the underlying LLM to the new model
        """
        self.model = new_model_name
        self.llm = LLM.create(new_model_name)
    
    def make_human_move(self, nim_game, move_remove):
        """
        Process a move made by a human player
        """
        self.evaluation = "Mouvement choisi par un joueur humain"
        self.threats = "N/A"
        self.opportunities = "N/A"
        self.strategy = f"Le joueur humain a décidé de retirer {move_remove} bâtonnet(s)"
        self.move_remove = move_remove
        nim_game.pick(move_remove)
        
            
        
