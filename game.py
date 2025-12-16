# Nim Game - LLM Implementation
class NimGame:
    def __init__(self, n=15, k=3):
        self.n = n
        self.k = k
        self.history = []
        self.current_player = "human"

    def valid_moves(self):
        return list(range(1, min(self.k, self.n) + 1))

    def play(self, move):
        if move not in self.valid_moves():
            raise ValueError("Coup invalide")

        self.n -= move
        self.history.append((self.current_player, move))
        self.current_player = "bot" if self.current_player == "human" else "human"

    def is_over(self):
        return self.n == 0

    def loser(self):
        if not self.is_over():
            return None
        return "human" if self.current_player == "bot" else "bot"
