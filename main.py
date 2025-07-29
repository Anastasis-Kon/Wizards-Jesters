import pygame
from game_state import *
from ui import *
#from fixed_ismcts_ai import ISMCTSWizardGame,ISMCTSAIPlayer
from ai import ISMCTSWizardGame,ISMCTSAIPlayer # Import the ISMCTS version
import threading
import copy
import time 

pygame.init()

WIDTH = 1500
HEIGHT = 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wizard Card Game - ISMCTS AI")
clock = pygame.time.Clock()

# Game setup state
setup_phase = True
selected_players = 4  # Default
ai_difficulty = "Normal"  # Easy, Normal, Hard
font = pygame.font.SysFont(None, 48)
small_font = pygame.font.SysFont(None, 36)
tiny_font = pygame.font.SysFont(None, 24)
show_text = True
active = False
last_blink_time = time.time()
name_text="Player 1"
# Initialize game state (will be created after setup)
state = None
calculating_best_move = False
def calculate_best_move_async(game_state, player_name):
    global calculating_best_move
    try:
        calculating_best_move = True
        suggestion_ai = ISMCTSAIPlayer(player_name, iterations=10000)
        suggestion_ai.time_limit = 5.0  # optional: time-limited search

        if game_state.phase == GamePhase.BIDDING:
            best_bid = suggestion_ai.get_bid(game_state)
            set_best_move_suggestion(f"Bid {best_bid}")
        elif game_state.phase == GamePhase.PLAYING:
            best_card = suggestion_ai.get_card_play(game_state)
            set_best_move_suggestion(f"Play {best_card}" if best_card else "No valid move")
        else:
            set_best_move_suggestion("Not applicable in this phase")
            
    except Exception as e:
        set_best_move_suggestion(f"Calculation failed: {e}")
    finally:
        calculating_best_move = False


def draw_rounded_rect(surface, color, rect, radius=10, border_color=None, border_width=2):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)



running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            #state.save_game_log()
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and setup_phase:
            # Handle player selection clicks
            mouse_x, mouse_y = event.pos
            active = False
            # Player count buttons
            button_width = 80
            button_height = 60
            spacing = 20
            start_x = WIDTH // 2 - (4 * (button_width + spacing) - spacing) // 2
            start_y = HEIGHT // 2 - 90
            
            for i in range(4):  # 2-6 players
                players = i + 3
                button_x = start_x + i * (button_width + spacing)
                button_rect_p = pygame.Rect(button_x, start_y, button_width, button_height)
                
                if button_rect_p.collidepoint(mouse_x, mouse_y):
                    selected_players = players
                    break
            
            # AI Difficulty buttons
            difficulty_options = ["Easy", "Normal", "Hard"]
            diff_button_width = 120
            diff_spacing = 30
            diff_start_x = WIDTH // 2 - (3 * (diff_button_width + diff_spacing) - diff_spacing) // 2
            diff_start_y = HEIGHT // 2 + 40
            
            for i, difficulty in enumerate(difficulty_options):
                button_x = diff_start_x + i * (diff_button_width + diff_spacing)
                button_rect = pygame.Rect(button_x, diff_start_y, diff_button_width, button_height)
                
                if button_rect.collidepoint(mouse_x, mouse_y):
                    ai_difficulty = difficulty
                    break
            
            # Start button
            start_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 230, 200, 50)
            

            if start_button.collidepoint(mouse_x, mouse_y):
                active=False
                # Create ISMCTS game with difficulty settings
                state = ISMCTSWizardGame(selected_players)
                state.set_human_player_name(name_text)
                
                # Set AI difficulty by adjusting iterations
                iterations_map = {"Easy": 1000, "Normal": 5000, "Hard": 10000}
                iterations = iterations_map[ai_difficulty]
                
                for ai_player in state.ai_players.values():
                    ai_player.iterations = iterations
                
                setup_phase = False
                break
        elif event.type == pygame.KEYDOWN and setup_phase:
            active = True
            if event.key == pygame.K_BACKSPACE:
                name_text = name_text[:-1]
            else:
                name_text +=event.unicode        
        elif event.type == pygame.MOUSEBUTTONDOWN and not setup_phase:
            show_all_button_rect, show_best_move_button_rect,auto_play_rect,i_text_rect= draw_board(screen, state)
            
            if event.button == 4:  # Scroll up
                state.log_scroll = max(state.log_scroll - 25, 0)
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(state.game_log) * 18 - 120)
                state.log_scroll = min(state.log_scroll + 25, max_scroll)
            elif  is_button_clicked(event.pos,show_all_button_rect):
                # Button was clicked, cards will toggle on next frame
                toggle_show_all_cards()
            elif  is_button_clicked(event.pos,show_best_move_button_rect):
                # Button was clicked, cards will toggle on next frame
                toggle_show_best_move()
                if not calculating_best_move and state:
                    player_name = state.player_names[state.current_player_index]
                    set_best_move_suggestion("Calculating...")
                    # Start calculation in a new thread
                    threading.Thread(
                        target=calculate_best_move_async,
                        args=(copy.deepcopy(state), player_name),  # Use a deepcopy or game-specific copy if needed
                        daemon=True  # Thread dies with main program
                    ).start()
            elif is_button_clicked(event.pos,auto_play_rect):
                state.toggle_auto_play()
            elif is_info_button_clicked(event.pos,i_text_rect):
                pass

            else:
                # Use the game's handle_click method for all phases
                active=False
                set_best_move_suggestion("")
                state.handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and state and state.phase == GamePhase.GAME_OVER:
                # Restart game
                setup_phase = True
                state = None
        

    if setup_phase:

        WIDTH, HEIGHT = screen.get_size()
        screen.fill(GREEN)
        # Optional: dark corners for shadow effect
        shadow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, DARK_GREEN, (-100, -100, WIDTH+200, HEIGHT+200))
        screen.blit(shadow, (0, 0))

        # Title
        title = font.render("Wizard Card Game - ISMCTS AI", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HEIGHT // 2 - 200))

        # Instructions
        instruction = small_font.render("Select number of players:", True, WHITE)
        screen.blit(instruction, (WIDTH // 2 - instruction.get_width() // 2, HEIGHT // 2 - 140))

        # Player selection buttons
        button_width = 80
        button_height = 60
        spacing = 20
        start_x = WIDTH // 2 - (4 * (button_width + spacing) - spacing) // 2
        start_y = HEIGHT // 2 - 90

        for i in range(4):  # 2-6 players
            players = i + 3
            button_x = start_x + i * (button_width + spacing)
            button_rect_p = pygame.Rect(button_x, start_y, button_width, button_height)

            # Shadow effect
            shadow_rect = button_rect_p.move(3, 3)
            draw_rounded_rect(screen, SHADOW_COLOR_S, shadow_rect, radius=8)

            # Highlight if selected
            color = LIGHT_BLUE if players == selected_players else WHITE
            draw_rounded_rect(screen, color, button_rect_p, radius=8, border_color=BLACK)

            # Text
            text = small_font.render(str(players), True, BLACK)
            text_rect = text.get_rect(center=button_rect_p.center)
            screen.blit(text, text_rect)

        # AI Difficulty selection
        diff_instruction = small_font.render("AI Difficulty:", True, WHITE)
        screen.blit(diff_instruction, (WIDTH // 2 - diff_instruction.get_width() // 2, HEIGHT // 2))

        difficulty_options = ["Easy", "Normal", "Hard"]
        diff_button_width = 120
        diff_spacing = 30
        diff_start_x = WIDTH // 2 - (3 * (diff_button_width + diff_spacing) - diff_spacing) // 2
        diff_start_y = HEIGHT // 2 + 40

        for i, difficulty in enumerate(difficulty_options):
            button_x = diff_start_x + i * (diff_button_width + diff_spacing)
            button_rect = pygame.Rect(button_x, diff_start_y, diff_button_width, button_height)

            # Shadow
            shadow_rect = button_rect.move(3, 3)
            draw_rounded_rect(screen, SHADOW_COLOR_S, shadow_rect, radius=10)

            # Highlight if selected
            color = LIGHT_BLUE if difficulty == ai_difficulty else WHITE
            draw_rounded_rect(screen, color, button_rect, radius=10, border_color=BLACK)

            # Text
            text = small_font.render(difficulty, True, BLACK)
            text_rect = text.get_rect(center=button_rect.center)
            screen.blit(text, text_rect)

        # Difficulty descriptions
        descriptions = {
            "Easy": "1000 ISMCTS iterations - Quick moves",
            "Normal": "5000 ISMCTS iterations - Balanced play",
            "Hard": "10000 ISMCTS iterations - Strategic play"
        }
        desc_text = tiny_font.render(descriptions[ai_difficulty], True, WHITE)
        screen.blit(desc_text, (WIDTH // 2 - desc_text.get_width() // 2, HEIGHT // 2 + 110))

        current_time = time.time()

        if not active:
            if current_time - last_blink_time > 0.8 :  # 800ms
                show_text = not show_text
                last_blink_time = current_time
        else:
            show_text = True
        
        prompt_surface = small_font.render("Enter Player Name: ", True, WHITE)
        name_surface = small_font.render(name_text, True, WHITE)
        screen.blit(prompt_surface, (WIDTH//2 - prompt_surface.get_width()//2-name_surface.get_width()//2, HEIGHT//2 + 150))
        
        # Blinking name text
        if show_text:  # Always show if there's text, blink only when empty
            screen.blit(name_surface, 
                    (WIDTH//2 - prompt_surface.get_width()//2 + prompt_surface.get_width()-name_surface.get_width()//2, 
                        HEIGHT//2 + 150))


        # Start button
        start_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 230, 200, 50)
        shadow_rect = start_button.move(3, 3)
        draw_rounded_rect(screen, SHADOW_COLOR_S, shadow_rect, radius=12)

        draw_rounded_rect(screen, YELLOW, start_button, radius=12, border_color=BLACK)

        start_text = small_font.render("Start Game", True, BLACK)
        start_text_rect = start_text.get_rect(center=start_button.center)
        screen.blit(start_text, start_text_rect)

        # Info text
        info_lines = [
            "ISMCTS AI uses Monte Carlo Tree Search with Information Sets",
            "to handle the imperfect information in Wizard card game.",
            "Higher difficulty means more strategic thinking but slower moves."
        ]
        for i, line in enumerate(info_lines):
            info_text = tiny_font.render(line, True, WHITE)
            screen.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, HEIGHT // 2 + 300 + i * 20))



        
            
    else:
        # Update game state (this handles AI moves and timers)
        state.update()
        
        draw_board(screen, state)
        
        # Show AI thinking indicator
        current_player = state.player_names[state.current_player_index]
        if (state.phase in [GamePhase.BIDDING, GamePhase.PLAYING] and 
            not state.players[current_player]["is_human"] and 
            state.ai_timer > 0):
            
            thinking_text = tiny_font.render("AI thinking...", True, WHITE)
            screen.blit(thinking_text, (10, HEIGHT - 40))
        
        # Show difficulty in corner
        diff_text = tiny_font.render(f"AI: {ai_difficulty}", True, WHITE)
        screen.blit(diff_text, (WIDTH - diff_text.get_width() - 10, HEIGHT - 20))
        
        # Show restart instruction when game is over
        if state.phase == GamePhase.GAME_OVER:
            restart_text = small_font.render("Press R to restart", True, WHITE)
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT - 50))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()