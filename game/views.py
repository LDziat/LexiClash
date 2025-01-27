from django.shortcuts import render, redirect, get_object_or_404
from .models import BoardTile, PlayerProfile, Tile
from random import randrange, choice
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.db import transaction
import ast
from math import sqrt
from .word_dict import w_dict
from typing import List, Optional, Dict
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.template.loader import render_to_string

# views.py
from django.shortcuts import render

alphas = [
    "A", "A", "A", "A", "A", "A", "A", 
    "B", "B",
    "C", "C",
    "D", "D", "D", "D",
    "E", "E", "E", "E", "E", "E", "E", "E", "E", "E", 
    "F", "F",
    "G", "G", "G",
    "H", "H",
    "I", "I", "I", "I", "I", "I", "I", 
    "J",
    "K",
    "L", "L", "L", "L",
    "M", "M",
    "N", "N", "N", "N", "N", "N",
    "O", "O", "O", "O", "O", "O", "O", 
    "P", "P",
    "Q",
    "R", "R", "R", "R", "R", "R",
    "S", "S", "S", "S",
    "T", "T", "T", "T", "T", "T",
    "U", "U", "U", "U",
    "V", "V",
    "W", "W",
    "X",
    "Y", "Y",
    "Z"
]

word_dict = w_dict()

from typing import List, Dict, Optional
from .models import Tile

def get_tile_effect(x, y):
    """
    Determines the special effect of a tile based on its x, y position.

    Args:
        x (int): The x-coordinate of the tile.
        y (int): The y-coordinate of the tile.

    Returns:
        str: The special effect of the tile (e.g., "double-letter", "triple-word") or None if no effect.
    """
    if x % 10 == 0 and y % 10 == 0:
        return "triple-word"
    if x % 12 == 0 and y % 12 == 0:
        return "double-word"
    if (x % 8 == 0 and y % 4 == 0) or (x % 4 == 0 and y % 8 == 0):
        return "triple-letter"
    if (x % 16 == 0 and y % 4 == 0) or (x % 4 == 0 and y % 16 == 0) or (x % 6 == 0 and y % 6 == 0):
        return "double-letter"
    return None

def get_words_from_tiles(tiles: List[Tile], start_tiles: List[Tile], profile=None) -> Dict[str, List[str]]:
    """
    Reads the words horizontally and vertically from a list of placed tiles, starting from each given tile in start_tiles.

    Args:
        tiles (List[Tile]): List of all tiles currently placed on the board.
        start_tiles (List[Tile]): List of tiles from which we start reading words.

    Returns:
        dict: Dictionary containing lists of horizontal and vertical words if they exist.
    """
    if not start_tiles:
        return {'horizontal': [], 'vertical': [], 'bonus': []}

    # Create a dictionary of relevant tiles for quick lookup
    tile_dict = {(tile.x, tile.y): tile for tile in tiles if tile.tile.owner == profile or tile.tile.mode == 'filled'}

    # Initialize result dictionary
    words = {'horizontal': [], 'vertical': [], 'bonus': []}

    def collect_word_in_direction(start, delta_x, delta_y) -> Optional[str]:
        """Collects a word in the given direction starting from the tile."""
        if not start:
            return None

        dub_word = trip_word = False
        word = []
        x, y = start.x, start.y

        # Move backwards to the start of the word
        while (x - delta_x, y - delta_y) in tile_dict:
            x -= delta_x
            y -= delta_y

        # Collect letters and bonuses while moving forward
        while (x, y) in tile_dict:
            tile = tile_dict[(x, y)]
            word.append(tile.tile.letter)
            effect = get_tile_effect(x, y)
            if effect:
                if effect == 'double-letter':
                    words['bonus'].append(f"${tile.tile.letter}")
                elif effect == 'triple-letter':
                    words['bonus'].append(f"${tile.tile.letter * 2}")
                elif effect == 'double-word':
                    dub_word = True
                elif effect == 'triple-word':
                    trip_word = True
            x += delta_x
            y += delta_y

        # Handle word-level bonuses
        if dub_word:
            words['bonus'].append(f"${''.join(word)}")
        if trip_word:
            words['bonus'].append(f"${''.join(word) * 2}")

        return ''.join(word) if len(word) > 1 else None

    # Iterate over start tiles and collect words
    for start_tile in start_tiles:
        try:
            st_tile = BoardTile.objects.get(tile=start_tile['id'])
        except BoardTile.DoesNotExist:
            continue  # Skip if the start tile does not exist

        # Get horizontal and vertical words
        horizontal_word = collect_word_in_direction(st_tile, delta_x=1, delta_y=0)
        if horizontal_word:
            words['horizontal'].append(horizontal_word)

        vertical_word = collect_word_in_direction(st_tile, delta_x=0, delta_y=1)
        if vertical_word:
            words['vertical'].append(vertical_word)

    # Remove duplicates and return results
    words['horizontal'] = list(set(words['horizontal']))
    words['vertical'] = list(set(words['vertical']))
    words['bonus'] = list(set(words['bonus']))

    return words

def score_word(word):
    point_map = {
        'A': 1, 'B': 3, 'C': 3, 'D': 2, 'E': 1, 'F': 4, 'G': 2, 'H': 4,
        'I': 1, 'J': 8, 'K': 5, 'L': 1, 'M': 3, 'N': 1, 'O': 1, 'P': 3,
        'Q': 10, 'R': 1, 'S': 1, 'T': 1, 'U': 1, 'V': 4, 'W': 4, 'X': 8,
        'Y': 4, 'Z': 10, '$': 0,
    }
    return sum(point_map.get(char, 0) for char in word.upper())



def prescore(dic_h_v):
    if not dic_h_v:
        return 0

    retscore = sum(
        score_word(word)
        for key in ['horizontal', 'vertical', 'bonus']
        for word in (dic_h_v.get(key) or [])
    )
    return retscore


def tilegen(x=0, y=0, user=None, zoom=12):
    """
    Generates a dictionary of tiles within a specified range.

    Args:
        x (int): Starting x-coordinate.
        y (int): Starting y-coordinate.
        user: The user object (for authentication).
        zoom (int): The range to generate tiles.

    Returns:
        dict: A dictionary with (x, y) as keys and tile objects as values.
    """
    ret_dict = {}
    x = int(x)
    y = int(y)

    # Fetch relevant BoardTile objects in a single query
    relevant_tiles = BoardTile.objects.filter(
        x__gte=x, x__lt=x + zoom, y__gte=y, y__lt=y + zoom
    ).select_related('tile')

    user_profile = (
        PlayerProfile.objects.get(user=user) if user and user.is_authenticated else None
    )

    for tile in relevant_tiles:
        tile.tile.get_points()  # Perform tile processing
        key = (tile.x, tile.y)

        # Add tile based on mode and ownership conditions
        if tile.tile.mode == 'placing' and user_profile and tile.tile.owner == user_profile:
            ret_dict[key] = tile.tile
        elif tile.tile.mode != 'placing':
            ret_dict[key] = tile.tile

    return ret_dict



def tile_placing_logic(tile, x, y, profile):
    """
    Handles the logic for placing a tile on the board.

    Args:
        tile (Tile): The tile to be placed.
        x (int): The x-coordinate where the tile is placed.
        y (int): The y-coordinate where the tile is placed.
        profile (PlayerProfile): The profile of the player attempting to place the tile.

    Returns:
        str: Error message if tile placement is invalid, otherwise None.
    """
    # Check if a conflicting tile already exists
    if BoardTile.objects.filter(
        x=x, y=y, tile__mode__in=['filled', 'placing'], tile__owner=profile
    ).exists():
        return "Tile already placed here with mode 'filled' or by the current user."

    # Save the new tile and create a BoardTile object
    tile.save()
    BoardTile.objects.create(x=x, y=y, tile=tile)

    return None


from django.db import transaction

def newtile(player_profile):
    """
    Creates a new tile for the given player profile.

    Args:
        player_profile (PlayerProfile): The profile of the player receiving the new tile.

    Returns:
        Tile: The newly created tile object.
    """
    with transaction.atomic():  # Ensures the operations are performed atomically
        # Create and save the tile in a single step
        tile = Tile.objects.create(
            letter=choice(alphas),
            mode='holding',
            owner=player_profile
        )
        tile.get_points()  # Calculate points if required
        tile.save()  # Save any updates made in get_points() (if necessary)

    return tile


def board_view(request, center_x=None, center_y=None):
    """
    Renders the game board based on user profile and tile placement.

    Args:
        request (HttpRequest): The request object containing user info.
        center_x (int, optional): X-coordinate for board center.
        center_y (int, optional): Y-coordinate for board center.

    Returns:
        HttpResponse: Rendered game board HTML.
    """
    user = request.user
    profile = None
    zoom = 12
    uscore = 0
    handsize = 12
    center_x = int(center_x or 0)
    center_y = int(center_y or 0)

    # User is authenticated: Get profile and update coordinates
    if user.is_authenticated:
        profile = PlayerProfile.objects.get(user=user)
        zoom = profile.zoom
        uscore = profile.score
        if center_x == 0 and center_y == 0:
            center_x, center_y = profile.lastx, profile.lasty
        else:
            profile.lastx, profile.lasty = center_x, center_y
            profile.save()

    # Generate board tiles and player hand
    tiles = tilegen(center_x, center_y, user, zoom)
    user_tiles = []

    if user.is_authenticated:
        while len(profile.current_hand) < handsize:
            profile.add_tile_to_hand(newtile(profile))
        user_tiles = profile.current_hand

        # Manage tiles in placing mode
        placing_tiles = [
            tile for tile in profile.current_hand if tile.get('mode') == 'placing'
        ]
        board_tiles = []

        for tile in placing_tiles:
            try:
                board_tile = BoardTile.objects.get(tile=tile['id'])
                board_tiles.append(board_tile)
            except BoardTile.DoesNotExist:
                tile['mode'] = 'holding'
                profile.save()

        # Get words from placed tiles
        all_tiles = BoardTile.objects.all()
        words = get_words_from_tiles(all_tiles, placing_tiles, profile)
    else:
        # Handle unauthenticated users
        user_tiles = [newtile(None) for _ in range(handsize)]
        words = {'horizontal': [], 'vertical': [], 'bonus': []}

    # Prepare board data for rendering
    board_size = zoom - 1
    board = [
        [
            tiles.get((x + center_x, y + center_y), None)
            for x in range(board_size)
        ]
        for y in range(board_size)
    ]

    context = {
        'board': board,
        'bsiz': board_size,
        'center_x': center_x,
        'center_y': center_y,
        'user_tiles': user_tiles,
        'user': user,
        'hword': words['horizontal'],
        'vword': words['vertical'],
        'score': uscore,
        'prescore': prescore(words),
    }
    return render(request, 'game/board.html', context)

@login_required
def zoom_view(request, level):
    """
    Adjusts the zoom level for the player's profile and redirects to the updated board view.

    Args:
        request (HttpRequest): The request object containing user info.
        level (int): The zoom adjustment value, positive or negative.

    Returns:
        HttpResponseRedirect: Redirect to the board view with updated zoom and coordinates.
    """
    # Retrieve the player's profile
    profile = PlayerProfile.objects.get(user=request.user)
    
    # Adjust the zoom level
    old_zoom = profile.zoom
    new_zoom = profile.zoom + int(level)
    new_zoom = max(5, min(new_zoom, 37))  # Clamp zoom between 5 and 37
    if new_zoom % 2 != 0:
        new_zoom += 1  # Ensure zoom is always even

    profile.zoom = new_zoom
    profile.save()

    # Update the coordinates to center the board correctly
    if new_zoom != old_zoom:
        center_x = profile.lastx - (int(level) // 2)
        center_y = profile.lasty - (int(level) // 2)
        # Redirect to the board view with updated center coordinates
        return redirect('board_view', center_x, center_y)
    else:
        # Redirect to the board view with original center coordinates
        return redirect('board_view', profile.lastx, profile.lasty)

def dashboard_view(request):
    profile = PlayerProfile.objects.get(user=request.user)
    cooldown_remaining = profile.get_cooldown_time()
    return render(request, 'game/dashboard.html', {'cooldown_remaining': cooldown_remaining})


def get_updated_board(center_x, center_y, user):
    profile = PlayerProfile.objects.get(user=user)
    zoom = profile.zoom
    tiles = tilegen(center_x, center_y, user, zoom)
    board_size = zoom - 1
    board = [
        [
            tiles.get((x + center_x, y + center_y), None)
            for x in range(board_size)
        ]
        for y in range(board_size)
    ]
    return board

@login_required
def update_tile(request):
    user = request.user
    if request.method == 'POST':
        tile_id = request.POST.get('tile')
        if tile_id is not None:
            # Log tile_id for debugging
            x, y = map(int, tile_id.split(','))
            # Perform necessary actions with x, y
            updated_board = get_updated_board(center_x=x, center_y=y, user=user)
            return JsonResponse({
                'board_html': render_to_string('dynamic_board.html', {'board': updated_board})
            })
        else:
            return JsonResponse({'error': 'Tile ID is missing'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)






def place_tile(request):
    try:
        if request.method == "POST":
            position = request.POST.get('tile_position')
            try:
                user_tile = ast.literal_eval(request.POST.get('user_tile'))
            except:
                user_tile = None
            profile = PlayerProfile.objects.get(user=request.user)
            tile = Tile.objects.filter(id=user_tile['id']).first()
            if not position or not user_tile:
                return redirect("home")
            # Parse the position from the button clicked
            x, y = map(int, position.split(','))
            # Here you would update your game state with the new tile
            # Placing logic returns None on success
            fail_place = tile_placing_logic(tile, x, y, profile)
            if fail_place == None: # Don't mess with player hand if tile placement failed
                inter_dic = tile.to_dict()
                inter_dic['mode'] = 'holding'                   # This lets us find the old version of the tile
                profile.current_hand[profile.current_hand.index(inter_dic)]['mode']='placing'
                profile.placed_tiles.append(inter_dic)
                tile.mode='placing'
                tile.owner = profile
                tile.save()
                profile.save()
            # Logic to place the tile on the board (update your game state here)
            # Redirect back to the board view
            return redirect('board_view', center_x=int(x-((profile.zoom/2)-1)), center_y=int(y-((profile.zoom/2)-1)))
        return redirect('home')
    except Exception as e:
        if "SimpleLazyObject" not in str(e):    # Ignoring a known common warning
            print("Error:", e)
        position = request.POST.get('tile_position')
        zoom_off = 5
        if request.user.is_authenticated == True:
            profile = PlayerProfile.objects.get(user=request.user)
            zoom_off = int((profile.zoom/2)-1)
        x, y = map(int, position.split(','))
        return redirect('board_view', center_x=int(x-zoom_off), center_y=int(y-zoom_off))


@login_required
def undo_tile(request):
    profile = PlayerProfile.objects.get(user=request.user)
    retx = 5
    rety = 5
    
    if profile.placed_tiles:
        # Move the last placed tile to history
        last_tile = profile.placed_tiles.pop()  # Remove last tile from placed
        index = next((i for i, tile in enumerate(profile.current_hand) if tile['id'] == last_tile['id']), None)
        if index is not None:
            # Set mode to 'holding' for the found tile
            profile.current_hand[index]['mode'] = 'holding'
            profile.save()
        b_tile = BoardTile.objects.get(tile=last_tile['id'])
        retx = b_tile.x
        rety = b_tile.y
        tile = Tile.objects.get(id=last_tile['id'])
        b_tile.delete()
        tile.mode = 'holding'
        tile.save()
        profile.placed_tiles_history.append(last_tile)  # Add to history

    profile.save()
    return redirect('board_view', int(retx-((profile.zoom/2)-1)), int(rety-((profile.zoom/2)-1)))  # Redirect to the game board page

@login_required
def clear_placed_tiles(request):
    profile = PlayerProfile.objects.get(user=request.user)
    
    tiles = profile.current_hand
    # Move all placed tiles to history
    placed_tiles = BoardTile.objects.filter(tile__mode='placing').filter(tile__owner=profile)
    #profile.placed_tiles.clear()  # Clear placed tiles
    for tile in placed_tiles:
        inter_dic = tile.tile.to_dict()
        try:
            profile.current_hand[profile.current_hand.index(inter_dic)]['mode']='holding'
        except Exception as e:
            if "SimpleLazyObject" not in str(e):    # Ignoring a known common warning
                print("Error:", e)
        tile.tile.mode='holding'
        tile.tile.save()
        tile.delete()
        profile.save()


    profile.save()
    return redirect('home')  # Redirect to the game board page

def check_words(wordlist):
    for word in wordlist:
        if word.upper() in word_dict:
            None
        elif word[0] == "$":
            None
        else:
            return False
    return True
        

@login_required
def submit_tiles(request):
    profile = PlayerProfile.objects.get(user=request.user)
    x, y = 0, 0

    # User's placed tiles
    placed_tiles = BoardTile.objects.filter(tile__mode='placing', tile__owner=profile)
    p_tiles = [board_tile.tile.to_dict() for board_tile in placed_tiles]
    all_tiles = BoardTile.objects.all()

    # Check if there are any tiles already in play
    existing_tiles = BoardTile.objects.exclude(tile__mode='placing')

    if existing_tiles.exists():
        # Ensure placed tiles are adjacent to at least one existing tile
        adjacent_to_existing = False
        for tile in placed_tiles:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Check all 4 directions
                adjacent_x = tile.x + dx
                adjacent_y = tile.y + dy
                if existing_tiles.filter(x=adjacent_x, y=adjacent_y).exists():
                    adjacent_to_existing = True
                    break
            if adjacent_to_existing:
                break

        if not adjacent_to_existing:
            return redirect('clear_placed_tiles')  # Invalid move, no adjacency
    else:
        # If no tiles are in play, ensure the current move is the starting move
        if len(placed_tiles) == 0:
            return redirect('clear_placed_tiles')  # Invalid move, no starting tiles

    # Generate words and validate them
    words = get_words_from_tiles(all_tiles, p_tiles, profile)
    words = list(set(words['horizontal'])) + list(set(words['vertical'])) + list(set(words['bonus']))

    if check_words(words):  # Validate words
        profile.placed_tiles.clear()
        for word in words:
            # Score word
            wordscore = score_word(word)  # Function to calculate score
            profile.played_words.append(word)
            profile.score += wordscore
            profile.word_count += 1

        # Convert profile.current_hand to a list of dictionaries for easier lookup
        current_hand = list(profile.current_hand)

        # Update placed tiles and hand
        for tile in placed_tiles:
            inter_dic = tile.tile.to_dict()

            try:
                # Find the index once, then delete by index
                index = current_hand.index(inter_dic)
                # Mark as filled in current_hand
                current_hand[index]['mode'] = 'filled'
                # Remove from current_hand
                del current_hand[index]
            except ValueError:
                print("ValueError: Tile not found in current_hand, possibly already filled")

            # Update tile properties
            tile.tile.mode = 'filled'
            tile.tile.save()
            x, y = tile.x, tile.y

            tiles_to_update = BoardTile.objects.filter(x=x, y=y, tile__mode='placing').exclude(tile__owner=profile)
            for board_tile in tiles_to_update:
                board_tile.tile.owner.set_tile_mode(board_tile.tile, 'holding')
                board_tile.tile.mode = 'holding'
                board_tile.tile.save()
                board_tile.delete()
            tile.save()

        # Assign modified current_hand back to profile and save once
        profile.current_hand = current_hand
        profile.save()

    else:
        return redirect('clear_placed_tiles')  # Invalid words

    # Redirect to the game board page
    return redirect('board_view', center_x=int(x - ((profile.zoom / 2) - 1)), center_y=int(y - ((profile.zoom / 2) - 1)))

@login_required
def swap_tiles_view(request):
    profile = PlayerProfile.objects.get(user=request.user)
    
    if request.method == "POST":
        # Get the IDs of selected tiles to swap
        selected_tile_ids = request.POST.getlist("swap_tiles")
        
        # Filter out the tiles in current hand that are selected and not in placing mode
        tiles_to_swap = [
            tile for tile in profile.current_hand
            if str(tile["id"]) in selected_tile_ids and tile.get("mode") != "placing"
        ]

        # Remove selected tiles from the current hand
        profile.current_hand = [
            tile for tile in profile.current_hand
            if str(tile["id"]) not in selected_tile_ids or tile.get("mode") == "placing"
        ]

        # Add new random tiles for each removed tile
        new_tiles = [newtile(profile) for _ in tiles_to_swap]
        profile.current_hand.extend(new_tile.to_dict() for new_tile in new_tiles)

        # Save changes to the profile
        profile.save()

        # Redirect back to the board view
        return redirect("board_view", profile.lastx, profile.lasty)

    # Exclude tiles with 'placing' mode from the list shown for swapping
    current_hand = [tile for tile in profile.current_hand]# if tile.get("mode") != "placing"]

    # Render the swap tile page with checkboxes for non-placing tiles
    return render(request, "game/swap_tiles.html", {"current_hand": current_hand})

def leaderboard(request):
    # Fetch all player profiles and order by score in descending order
    mode = '-score'
    leaderboard = PlayerProfile.objects.all().order_by(mode)[:50]  # Top 50 players
    
    return render(request, 'game/leaderboard.html', {'leaderboard': leaderboard})


def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            PlayerProfile.objects.create(user=user)  # Create associated PlayerProfile
            login(request, user)
            return redirect("home")  # Adjust this to the desired redirect
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect('home')  # Redirect to the login page or any other page



