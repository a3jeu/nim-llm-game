import logging
import os
import math
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict



@dataclass
class Result:
    red_player: str
    blue_player: str
    variant: str
    red_won: bool
    blue_won: bool
    date: datetime


DB_FILE = "nim_games.db"


def _init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema if it doesn't exist"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            red_player TEXT NOT NULL,
            blue_player TEXT NOT NULL,
            variant TEXT NOT NULL,
            red_won INTEGER NOT NULL,
            blue_won INTEGER NOT NULL,
            date TEXT NOT NULL
        )
    """)
    conn.commit()


def _get_db() -> Optional[sqlite3.Connection]:
    """Helper function to get SQLite database connection with error handling"""
    try:
        conn = sqlite3.connect(DB_FILE)
        _init_db(conn)
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to database: {e}")
        return None


def record_game(result: Result) -> bool:
    """
    Store the results in the database, if database is available.
    Returns True if successful, False if database is unavailable.
    """
    conn = _get_db()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO games (red_player, blue_player, variant, red_won, blue_won, date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            result.red_player,
            result.blue_player,
            result.variant,
            1 if result.red_won else 0,
            1 if result.blue_won else 0,
            result.date.isoformat()
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error("Failed to record a game in the database")
        logging.exception(e)
        if conn:
            conn.close()
        return False


def get_games() -> List[Result]:
    """
    Return all games in the order that they were played.
    Returns empty list if database is unavailable.
    """
    conn = _get_db()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT red_player, blue_player, variant, red_won, blue_won, date
            FROM games
            ORDER BY id
        """)
        
        results = []
        for row in cursor.fetchall():
            results.append(Result(
                red_player=row[0],
                blue_player=row[1],
                variant=row[2],
                red_won=bool(row[3]),
                blue_won=bool(row[4]),
                date=datetime.fromisoformat(row[5])
            ))
        
        conn.close()
        return results
    except Exception as e:
        logging.error("Error getting games")
        logging.exception(e)
        if conn:
            conn.close()
        return []


class EloCalculator:
    def __init__(self, k_factor: float = 32, default_rating: int = 1000):
        """
        Initialize the ELO calculator.

        Args:
            k_factor: Determines how much ratings change after each game
            default_rating: Starting rating for new players
        """
        self.k_factor = k_factor
        self.default_rating = default_rating
        self.ratings: Dict[str, float] = {}

    def get_player_rating(self, player: str) -> float:
        """Get a player's current rating, or default if they're new."""
        return self.ratings.get(player, self.default_rating)

    def calculate_expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate the expected score (win probability) for player A against player B.
        Uses the ELO formula: 1 / (1 + 10^((ratingB - ratingA)/400))
        """
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

    def update_ratings(
        self, player_a: str, player_b: str, score_a: float, score_b: float
    ) -> None:
        """
        Update ratings for two players based on their game outcome.

        Args:
            player_a: Name of first player
            player_b: Name of second player
            score_a: Actual score for player A (1 for win, 0.5 for draw, 0 for loss)
            score_b: Actual score for player B (1 for win, 0.5 for draw, 0 for loss)
        """
        rating_a = self.get_player_rating(player_a)
        rating_b = self.get_player_rating(player_b)

        expected_a = self.calculate_expected_score(rating_a, rating_b)
        expected_b = 1 - expected_a

        # Update ratings using the ELO formula: R' = R + K * (S - E)
        # where R is the current rating, K is the k-factor,
        # S is the actual score, and E is the expected score
        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * (score_b - expected_b)

        self.ratings[player_a] = new_rating_a
        self.ratings[player_b] = new_rating_b


def calculate_elo_ratings(
    results: List[Result], exclude_self_play: bool = True
) -> Dict[str, float]:
    """
    Calculate final ELO ratings for all players based on a list of game results.

    Args:
        results: List of game results, sorted by date
        exclude_self_play: If True, skip games where a player plays against themselves

    Returns:
        Dictionary mapping player names to their final ELO ratings
    """
    calculator = EloCalculator()

    for result in results:
        # Skip self-play games if requested
        if exclude_self_play and result.red_player == result.blue_player:
            continue

        # Convert game result to ELO scores (1 for win, 0.5 for draw, 0 for loss)
        if result.red_won and not result.blue_won:
            red_score, blue_score = 1.0, 0.0
        elif result.blue_won and not result.red_won:
            red_score, blue_score = 0.0, 1.0
        else:
            # Draw (including double-win or double-loss cases)
            red_score, blue_score = 0.5, 0.5

        calculator.update_ratings(
            result.red_player, result.blue_player, red_score, blue_score
        )

    return calculator.ratings


def ratings() -> Dict[str, float]:
    """
    Return the ELO ratings from all prior games in the DB
    """
    games = get_games()
    return calculate_elo_ratings(games)


def ratings_by_variant(variant: str) -> Dict[str, float]:
    """
    Return the ELO ratings for a specific variant from all prior games in the DB
    
    Args:
        variant: The game variant to filter by ('normal', 'a', 'b')
    
    Returns:
        Dictionary mapping player names to their ELO ratings for that variant
    """
    games = get_games()
    filtered_games = [game for game in games if game.variant == variant]
    return calculate_elo_ratings(filtered_games)