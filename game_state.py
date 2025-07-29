import pygame
import random
from enum import Enum
import datetime



class GamePhase(Enum):
    DEALING = 1
    BIDDING = 2
    PLAYING = 3
    SCORING = 4
    GAME_OVER = 5

def create_deck():
    """Create a Wizard deck: 52 regular cards + 4 Wizards + 4 Fools"""
    suits = ['R', 'G', 'B', 'Y']  # Red, Green, Blue, Yellow
    ranks = list(range(1, 14))  # 1-13
    deck = [f"{rank}{suit}" for rank in ranks for suit in suits]
    deck += ["Wizard"] * 4
    deck += ["Fool"] * 4
    random.shuffle(deck)
    return deck

def create_players(num_players,name_input="Player 1"):
    """Create players with positions based on number of players"""
    
    players = {}
    
    if num_players == 2:
        positions = [(400, 600), (650, 500)]
    elif num_players == 3:
        positions = [(400, 600), (650, 500), (650, 250)]
    elif num_players == 4:
        positions = [(400, 600), (650, 500), (650, 250), (400, 100)]
    elif num_players == 5:
        positions = [(400, 600), (650, 500), (650, 250), (400, 100), (150, 250)]
    else:  # 6 players
        positions = [(400, 600), (650, 500), (650, 250), (400, 100), (150, 250), (150, 500)]
    
    players[name_input]= {"pos": positions[0],"hand": [],"is_human": True}

    
         
    for i in range(1,num_players):
        players[f"Player {i+1}"] = {
            "pos": positions[i],
            "hand": [],
            "is_human": i == 0  # Only Player 1 is human
        }
    
    return players




class WizardGame:
    def __init__(self, num_players=4):
        self.num_players = num_players
        self.players = create_players(num_players)
        self.player_names = list(self.players.keys())
        self.original_human_player = None
       
        self.deck = []
        self.trump_suit = None
        self.trump_card = None
        self.phase = GamePhase.DEALING
        
        # Game state
        self.round_num = 1
        self.max_rounds = 60 // self.num_players  # Adjust based on player count
        self.dealer_index = 0
        self.current_player_index = 0
        self.trick_leader_index = 0
        
        # Round state
        self.bids = {}
        self.tricks_won = {}
        self.played_cards = {}  # {player: card} for current trick
        self.trick_num = 1
        self.led_suit = None
        
        # Scoring
        self.scores = {name: 0 for name in self.player_names}
        self.round_results = []
        
        # UI state
        self.message = ""
        self.bid_buttons = []
        self.game_log = []
        self.log_scroll = 0
        self.ai_timer = 0
        self.next_round_timer = 1
        
        self.start_new_round()

    def set_human_player_name(self, new_name):
        """Update the human player's name"""
        # Find the human player
        human_player_key = None
        for player_name, player_data in self.players.items():
            if player_data["is_human"]:
                human_player_key = player_name
                break
        self.original_human_player = new_name

        if human_player_key and human_player_key != new_name:
            # Update the player dictionary with new name
            player_data = self.players.pop(human_player_key)
            self.players[new_name] = player_data
             
            self.original_human_player = new_name
            
            # Update player_names list if it exists
            if hasattr(self, 'player_names'):
                try:
                    index = self.player_names.index(human_player_key)
                    self.player_names[index] = new_name
                except ValueError:
                    pass
            if hasattr(self, 'scores'):
                old_score = self.scores.get(human_player_key, 0)
                self.scores = {name: 0 for name in self.player_names}
                self.scores[new_name] = old_score  # Preserve any existing score
            if hasattr(self, 'tricks_won'):
                tricks_won_old = self.tricks_won.get(human_player_key, 0)
                self.tricks_won = {name: 0 for name in self.player_names}
                self.tricks_won[new_name] = tricks_won_old  # Preserve any existing score


    def toggle_auto_play(self):
        """Toggle the original human player between human and AI control"""
        if not self.original_human_player:
            return False  # No original human player found
        
        if self.original_human_player not in self.players:
            return False  # Original human player no longer exists
        
        # Toggle the original human player's is_human flag
        current_state = self.players[self.original_human_player]["is_human"]
        self.players[self.original_human_player]["is_human"] = not current_state
        
        if self.players[self.original_human_player]["is_human"]:
            self.log(f"{self.original_human_player} is now controlled by human")
        else:
            self.log(f"{self.original_human_player} is now controlled by AI")
        
        return True

    def is_auto_play_enabled(self):
        """Check if auto-play is currently enabled (original human player is AI-controlled)"""
        if not self.original_human_player or self.original_human_player not in self.players:
            return False
        return not self.players[self.original_human_player]["is_human"]

    def start_new_round(self):
        """Start a new round"""
        if self.round_num > self.max_rounds:
            self.save_game_log()
            self.phase = GamePhase.GAME_OVER
            self.message = "Game Over!"
            return
            
        self.deck = create_deck()
        self.trump_suit = None
        self.trump_card = None
        self.bids = {}
        self.tricks_won = {name: 0 for name in self.player_names}
        self.played_cards = {}
        self.trick_num = 1
        self.led_suit = None
        
        # Deal cards
        self.deal_cards()
        
        # Determine trump
        self.determine_trump()
        
        # Start bidding with player to left of dealer
        self.current_player_index = (self.dealer_index + 1) % self.num_players
        self.phase = GamePhase.BIDDING
        self.bid_buttons = []
        
        self.log(f"Round {self.round_num} started. {self.player_names[self.dealer_index]} deals.")
        if self.trump_suit:
            self.log(f"Trump suit: {self.trump_suit} (from {self.trump_card})")
        else:
            self.log("No trump this round")
    
    def deal_cards(self):
        """Deal cards for current round"""
        cards_per_player = self.round_num
        
        # Clear hands
        for player in self.players.values():
            player["hand"] = []
        
        # Deal cards
        for _ in range(cards_per_player):
            for i in range(self.num_players):
                player_name = self.player_names[i]
                if self.deck:
                    self.players[player_name]["hand"].append(self.deck.pop())
    
    def determine_trump(self):
        """Determine trump suit based on top card of remaining deck"""
        if self.round_num == self.max_rounds:
            # Last round has no trump
            self.trump_suit = None
            self.trump_card = None
            return
        
        if not self.deck:
            self.trump_suit = None
            self.trump_card = None
            return
            
        self.trump_card = self.deck.pop()
        
        if self.trump_card == "Fool":
            self.trump_suit = None
        elif self.trump_card == "Wizard":
            # Dealer chooses trump - for now, let's make it random for AI dealer
            if self.players[self.player_names[self.dealer_index]]["is_human"]:
                # Human dealer - would need UI for this
                self.trump_suit = random.choice(['R', 'G', 'B', 'Y'])
            else:
                self.trump_suit = random.choice(['R', 'G', 'B', 'Y'])
        else:
            self.trump_suit = self.trump_card[-1]  # Last character is suit
    
    def process_bid(self, bid):
        """Process a bid from current player"""
        if self.phase != GamePhase.BIDDING:
            return False
            
        current_player = self.player_names[self.current_player_index]
        self.bids[current_player] = bid
        self.log(f"{current_player} bids {bid}")
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % self.num_players
        
        # Check if all players have bid
        if len(self.bids) == self.num_players:
            self.phase = GamePhase.PLAYING
            # First trick starts with player to left of dealer
            self.trick_leader_index = (self.dealer_index + 1) % self.num_players
            self.current_player_index = self.trick_leader_index
            self.log("Bidding complete. Playing tricks...")
        
        return True
    
    def can_play_card(self, card, player_name):
        """Check if a card can be legally played"""
        if not self.led_suit:
            return True  # First card of trick, anything goes
        
        if card in ["Wizard", "Fool"]:
            return True  # Special cards can always be played
        
        player_hand = self.players[player_name]["hand"]
        
        # Must follow led suit if possible
        can_follow_suit = any(c[-1] == self.led_suit and c not in ["Wizard", "Fool"] 
                             for c in player_hand)
        
        if can_follow_suit:
            return card[-1] == self.led_suit or card in ["Wizard", "Fool"]
        else:
            return True  # Can play anything if can't follow suit
    
    def play_card(self, card, player_name):
        """Play a card"""
        if self.phase != GamePhase.PLAYING:
            return False
        
        if player_name != self.player_names[self.current_player_index]:
            return False  # Not this player's turn
        
        if not self.can_play_card(card, player_name):
            self.log(f"{player_name} must follow led suit!")
            return False
        
        # Remove card from hand and play it
        self.players[player_name]["hand"].remove(card)
        self.played_cards[player_name] = card
        
        # Set led suit if this is first card
        if not self.led_suit:
            if card == "Fool":
                # Fool doesn't set led suit - wait for next card
                pass
            elif card not in ["Wizard", "Fool"]:
                self.led_suit = card[-1]
        elif self.led_suit is None and card not in ["Wizard", "Fool"]:
            # Second card after Fool sets the led suit
            self.led_suit = card[-1]
        
        self.log(f"{player_name} played {card}")
        
        # Move to next player
        self.current_player_index = (self.current_player_index + 1) % self.num_players
        
        # Check if trick is complete
        if len(self.played_cards) == self.num_players:
            self.resolve_trick()
        
        return True
    
    def resolve_trick(self):
        """Determine winner of current trick"""
        winner = self.determine_trick_winner()
        self.tricks_won[winner] += 1
        self.log(f"{winner} wins trick {self.trick_num}")
        
        # Prepare for next trick
        self.played_cards = {}
        self.led_suit = None
        self.trick_num += 1
        
        # Winner leads next trick
        self.trick_leader_index = self.player_names.index(winner)
        self.current_player_index = self.trick_leader_index
        
        # Check if round is over
        if self.trick_num > self.round_num:
            self.score_round()
    
    def determine_trick_winner(self):
        """Determine who wins the current trick"""
        
        # Check for Wizards first
        for player, card in self.played_cards.items():
            if card == "Wizard":
                return player  # First Wizard wins
        
        # No Wizards - check for trump cards
        trump_cards = {}
        for player, card in self.played_cards.items():
            if card != "Fool" and self.trump_suit and card[-1] == self.trump_suit:
                trump_cards[player] = int(card[:-1])
        
        if trump_cards:
            # Highest trump wins
            winner = max(trump_cards.items(), key=lambda x: x[1])
            return winner[0]
        
        # No trump - check led suit
        if self.led_suit:
            led_suit_cards = {}
            for player, card in self.played_cards.items():
                if card != "Fool" and card[-1] == self.led_suit:
                    led_suit_cards[player] = int(card[:-1])
            
            if led_suit_cards:
                winner = max(led_suit_cards.items(), key=lambda x: x[1])
                return winner[0]
        
        # Only Fools played - first Fool wins
        for player, card in self.played_cards.items():
            if card == "Fool":
                return player
        
        # Shouldn't reach here
        return list(self.played_cards.keys())[0]
    
    def score_round(self):
        """Score the completed round"""
        self.phase = GamePhase.SCORING
        round_scores = {}
        
        for player in self.player_names:
            bid = self.bids[player]
            won = self.tricks_won[player]
            
            if bid == won:
                # Correct bid: 20 + 10 per trick
                score = 20 + 10 * won
            else:
                # Wrong bid: -10 per trick difference
                score = -10 * abs(bid - won)
            
            round_scores[player] = score
            self.scores[player] += score
            self.log(f"{player}: bid {bid}, won {won} -> {score} points")
        
        self.round_results.append({
            'round': self.round_num,
            'bids': self.bids.copy(),
            'won': self.tricks_won.copy(),
            'scores': round_scores.copy()
        })
        
        # Advance to next round
        self.round_num += 1
        self.dealer_index = (self.dealer_index + 1) % self.num_players
        
        # Set timer for next round
        self.next_round_timer = pygame.time.get_ticks() + 3000  # 3 seconds
    
    def update(self):
        """Update game state - handle timers"""
        current_time = pygame.time.get_ticks()
        
        # Handle next round timer
        if self.next_round_timer > 0 and current_time >= self.next_round_timer:
            self.next_round_timer = 0
            self.start_new_round()
        
        # Handle AI moves
        if self.phase == GamePhase.BIDDING:
            current_player = self.player_names[self.current_player_index]
            if not self.players[current_player]["is_human"]:
                if self.ai_timer == 0:
                    self.ai_timer = current_time + 1000  # 1.5 second delay
                elif current_time >= self.ai_timer:
                    self.ai_timer = 0
                    # Simple AI bidding
                    ai_bid = random.randint(0, self.round_num)
                    self.process_bid(ai_bid)
        
        elif self.phase == GamePhase.PLAYING:
            current_player = self.player_names[self.current_player_index]
            if not self.players[current_player]["is_human"]:
                if self.ai_timer == 0:
                    self.ai_timer = current_time + 1000  # 1 second delay
                elif current_time >= self.ai_timer:
                    self.ai_timer = 0
                    # Simple AI - play first legal card
                    hand = self.players[current_player]["hand"]
                    for card in hand:
                        if self.can_play_card(card, current_player):
                            self.play_card(card, current_player)
                            break
    
    def handle_click(self, pos):
        """Handle mouse clicks"""
        if self.phase == GamePhase.BIDDING:
            return self.handle_bid_click(pos)
        elif self.phase == GamePhase.PLAYING:
            return self.handle_card_click(pos)
        return False
    
    def handle_bid_click(self, pos):
        """Handle clicking on bid buttons"""
        for rect, bid_value in self.bid_buttons:
            if rect.collidepoint(pos):
                return self.process_bid(bid_value)
        return False
    
    
    def handle_card_click(self, pos):
        """Handle clicking on cards"""
        current_player = self.player_names[self.current_player_index]
        player_info = self.players[current_player]
        
        # Only allow human player to click
        if not player_info["is_human"]:
            return False
        
        #for rect, card in player_info.get("rects", []):
        for rect, card in reversed(player_info.get("rects", [])):
            if rect.collidepoint(pos):
                return self.play_card(card, current_player)
        return False


    def log(self, message):
        """Add message to game log"""
        self.game_log.append(message)
        self.message = message
        if len(self.game_log) > 100:  # Limit log size
            self.game_log.pop(0)

    
    def save_game_log(self, filename="wizard_game_log.txt"):
        # Get current timestamp
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Count number of players based on bids length from the first round
        if not self.round_results:
            print("No round results to log.")
            return

        num_players = len(self.round_results[0]['bids'])

        # Start log content
        log_lines = [
            f"Wizard Game Log - {timestamp}",
            f"Number of Players: {num_players}",
            "-" * 40
        ]

        # Add each round's results
        for result in self.round_results:
            log_lines.append(f"Round {result['round']}:")
            log_lines.append(f"  Bids: {result['bids']}")
            log_lines.append(f"  Tricks Won: {result['won']}")
            log_lines.append(f"  Round Scores: {result['scores']}")
            log_lines.append("-" * 40)

        # Write to file
        with open(filename, "a", encoding="utf-8") as f:
            for line in log_lines:
                f.write(line + "\n")

        print(f"Game log saved to {filename}")

    
    