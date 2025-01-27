from django.contrib.auth.models import User
from django.db import models
from uuid import uuid4
from django.utils import timezone

class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)         # User account
    current_hand = models.JSONField(default=list)                       # To store the hand of Tile objects
    played_words = models.JSONField(default=list)                       # To store lists of played Tile objects (list of lists)
    last_played_time = models.DateTimeField(null=True, blank=True)      # Last played date & time (UNUSED) 
    cooldown_remaining = models.IntegerField(default=0)                 # Cooldown in seconds (UNUSED)
    placed_tiles = models.JSONField( default=list, blank=True)          # Store placed tiles as JSON
    placed_tiles_history = models.JSONField( default=list, blank=True)  # History of placed tiles
    zoom = models.IntegerField(default=12)                              # Zoom in amount
    lastx = models.IntegerField(default=0)                              # User's X position on the board
    lasty = models.IntegerField(default=0)                              # User's Y position on the board
    score = models.IntegerField(default=0)                              # User's Score
    word_count = models.IntegerField(default=0)                         # Count of words (Likely inaccurate)


    def get_cooldown_time(self):
        """Calculate the remaining cooldown time."""
        if not self.last_played_time:
            return 0
        elapsed = timezone.now() - self.last_played_time
        return max(0, self.cooldown_remaining - elapsed.total_seconds())

    def add_tile_to_hand(self, tile):
        """Add a Tile object to the current hand."""
        hand = self.current_hand
        hand.append(tile.to_dict())
        self.current_hand = hand
        self.save()

    def delete_tile_from_hand(self, tile):
        """Add a Tile object to the current hand."""
        hand = self.current_hand
        hand.remove(tile.to_dict())
        self.current_hand = hand
        self.save()

    def play_word(self, word_tiles):
        """Add a word to the played_words as a list of Tile objects."""
        words = self.played_words
        word_data = [tile.to_dict() for tile in word_tiles]
        words.append(word_data)
        self.played_words = words
        self.save()

    def set_tile_mode(self, tile, new_mode):
        """
        Update the mode of a Tile object in the current hand.

        Parameters:
        - tile: The Tile object to update.
        - new_mode: The new mode string to set for the tile.
        """
        # Convert tile to dictionary
        tile_dict = tile.to_dict()

        # Iterate over each tile in the current hand to find a match
        hand = self.current_hand
        for t in hand:
            if t['id'] == tile_dict['id']:
                t['mode'] = new_mode
                if t in self.placed_tiles:
                    self.placed_tiles.remove(t)
                break
        
        # Update current hand and save changes
        self.current_hand = hand
        self.save()

    
    def zoom_in(self):
        """Zooms the view in"""
        self.zoom += 1
        self.save()
    def zoom_out(self):
        """Zooms the view out"""
        self.zoom += 1
        self.save()

class Tile(models.Model):
    # A Tile is any tile object, whether held in a player's hand or placed on the board.
    # A Tile object has no position, and its state is controlled entirely by the mode charfield
    letter = models.CharField(max_length=1)                                                     # Letter for tile
    is_blank = models.BooleanField(default=False)                                               # Flag for blank tiles (UNUSED)
    effects = models.JSONField(null=True, blank=True)                                           # For blank tile effects (UNUSED)
    mode = models.CharField(max_length=16)                                                      # Mode: 'holding', 'placing', or 'filled'
    owner = models.ForeignKey(PlayerProfile, on_delete=models.CASCADE, null=True, blank=True)   # Owner of the tile object
    points = models.IntegerField(default=0)                                                     # Point value for tile

    def to_dict(self):
        # Helper method to serialize Tile object as a dictionary.
        # Useful as a management tool for linking BoardTile objects to the correct Tile objects
        return {
            "id": self.id,
            "letter": self.letter,
            "is_blank": self.is_blank,
            "effects": self.effects,
            "mode": self.mode,
            "points": self.points,
        }
    
    def get_points(self):
    # Define the point values for each letter in a dictionary
        point_map = {
            'A': 1, 'B': 3, 'C': 3, 'D': 2,
            'E': 1, 'F': 4, 'G': 2, 'H': 4,
            'I': 1, 'J': 8, 'K': 5, 'L': 1,
            'M': 3, 'N': 1, 'O': 1, 'P': 3,
            'Q': 10, 'R': 1, 'S': 1, 'T': 1,
            'U': 1, 'V': 4, 'W': 4, 'X': 8,
            'Y': 4, 'Z': 10
        }
        self.points = point_map.get(self.letter.upper(), 0)
        self.save()
        # Return the point value for the given letter
        return self.points  # Default to 0 if the letter is not in the dictionary

    

class BoardTile(models.Model):
    # A BoardTile is a Tile object with a position on the game board.
    x = models.IntegerField()                                                               # The X Position of the BoardTile
    y = models.IntegerField()                                                               # The Y Position of the BoardTile
    tile = models.ForeignKey(Tile, on_delete=models.SET_NULL, null=True)                    # Links to a Tile Object
    owner = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)     # The owner of the BoardTile object
