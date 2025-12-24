# The Nim game implementation

from arena.matchstick_view import display_matchsticks

RED = 1
BLUE = 2
EMPTY = 0

class NimGame:
    """
    Class representing a game of Nim with different variants.
    """
    def __init__(self, variant="normal", n = 21):
        """
        Initialize game state and configuration.
        """
        # variant can be "normal" or "a" or "b"
        self.variant = variant
        self.n = n  # Number of matchsticks
        self.history = []
        self.winner = EMPTY
        self.player_to_move = RED  # RED starts
        self.forfeited = False
        
    def __repr__(self):
        """
        Return HTML for the current matchstick display.
        """
        return display_matchsticks(n=self.n)
    
    def message(self): 
        """
        Return a status message describing the current game state.
        """
        if self.winner and not self.forfeited:
            return f"Le joueur <strong>{'Rouge' if self.winner == RED else 'Bleu'}</strong> a gagné!"
        elif self.forfeited:
            return f"Le joueur <strong>{'Rouge' if self.player_to_move == BLUE else 'Bleu'}</strong> a gagné car <strong>{'Rouge' if self.player_to_move == RED else 'Bleu'}</strong> a fait un coup invalide."
        else:
            return f"Il reste <strong>{self.n}</strong> bâtonnets. C'est au joueur <strong>{'Rouge' if self.player_to_move == RED else 'Bleu'}</strong> de jouer."
    
    def pick(self, taken):
        """
        Apply a move and update the game state.
        """
        # Check if move is valid
        if taken not in self.valid_moves():
            raise ValueError(f"Invalid move: {taken}. Valid moves are: {self.valid_moves()}")
        
        self.n -= taken
        self.history.append(taken)
        if self.check_winner():
            return
        else:
            self.player_to_move = BLUE if self.player_to_move == RED else RED
    
    def valid_moves(self):
        """
        Return the list of valid moves for the current variant.
        """
        # Version de base:
        # -Chaque joueur a la possibilité de piger 1 ou 2 baguette

        # Variante A:
        # -Si le nombre de baguettes restant est pair, le joueur peut retirer 1, 2 ou 4 baguettes. Si le nombre de baguettes est impair, le joueur peut retirer 1, 3 ou 4 baguettes 

        # Variante B:
        # -Chaque joueur a la possibilité de piger 1, 2 ou 3 baguettes. Il ne peut pas y avoir 2 tours consécutifs où le meme nombre de baguette est retiré.
        valid_moves = []
        if self.variant == "normal":
            valid_moves = [1, 2]
        elif self.variant == "a":
            if self.n % 2 == 0:
                valid_moves = [1, 2, 4]
            else:
                valid_moves = [1, 3, 4]
        elif self.variant == "b":
            last_move = self.history[-1] if self.history else None
            for move in [1, 2, 3]:
                if move != last_move:
                    valid_moves.append(move)
                    
        return [move for move in valid_moves if move <= self.n]
        
    def check_winner(self):
        """
        Set and return the winner if the game has ended.
        """
        if self.n == 0:
            self.winner = self.player_to_move
        return self.winner
    
    def is_active(self):
        """
        Returns True if the game is still ongoing.
        """
        return self.winner == EMPTY and not self.forfeited
    
    def game_started(self):
        """
        Returns True if at least one move has been made.
        """
        return len(self.history) > 0
            
