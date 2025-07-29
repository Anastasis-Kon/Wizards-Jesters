import pygame
from game_state import GamePhase
import math

# Colors
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
LIGHT_BLUE = (200, 200, 255)
LIGHT_RED = (255, 200, 200)
LIGHT_YELLOW = (255, 255, 200)
GRAY = (128, 128, 128)
DARK_BLUE = (10, 10, 50)
GREEN_FELT = (0, 100, 0)
DARK_GREEN = (0, 80, 0)
WOOD_BROWN = (139, 69, 19)
SHADOW_COLOR = (0, 0, 0, 100)
SHADOW_COLOR_S = (50, 50, 50, 50)
LIGHT_BLUE_B = (70, 120, 200)
CARD_BACK_COLOR = (30, 60, 150)  # Dark blue
DARK_GREY= (169, 169, 169)
OFF_WHITE=(245,245,220)

show_all_cards = False
show_best_move = False
show_help = False

best_move_suggestion = ""



def draw_board(screen, game):
    """Draw the game board"""
    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont(None, 36)
    small_font = pygame.font.SysFont(None, 24)
    draw_background(screen)
    draw_poker_table(screen)

    show_all_button_rect = draw_show_all_cards_button(screen, small_font)

    show_best_move_button_rect = draw_show_best_move_button(screen, small_font)
    
    auto_play_rect = draw_auto_play_button(screen, small_font, game)

    

    for name, info in game.players.items():
        x, y = info["pos"]

        # Base settings
        radius = 30  # Smaller circle
        border_width = 3  # Slightly thicker border for style

        # Color based on phase and player turn
        color = WHITE
        if game.phase == GamePhase.PLAYING and name == game.player_names[game.current_player_index]:
            color = YELLOW  # Highlight current player
        elif game.phase == GamePhase.BIDDING and name == game.player_names[game.current_player_index]:
            color = LIGHT_BLUE

        # Shadow (for depth)
        shadow_offset = 4
        pygame.draw.circle(screen, (50, 50, 50), (x + shadow_offset, y + shadow_offset), radius + 2)

        # Outer circle (border)
        pygame.draw.circle(screen, BLACK, (x, y), radius + border_width)

        # Inner circle (player chip)
        pygame.draw.circle(screen, color, (x, y), radius)

        # Optional: tiny inner dot for style
        pygame.draw.circle(screen, (200, 200, 200), (x, y), 5)

        # Player name above
        label = font.render(name, True, BLACK)
        screen.blit(label, (x - label.get_width() // 2, y - radius - 35))


        # Bid and tricks won
        if name in game.bids:
            bid_text = small_font.render(f"Bid: {game.bids[name]}", True, WHITE)
            screen.blit(bid_text, (x - bid_text.get_width() // 2, y + 40))
        
        if name in game.tricks_won:
            tricks_text = small_font.render(f"Won: {game.tricks_won[name]}", True, WHITE)
            screen.blit(tricks_text, (x - tricks_text.get_width() // 2, y + 60))
        
        # Cards in hand
        draw_player_cards(screen, game, name, info, small_font)

    # Draw trump card
    draw_trump_card(screen, game, font, small_font)
    
    # Draw played cards in center
    draw_played_cards(screen, game, small_font)
    
    # Draw bidding UI
    if game.phase == GamePhase.BIDDING:
        draw_bid_ui(screen, game)
    
    # Draw game info
    draw_game_info(screen, game,small_font)

    
    draw_scoreboard(screen, game)
    if best_move_suggestion:
        suggestion_text = small_font.render(f"Suggestion: {best_move_suggestion}", True, WHITE)
        screen.blit(suggestion_text, (20, HEIGHT - 60))

    #Draw help box
    draw_help(screen,font,small_font)

    i_text_rect= draw_help_button(screen)

    # Draw message
    if game.message:
        msg = font.render(game.message, True, WHITE)
        screen.blit(msg, (20, HEIGHT - 40))
    return show_all_button_rect, show_best_move_button_rect,auto_play_rect, i_text_rect

def draw_rounded_rect(surface, color, rect, radius=10, border_color=None, border_width=2):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)


def draw_help(screen,font,tiny_font):

    WIDTH, HEIGHT = screen.get_size()
    if show_help:
        # Semi-transparent overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # Black with alpha
        screen.blit(overlay, (0, 0))

        # Instruction box
        help_rect = pygame.Rect(WIDTH // 2 - 400, HEIGHT // 2 - 300, 820, 550)
        draw_rounded_rect(screen, OFF_WHITE, help_rect, radius=12, border_color=BLACK)

        # Title
        help_title = font.render("How to Play Wizard", True, BLACK)
        screen.blit(help_title, (help_rect.centerx - help_title.get_width() // 2, help_rect.top + 20))

        # Instructions
        instructions = [
    "• Each round, players are dealt an increasing number of cards from a special Wizard deck.",
    "• After the deal, each player bids how many tricks (hands) they expect to win that round.",
    "• The top card of the undealt deck is revealed to determine the trump suit.",
    "• If a Jester is revealed, there is no trump. If a Wizard is revealed, a trump suit is randomly selected.",
    "• Players take turns playing one card per trick, starting with the player to the dealer's left.",
    "• Players must follow the suit of the first card played, if they have it, otherwise play any card.",
    "• Trump cards beat all cards of other suits. Wizards beat all other cards. Jesters lose to everything.",
    "• The highest card in the lead suit wins the trick unless a trump or Wizard is played.",
    "• After all tricks are played, scores are calculated for each player.",
    "• If a player matches their bid exactly, they score 20 points plus 10 per trick won.",
    "• If a player misses their bid, they lose 10 points per trick off their bid (over or under).",
    "• The number of cards dealt increases by one each round until the deck runs out.",
    "• The game ends after the final round and the player with the highest total score wins!"
]
        for i, line in enumerate(instructions):
            text = tiny_font.render(line, True, BLACK)
            screen.blit(text, (help_rect.left + 30, help_rect.top + 80 + i * 35))



def draw_help_button(screen):
    WIDTH, HEIGHT = screen.get_size()

    help_radius = 20
    help_center = (WIDTH -50, 50)
    button_color = LIGHT_YELLOW if show_help else LIGHT_BLUE
    pygame.draw.circle(screen, button_color, help_center, help_radius)
    pygame.draw.circle(screen, BLACK, help_center, help_radius, 2)  # Border

    # "i" Icon (centered)
    font = pygame.font.SysFont("Segoe UI Symbol", 36, bold=True)
    i_text = font.render("ℹ", True, BLACK)
    i_text_rect = i_text.get_rect(center=help_center)
    screen.blit(i_text, i_text_rect)

    return help_center, help_radius

def is_info_button_clicked(mouse_pos, i_text_rect):
    help_center,help_radius = i_text_rect
    dist = ((mouse_pos[0] - help_center[0]) ** 2 + (mouse_pos[1] - help_center[1]) ** 2) ** 0.5
    if dist <= help_radius:
        global show_help
        show_help = not show_help


def draw_auto_play_button(screen, font, game):
    """Draw the auto-play toggle button and return its rect for click detection"""
    button_width = 150
    button_height = 40
    button_x = 10  # Position it next to the show all cards button
    button_y = 110
    
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Button color based on state
    auto_play_on = game.is_auto_play_enabled()
    button_color = LIGHT_YELLOW if auto_play_on else LIGHT_BLUE
    shadow_rect = button_rect.move(2, 2)
    pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=3)
    
    pygame.draw.rect(screen, button_color, button_rect, border_radius=3)
    pygame.draw.rect(screen, BLACK, button_rect, 2, border_radius=3)
     
    # Button text
    text = "Auto-Play: ON" if auto_play_on else "Auto-Play: OFF"
    button_text = font.render(text, True, BLACK)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    
    return button_rect



def toggle_show_best_move():
    global show_best_move
    show_best_move = not show_best_move

def is_button_clicked(mouse_pos, button_rect):
    return button_rect.collidepoint(mouse_pos)

def set_best_move_suggestion(suggestion):
    global best_move_suggestion
    best_move_suggestion = suggestion

def draw_show_best_move_button(screen, font):
    button_rect = pygame.Rect(10, 60, 150, 40)  # Below show all cards
    button_color = LIGHT_YELLOW if show_best_move else LIGHT_BLUE
    shadow_rect = button_rect.move(2, 2)
    pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=3)
    pygame.draw.rect(screen, button_color, button_rect,border_radius=3)
    pygame.draw.rect(screen, BLACK, button_rect, 2,border_radius=3)
    text = "Hide Best Move" if show_best_move else "Show Best Move"
    button_text = font.render(text, True, BLACK)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    return button_rect

def toggle_show_all_cards():
    """Toggle the show all cards state - call this from main file"""
    global show_all_cards
    show_all_cards = not show_all_cards


def draw_show_all_cards_button(screen, font):
    """Draw the show all cards button and return its rect for click detection"""
    button_width = 150
    button_height = 40
    button_x = 10  # Top left corner
    button_y = 10
    
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Button color based on state
    button_color = LIGHT_YELLOW if show_all_cards else LIGHT_BLUE
    shadow_rect = button_rect.move(2, 2)
    pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=3)
    
    pygame.draw.rect(screen, button_color, button_rect,border_radius=3)
    pygame.draw.rect(screen, BLACK, button_rect, 2,border_radius=3)
     
    # Button text
    text = "Hide All Cards" if show_all_cards else "Show All Cards"
    button_text = font.render(text, True, BLACK)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
    
    return button_rect

def draw_background(screen):
    WIDTH, HEIGHT = screen.get_size()
    screen.fill(LIGHT_BLUE_B)
    # Optional: dark corners for shadow effect
    shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, SHADOW_COLOR, (-100, -100, WIDTH+200, HEIGHT+200))
    screen.blit(shadow, (0, 0))

# Draw the poker table (oval with wooden border)
def draw_poker_table(screen):
    table_rect = pygame.Rect(180, 160, 450, 450)  # x, y, w, h

    # Wooden Border (Outer Oval)
    pygame.draw.ellipse(screen, WOOD_BROWN, table_rect)

    # Inner Felt (Green Oval)
    inner_rect = table_rect.inflate(-30, -30)  # slightly smaller for border
    pygame.draw.ellipse(screen, GREEN_FELT, inner_rect)

    # Inner Shadow to give depth (darker green inner oval)
    shadow_rect = inner_rect.inflate(-10, -10)
    pygame.draw.ellipse(screen, DARK_GREEN, shadow_rect)


def draw_player_cards(screen, game, name, info, small_font):
    """Draw cards for a player"""
    x, y = info["pos"]
    hand = info["hand"]
    info["rects"] = []
    
    # Determine if we should show cards
    should_show_cards = (info["is_human"] or 
                        game.phase == GamePhase.GAME_OVER or 
                        show_all_cards)
    
    if hand:
        # Determine position and size based on player
        is_original_human = (name == game.original_human_player)

        if is_original_human or info["is_human"]:
            # Human player - normal size, below
            max_visible = 7  # Max cards before overlapping starts
            card_width = 50
            card_height = 70
            padding = 5
            overlap_offset = 20  # How much cards overlap when there are many
            if len(hand) <= max_visible:
                total_width = len(hand) * (card_width + padding) - padding  # No overlap
            else:
                total_width = len(hand) * (card_width - overlap_offset) + overlap_offset  # Overlap

            start_x = x - total_width // 2
            start_y = y + 100
        else:
            # Non-human players - smaller cards, positioned around table
            card_width = 40
            card_height = 60
            padding = 3
            overlap_offset = 40  # How much cards overlap vertically
            column_offset = 41    # Horizontal offset between columns
            
            # Get player index to determine position
            player_keys = list(game.players.keys())

            if game.original_human_player in player_keys:
                player_keys.remove(game.original_human_player)
            else:
                player_keys=player_keys[1:]
            player_index = player_keys.index(name)

            
            # Common parameters for all non-human players
            max_cards_per_column = 10  # Max cards in a column before new column starts
            
            if player_index in [0, 1]:  # Right side players
                # Vertical layout on right side
                start_x = x + 70
                start_y = y - (min(len(hand), max_cards_per_column) * (card_height - overlap_offset)) // 2
            elif player_index in [2,3, 4]:  # Left side players
                # Vertical layout on left side
                start_x = x - 100 - card_width
                start_y = y - (min(len(hand), max_cards_per_column) * (card_height - overlap_offset)) // 2
            else:
                # Fallback position (horizontal)
                max_visible = 7
                start_x = x - (min(len(hand), max_visible) * (card_width - overlap_offset)) // 2
                start_y = y + 100
        
        # Draw the cards with overlapping when needed
        for i, card in enumerate(hand):
            if is_original_human or info["is_human"]:  # Horizontal layout
                # Calculate position with overlapping
                if len(hand) <= max_visible:
                    # No overlapping needed
                    card_x = start_x + i * (card_width + padding)
                else:
                    # Overlapping cards
                    card_x = start_x + i * (card_width - overlap_offset)
                card_y = start_y
            else:  # Vertical layout for side players with columns
                # Calculate column and position within column
                column = i // max_cards_per_column
                total_columns = (len(hand) - 1) // max_cards_per_column + 1
                pos_in_column = i % max_cards_per_column
                
                card_x = start_x + (total_columns - 1 - column) * column_offset
                card_y = start_y + pos_in_column * (card_height - overlap_offset)
                
            
            if should_show_cards or is_original_human:
                # Draw the actual card using the draw_card function
                draw_card(screen, game, card, card_x, card_y, card_width, card_height)
            else:
                draw_card_facedown(screen, game, card, card_x, card_y, card_width, card_height)
            
            # Store the rect for click detection (human player only)
            if info["is_human"]:
                card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
                info["rects"].append((card_rect, card))

def draw_trump_card(screen, game, font, small_font):
    """Draw the trump card"""
    if not game.trump_card:
        return
        
    trump_x, trump_y = 600, 50
    game.trump_card
    draw_card(screen,game,game.trump_card,trump_x,trump_y,card_width=50,card_height=70  )
    
    # Trump label
    label = small_font.render("Trump Card", True, WHITE)
    screen.blit(label, (trump_x - 5, trump_y - 20))

def draw_played_cards(screen, game, small_font):
    """Draw cards played in current trick"""
    if not game.played_cards:
        return
        
    WIDTH, HEIGHT = screen.get_size()
    center_x, center_y = (WIDTH -700) // 2, HEIGHT // 2
    
    # Dynamic positioning based on number of players
    num_players = len(game.player_names)
    angle_step = 360 / num_players
    radius = 80
    
    for i, (player, card) in enumerate(game.played_cards.items()):
        # Find the player's index in the player list
        player_index = game.player_names.index(player)
        angle = player_index * (-angle_step )* (math.pi / 180) + 90 # Convert to radians
        
        card_x = center_x + int(radius * math.cos(angle)) - 30
        card_y = center_y + int(radius * math.sin(angle)) - 30 ###
        
        draw_card(screen,game,card,card_x,card_y)

        # Player name above card
        name_text = pygame.font.SysFont(None, 18).render(player, True, WHITE)
        screen.blit(name_text, (card_x + 30 - name_text.get_width() // 2, card_y - 20))

def draw_card(screen, game, card, card_x, card_y,card_width=40,card_height=60):
    card_rect = pygame.Rect(card_x, card_y, card_width, card_height)

    # Drop shadow
    shadow_rect = card_rect.move(3, 3)
    pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=6)

    # Determine card background color
    card_color = WHITE
    if card == "Wizard":
        card_color = LIGHT_BLUE
    elif card == "Fool":
        card_color = LIGHT_RED
    elif game.trump_suit and len(card) > 1 and card[-1] == game.trump_suit:
        card_color = LIGHT_YELLOW

    pygame.draw.rect(screen, card_color, card_rect, border_radius=6)
    pygame.draw.rect(screen, BLACK, card_rect, 2, border_radius=6)

    # Determine display text and color
    if card == "Wizard":
        display_text = "W"
        text_color = BLACK
    elif card == "Fool":
        display_text = "F"
        text_color = RED
    elif len(card) > 1:
        display_text = card[:-1]  # number/letter
        suit = card[-1]
        suit_colors = {'R': RED, 'G': GREEN, 'B': BLUE, 'Y': (255, 215, 88)}
        text_color = suit_colors.get(suit, BLACK)

    # Draw card text (both upright and inverted)
    card_font = pygame.font.SysFont("Arial", 16, bold=True)
    text = card_font.render(display_text, True, text_color)

    # Top-left text
    text_pos = (card_x + 5, card_y + 5)
    screen.blit(text, text_pos)

    # Bottom-right inverted text
    inverted_text = pygame.transform.rotate(text, 180)
    inverted_text_rect = inverted_text.get_rect()
    inverted_text_pos = (card_x + card_width - inverted_text_rect.width - 5,
                         card_y + card_height - inverted_text_rect.height - 5)
    screen.blit(inverted_text, inverted_text_pos)

    return

def draw_card_facedown(screen, game, card, card_x, card_y,card_width=40,card_height=60):
    card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
    # Drop shadow
    shadow_rect = card_rect.move(3, 3)
    shadow_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 80), shadow_surface.get_rect(), border_radius=6)
    screen.blit(shadow_surface, shadow_rect.topleft)

    pygame.draw.rect(screen, WHITE, card_rect, border_radius=6)  # white border
    inner_rect = card_rect.inflate(-2, -2)  # make inner rect slightly smaller for border
    pygame.draw.rect(screen, CARD_BACK_COLOR, inner_rect, border_radius=6)  # card face

    # Optional: simple inner design (like a cross)
    pygame.draw.line(screen, WHITE, 
                    (inner_rect.left + 5, inner_rect.top + 5), 
                    (inner_rect.right - 5, inner_rect.bottom - 5), 2)
    pygame.draw.line(screen, WHITE, 
                    (inner_rect.right - 5, inner_rect.top + 5), 
                    (inner_rect.left + 5, inner_rect.bottom - 5), 2)


def draw_bid_ui(screen, game):
    """Draw bidding interface for human player"""
    current_player = game.player_names[game.current_player_index]
    if not game.players[current_player]["is_human"]:
        return
    
    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont(None, 36)
    
    # Clear previous bid buttons
    game.bid_buttons = []
    
    # Bidding prompt
    prompt = font.render(f"Your bid (0-{game.round_num}):", True, WHITE)
    screen.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 150))
    
    # Bid buttons
    button_width = 40
    button_height = 40
    spacing = 10
    max_buttons_per_row = 10
    
    for bid in range(game.round_num + 1):
        row = bid // max_buttons_per_row
        col = bid % max_buttons_per_row
        
        # Calculate position
        buttons_in_row = min(game.round_num + 1 - row * max_buttons_per_row, max_buttons_per_row)
        start_x = WIDTH // 2 - (buttons_in_row * (button_width + spacing) - spacing) // 2
        
        button_x = start_x + col * (button_width + spacing)
        button_y = HEIGHT - 100 + row * (button_height + spacing)
        
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        shadow_rect = button_rect.move(1, 1)
        pygame.draw.rect(screen, (0, 0, 0, 80), shadow_rect, border_radius=3)
        # Draw button
        pygame.draw.rect(screen, LIGHT_BLUE, button_rect,border_radius=3)
        pygame.draw.rect(screen, BLACK, button_rect, 2,border_radius=3)
        
        # Button text
        text = font.render(str(bid), True, BLACK)
        text_rect = text.get_rect(center=button_rect.center)
        screen.blit(text, text_rect)
        
        game.bid_buttons.append((button_rect, bid))

def draw_game_info(screen, game,small_font):
    """Draw game information panel"""
    WIDTH, HEIGHT = screen.get_size()
    font = pygame.font.SysFont(None, 24)
    
    # Game info panel
    info_x = WIDTH - 300
    info_y = 20
    
    # Round info
    round_text = font.render(f"Round: {game.round_num}/{game.max_rounds}", True, WHITE)
    screen.blit(round_text, (info_x, info_y))
    
    trick_text = font.render(f"Trick: {game.trick_num}/{game.round_num}", True, WHITE)
    screen.blit(trick_text, (info_x, info_y + 25))
    
    # Phase info
    phase_names = {
        GamePhase.DEALING: "Dealing",
        GamePhase.BIDDING: "Bidding",
        GamePhase.PLAYING: "Playing",
        GamePhase.SCORING: "Scoring",
        GamePhase.GAME_OVER: "Game Over"
    }
    phase_text = font.render(f"Phase: {phase_names.get(game.phase, 'Unknown')}", True, WHITE)
    screen.blit(phase_text, (info_x, info_y + 50))
    
    # Trump suit info
    if game.trump_suit:
        trump_text = font.render(f"Trump: {game.trump_suit}", True, WHITE)
        screen.blit(trump_text, (info_x, info_y + 75))
    elif game.trump_card == "Fool":
        no_trump_text = font.render("No Trump (Fool)", True, WHITE)
        screen.blit(no_trump_text, (info_x, info_y + 75))
    
    # Current player info
    if game.phase in [GamePhase.BIDDING, GamePhase.PLAYING]:
        current_text = font.render(f"Current: {game.player_names[game.current_player_index]}", True, WHITE)
        screen.blit(current_text, (info_x, info_y + 100))
    
    # Dealer info
    dealer_text = font.render(f"Dealer: {game.player_names[game.dealer_index]}", True, WHITE)
    screen.blit(dealer_text, (info_x, info_y + 125))
    
    # Score summary
    if game.phase == GamePhase.GAME_OVER:
        # Show final scores
        sorted_scores = sorted(game.scores.items(), key=lambda x: x[1], reverse=True)
        winner_text = font.render(f"Winner: {sorted_scores[0][0]} ({sorted_scores[0][1]} pts)", True, YELLOW)
        screen.blit(winner_text, (info_x, info_y + 150))
        
        for i, (player, score) in enumerate(sorted_scores[1:], 1):
            score_text = font.render(f"{i+1}. {player}: {score}", True, WHITE)
            screen.blit(score_text, (info_x, info_y + 150 + 25 * i))
    
    log_y = info_y + 200

    log_title = font.render("Recent Events:", True, WHITE)
    screen.blit(log_title, (info_x, log_y-20))

    x, y = info_x, log_y
    width, height = 280, 120
    # Draw log background
    pygame.draw.rect(screen, (20, 20, 20), (x, y, width, height))
    pygame.draw.rect(screen, WHITE, (x, y, width, height), 1)

    # Clip drawing to log area
    clip_rect = pygame.Rect(x, y, width, height)
    screen.set_clip(clip_rect)

    # Game log (recent messages)
    
        
    if game.game_log:
        
        log_y= info_y + 200 + 10 -game.log_scroll
        for entry in reversed(game.game_log[-100:]):  # Limit entries
            if len(entry) > 40:
                entry = entry[:37] + "..."
            line = small_font.render(entry, True, WHITE)
            screen.blit(line, (info_x+5 , log_y))
            log_y += 20
        screen.set_clip(None)  # Reset clip
    

def draw_scoreboard(screen, game):
   
    """Draw permanent scoreboard showing all round results"""
    font = pygame.font.SysFont(None, 18)
    small_font = pygame.font.SysFont(None, 16)
    
    # Calculate dimensions based on number of players and rounds
    num_players = len(game.player_names)
    max_rounds = game.max_rounds
    
    WIDTH, HEIGHT = screen.get_size()
   
    # Column widths
    round_col_width = 30
    player_col_width = max(80, 300 // num_players)  # Adjust based on player count
    
    # Row height
    row_height = 20
    header_height = 25
    
    # Calculate total scoreboard dimensions
    total_width = round_col_width + (num_players * player_col_width) 
    total_height = header_height + (max_rounds + 1) * row_height  # +1 for totals row
    
     # Game info panel
    x = WIDTH - total_width-20
    y= 350

    # Background
    scoreboard_rect = pygame.Rect(x, y, total_width, total_height)
    pygame.draw.rect(screen, (40, 40, 40), scoreboard_rect)
    pygame.draw.rect(screen, WHITE, scoreboard_rect, 2)
    
    # Headers
    current_x = x + 5
    
    # Round header
    round_header = font.render("Rd", True, WHITE)
    screen.blit(round_header, (current_x, y + 5))
    current_x += round_col_width
    
    # Player headers
    for i, player_name in enumerate(game.player_names):
        # Truncate long player names
        display_name = player_name if len(player_name) <= 8 else player_name[:6] + ".."
        player_header = font.render(display_name, True, WHITE)
        screen.blit(player_header, (current_x, y + 5))
        current_x += player_col_width
    
    # Horizontal line after headers
    pygame.draw.line(screen, WHITE, (x, y + header_height), (x + total_width, y + header_height), 1)
    
    # Round data
    for round_idx in range(max_rounds):
        row_y = y + header_height + (round_idx * row_height)
        current_x = x + 5
        
        # Round number
        round_text = small_font.render(str(round_idx + 1), True, WHITE)
        screen.blit(round_text, (current_x, row_y + 2))
        current_x += round_col_width
        
        # Player scores for this round
        if round_idx < len(game.round_results):
            round_data = game.round_results[round_idx]
            
            for player_name in game.player_names:
                score = round_data['scores'].get(player_name, 0)
                bid = round_data['bids'].get(player_name, 0)
                won = round_data['won'].get(player_name, 0)
                
                # Color code the score based on success
                if bid == won:
                    color = (0, 255, 0)  # Green for correct bid
                else:
                    color = (255, 100, 100)  # Light red for incorrect bid
                
                # Show score with bid/won info
                score_text = f"{score}"
                if game.phase != GamePhase.GAME_OVER or round_idx < game.round_num - 1:
                    # Show bid/won info for completed rounds
                    if bid is not None and won is not None:
                        score_text = f"{score} ({bid}/{won})"
                
                # Truncate if too long
                if len(score_text) > 8:
                    score_text = f"{score}"
                
                text = small_font.render(score_text, True, color)
                screen.blit(text, (current_x, row_y + 2))
                current_x += player_col_width
        else:
            # Future rounds - show empty cells
            for _ in game.player_names:
                dash_text = small_font.render("-", True, GRAY)
                screen.blit(dash_text, (current_x, row_y + 2))
                current_x += player_col_width
        
        # Highlight current round
        if round_idx == game.round_num - 1 and game.phase != GamePhase.GAME_OVER:
            pygame.draw.rect(screen, YELLOW, (x, row_y, total_width, row_height), 2)
    
    # Totals row
    totals_y = y + header_height + (max_rounds * row_height)
    pygame.draw.line(screen, WHITE, (x, totals_y), (x + total_width, totals_y), 2)
    
    current_x = x + 5
    
    # "Total" label
    total_label = font.render("Total", True, WHITE)
    screen.blit(total_label, (current_x, totals_y + 2))
    current_x += round_col_width
    
    # Player totals
    for player_name in game.player_names:
        total_score = game.scores[player_name]
        
        # Highlight winner in game over
        color = WHITE
        if game.phase == GamePhase.GAME_OVER:
            max_score = max(game.scores.values())
            if total_score == max_score:
                color = YELLOW
        
        total_text = font.render(str(total_score), True, color)
        screen.blit(total_text, (current_x, totals_y + 2))
        current_x += player_col_width    