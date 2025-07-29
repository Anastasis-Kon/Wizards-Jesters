import random
import math
import copy
from collections import defaultdict
import time
from game_state import *

class ISMCTSNode:
    def __init__(self, game_state, parent=None, action=None, player=None):
        self.game_state = game_state  # Determinized game state
        self.parent = parent
        self.action = action  # The action that led to this node
        self.player = player  # Player who made the action
        self.children = []
        self.visits = 0
        self.wins = 0.0
        self.untried_actions = []  # Initialize as empty list instead of None
        self.is_terminal = False
        
    def is_fully_expanded(self):
        return len(self.untried_actions) == 0
    
    def best_child(self, c_param=1.4):
        if not self.children:
            return None
        choices_weights = [
            (child.wins / child.visits) + c_param * math.sqrt((2 * math.log(self.visits) / child.visits))
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]
    
    def expand(self):
        if not self.untried_actions:
            return None
        action = self.untried_actions.pop()
        new_state = self.apply_action(action)
        child_node = ISMCTSNode(new_state, parent=self, action=action, player=self.game_state.get_current_player())
        child_node.initialize_actions()
        self.children.append(child_node)
        return child_node
    
    def initialize_actions(self):
        """Initialize untried actions for this node"""
        if not self.untried_actions:
            self.untried_actions = self.game_state.get_legal_actions()
            self.is_terminal = len(self.untried_actions) == 0 or self.game_state.is_terminal()
    
    def apply_action(self, action):
        # Create a copy of the game state and apply the action
        new_state = copy.deepcopy(self.game_state)
        try:
            if action['type'] == 'bid':
                new_state.process_bid(action['value'])
            elif action['type'] == 'play_card':
                new_state.play_card(action['card'], action['player'])
        except Exception as e:
            # If action fails, return current state
            pass
        return new_state
    
    def simulate(self):
        # Run a random playout from this state
        current_state = copy.deepcopy(self.game_state)
        max_moves = 100  # Prevent infinite loops
        moves_made = 0
        
        while not current_state.is_terminal() and moves_made < max_moves:
            actions = current_state.get_legal_actions()
            if not actions:
                break
            
            action = random.choice(actions)
            try:
                if action['type'] == 'bid':
                    current_state.process_bid(action['value'])
                elif action['type'] == 'play_card':
                    current_state.play_card(action['card'], action['player'])
            except Exception as e:
                # If action fails, break simulation
                break
            
            moves_made += 1
        
        return current_state.get_final_scores()
    
    def backpropagate(self, result, ai_player):
        self.visits += 1
        # Calculate reward for AI player
        if ai_player in result and result:
            # Use normalized score relative to other players
            scores = list(result.values())
            if scores:
                ai_score = result[ai_player]
                avg_score = sum(scores) / len(scores)
                # Normalize reward to [-1, 1] range
                max_diff = max(abs(s - avg_score) for s in scores) if len(scores) > 1 else 1
                if max_diff > 0:
                    self.wins += (ai_score - avg_score) / max_diff
        
        if self.parent:
            self.parent.backpropagate(result, ai_player)

class ISMCTSAIPlayer:
    def __init__(self, player_name, iterations=1000):
        self.player_name = player_name
        self.iterations = iterations
        self.time_limit = 2.0  # 2 seconds per move
        self.card_play_iterations = 500  # Iterations for card play decisions
    
    def determinize_game_state(self, game_state, player_perspective):
        """Create a determinized version of the game state from player's perspective"""
        try:
            # This is a key part of ISMCTS - we sample unknown information
            det_state = copy.deepcopy(game_state)
            
            # Get cards the player can see (their own hand + played cards)
            visible_cards = set()
            visible_cards.update(game_state.players[player_perspective]["hand"])
            visible_cards.update(game_state.played_cards.values())
            if game_state.trump_card and game_state.trump_card not in ["Wizard", "Fool"]:
                visible_cards.add(game_state.trump_card)
            
            # Calculate remaining cards
            all_cards = set(create_deck())
            remaining_cards = list(all_cards - visible_cards)
            random.shuffle(remaining_cards)
            
            # Count how many cards each other player should have
            cards_per_player = game_state.round_num
            
            # Distribute remaining cards to other players
            card_index = 0
            for player_name, player_info in det_state.players.items():
                if player_name != player_perspective:
                    # Only replace cards if we have enough remaining cards
                    cards_needed = cards_per_player - len(game_state.played_cards.get(player_name, []))
                    if card_index + cards_needed <= len(remaining_cards):
                        player_info["hand"] = remaining_cards[card_index:card_index + cards_needed]
                        card_index += cards_needed
                    # If not enough cards, keep original hand (shouldn't happen in normal game)
            
            return det_state
        except Exception as e:
            # If determinization fails, return original state
            return copy.deepcopy(game_state)
    
    def run_ismcts(self, game_state, iterations, time_limit=None):
        """Run ISMCTS algorithm and return the best action"""
        start_time = time.time()
        
        # Create root node
        root = ISMCTSNode(game_state)
        root.initialize_actions()
        
        if not root.untried_actions:
            return None
        
        # Run ISMCTS iterations
        for i in range(iterations):
            if time_limit and time.time() - start_time > time_limit:
                break
                
            # Selection and Expansion
            node = root
            path = [node]
            
            # Selection phase - traverse down the tree
            while node.is_fully_expanded() and node.children and not node.is_terminal:
                node = node.best_child()
                path.append(node)
            
            # Expansion phase - add a new child node
            if not node.is_terminal and node.untried_actions:
                node = node.expand()
                if node:
                    path.append(node)
            
            # Simulation phase - run random playout
            result = node.simulate()
            
            # Backpropagation phase
            for node in path:
                node.backpropagate(result, self.player_name)
        
        # Return best action
        if root.children:
            best_child = root.best_child(c_param=0)  # Exploitation only for final selection
            return best_child.action if best_child else None
        
        return None
    
    def get_bid(self, game_state):
        """Use ISMCTS to determine the best bid"""
        start_time = time.time()
        
        # Simple fallback if ISMCTS fails
        try:
            # Get legal bids
            legal_bids = list(range(game_state.round_num + 1))
            
            # For very simple cases, use heuristics
            if len(legal_bids) <= 2 or self.iterations < 100:
                return self.simple_bid_heuristic(game_state)
            
            # Run ISMCTS with multiple determinizations
            bid_scores = defaultdict(float)
            bid_counts = defaultdict(int)
            
            '''determinizations = min(5, max(1, self.iterations // 200))
            iterations_per_det = max(10, self.iterations // determinizations)
            '''
            determinizations = 1000
            iterations_per_det = 100

            
            for det_num in range(determinizations):
                if time.time() - start_time > self.time_limit * 0.8:
                    break
                    
                det_state = self.determinize_game_state(game_state, self.player_name)
                
                # Run ISMCTS for each possible bid
                for bid in legal_bids:
                    if time.time() - start_time > self.time_limit * 0.8:
                        break
                    
                    score = self.evaluate_bid(det_state, bid, iterations_per_det // len(legal_bids))
                    bid_scores[bid] += score
                    bid_counts[bid] += 1
            
            # Choose best bid
            if bid_scores:
                # Average scores across determinizations
                avg_scores = {bid: score / bid_counts[bid] for bid, score in bid_scores.items()}
                best_bid = max(avg_scores.keys(), key=lambda x: avg_scores[x])
                return best_bid
            else:
                print('Fallack Bid')
                return self.simple_bid_heuristic(game_state)
                
        except Exception as e:
            # Fallback to simple heuristic
            print('Fallack Bid Exception')
            return self.simple_bid_heuristic(game_state)
    
    def simple_bid_heuristic(self, game_state):
        """Simple bidding heuristic as fallback"""
        hand = game_state.players[self.player_name]["hand"]
        
        # Count strong cards
        strong_cards = 0
        for card in hand:
            if card == "Wizard":
                strong_cards += 1
            elif card != "Fool":
                rank = int(card[:-1])
                if rank >= 10:  # High cards
                    strong_cards += 0.7
                elif rank >= 7:  # Medium cards
                    strong_cards += 0.3
        
        # Bid based on strong cards, but add some randomness
        base_bid = min(game_state.round_num, int(strong_cards + 0.5))
        return max(0, min(game_state.round_num, base_bid + random.randint(-1, 1)))
    
    def evaluate_bid(self, det_state, bid, iterations):
        """Evaluate a specific bid using limited ISMCTS"""
        try:
            # Create state with this bid
            temp_state = copy.deepcopy(det_state)
            temp_state.process_bid(bid)
            
            # Quick simulation-based evaluation instead of full ISMCTS
            wins = 0
            total_sims = min(iterations, 50)  # Limit simulations
            
            for _ in range(total_sims):
                sim_state = copy.deepcopy(temp_state)
                result = self.quick_simulate(sim_state)
                if result and self.player_name in result:
                    scores = list(result.values())
                    ai_score = result[self.player_name]
                    avg_score = sum(scores) / len(scores)
                    if ai_score >= avg_score:
                        wins += 1
            
            return wins / total_sims if total_sims > 0 else 0.5
            
        except Exception as e:
            return 0.5  # Neutral score if evaluation fails
    
    def quick_simulate(self, game_state):
        """Quick simulation to end of round"""
        try:
            max_moves = 50
            moves_made = 0
            
            while not game_state.is_terminal() and moves_made < max_moves:
                if game_state.phase == GamePhase.BIDDING:
                    # Make random bids for remaining players
                    current_player = game_state.get_current_player()
                    if current_player not in game_state.bids:
                        bid = random.randint(0, game_state.round_num)
                        game_state.process_bid(bid)
                elif game_state.phase == GamePhase.PLAYING:
                    # Play random legal cards
                    current_player = game_state.get_current_player()
                    legal_cards = [card for card in game_state.players[current_player]["hand"]
                                 if game_state.can_play_card(card, current_player)]
                    if legal_cards:
                        card = random.choice(legal_cards)
                        game_state.play_card(card, current_player)
                    else:
                        break
                else:
                    break
                    
                moves_made += 1
            
            return game_state.get_final_scores()
            
        except Exception as e:
            return {}
    
    def get_card_play(self, game_state):
        """Use ISMCTS to determine the best card to play"""
        start_time = time.time()
        
        try:
            # Get legal cards
            player_hand = game_state.players[self.player_name]["hand"]
            legal_cards = [card for card in player_hand 
                          if game_state.can_play_card(card, self.player_name)]
            
            if len(legal_cards) == 1:
                return legal_cards[0]
            
            if not legal_cards:
                return player_hand[0] if player_hand else None
            
            # Run ISMCTS with multiple determinizations for card play
            card_scores = defaultdict(float)
            card_counts = defaultdict(int)
            
            '''  # Use fewer determinizations for card play to save time
            determinizations = min(3, max(1, self.card_play_iterations // 100))
            iterations_per_det = max(20, self.card_play_iterations // determinizations)'''

            determinizations = 1000
            iterations_per_det = 100


            for det_num in range(determinizations):
                if time.time() - start_time > self.time_limit * 0.9:
                    break
                    
                det_state = self.determinize_game_state(game_state, self.player_name)
                
                # Evaluate each legal card using ISMCTS
                for card in legal_cards:
                    if time.time() - start_time > self.time_limit * 0.9:
                        break
                    
                    score = self.evaluate_card_play(det_state, card, iterations_per_det // len(legal_cards))
                    card_scores[card] += score
                    card_counts[card] += 1
            
            # Choose best card
            if card_scores:
                # Average scores across determinizations
                avg_scores = {card: score / card_counts[card] for card, score in card_scores.items()}
                best_card = max(avg_scores.keys(), key=lambda x: avg_scores[x])
                return best_card
            else:
                print('Fallack Play')
                return self.simple_card_heuristic(game_state, legal_cards)
                
        except Exception as e:
            # Fallback to simple heuristic
            print('Fallack Play Exception')
            player_hand = game_state.players[self.player_name]["hand"]
            legal_cards = [card for card in player_hand 
                          if game_state.can_play_card(card, self.player_name)]
            return self.simple_card_heuristic(game_state, legal_cards) if legal_cards else None
    
    def evaluate_card_play(self, det_state, card, iterations):
        """Evaluate a specific card play using ISMCTS"""
        try:
            # Create state after playing this card
            temp_state = copy.deepcopy(det_state)
            temp_state.play_card(card, self.player_name)
            
            # Run ISMCTS from this state
            best_action = self.run_ismcts(temp_state, iterations, self.time_limit * 0.1)
            
            # Run multiple simulations to get average score
            wins = 0
            total_sims = min(iterations // 2, 25)  # Limit simulations
            
            for _ in range(total_sims):
                sim_state = copy.deepcopy(temp_state)
                result = self.quick_simulate(sim_state)
                if result and self.player_name in result:
                    scores = list(result.values())
                    ai_score = result[self.player_name]
                    avg_score = sum(scores) / len(scores)
                    # Normalize score
                    if ai_score >= avg_score:
                        wins += 1
            
            return wins / total_sims if total_sims > 0 else 0.5
            
        except Exception as e:
            return 0.5  # Neutral score if evaluation fails
    
    def simple_card_heuristic(self, game_state, legal_cards):
        """Simple heuristic for card selection as fallback"""
        try:
            if not legal_cards:
                return None
                
            # If we have a Wizard, play it
            for card in legal_cards:
                if card == "Wizard":
                    return card
            
            # Analyze the current trick
            played_cards = game_state.played_cards
            led_suit = game_state.led_suit
            trump_suit = game_state.trump_suit
            
            # If we're leading, play strategically
            if not played_cards:
                # Lead with high card if we want to win, low if we want to lose
                non_special = [c for c in legal_cards if c not in ["Wizard", "Fool"]]
                if non_special:
                    non_special.sort(key=lambda x: int(x[:-1]))
                    return non_special[-1]  # Play highest
                return legal_cards[0]
            
            # If following, try to follow suit appropriately
            if led_suit:
                suit_cards = [c for c in legal_cards if c != "Fool" and c != "Wizard" and c[-1] == led_suit]
                if suit_cards:
                    # Play lowest if we don't want the trick, highest if we do
                    suit_cards.sort(key=lambda x: int(x[:-1]))
                    return suit_cards[0]  # Play lowest for now
            
            # Play Fool if available (doesn't win but doesn't waste good card)
            for card in legal_cards:
                if card == "Fool":
                    return card
            
            # Play lowest card
            non_special = [c for c in legal_cards if c not in ["Wizard", "Fool"]]
            if non_special:
                non_special.sort(key=lambda x: int(x[:-1]))
                return non_special[0]
            
            return legal_cards[0]
            
        except Exception as e:
            return legal_cards[0] if legal_cards else None

# Extensions to WizardGame class to support ISMCTS
class ISMCTSWizardGame(WizardGame):
    def __init__(self, num_players=4):
        super().__init__(num_players)
        # Replace simple AI with ISMCTS AI
        self.ai_players = {}
        for player_name, player_info in self.players.items():
            if not player_info["is_human"]:
                
                self.ai_players[player_name] = ISMCTSAIPlayer(player_name)
    
    def get_current_player(self):
        """Get the current player name"""
        if 0 <= self.current_player_index < len(self.player_names):
            return self.player_names[self.current_player_index]
        return None
    
    def get_legal_actions(self):
        """Get legal actions for current game state"""
        actions = []
        current_player = self.get_current_player()
        
        if not current_player:
            return actions
        
        try:
            if self.phase == GamePhase.BIDDING:
                # Legal bids are 0 to number of cards in hand
                for bid_value in range(self.round_num + 1):
                    actions.append({
                        'type': 'bid',
                        'value': bid_value,
                        'player': current_player
                    })
            elif self.phase == GamePhase.PLAYING:
                # Legal cards to play
                if current_player in self.players:
                    player_hand = self.players[current_player]["hand"]
                    for card in player_hand:
                        if self.can_play_card(card, current_player):
                            actions.append({
                                'type': 'play_card',
                                'card': card,
                                'player': current_player
                            })
        except Exception as e:
            pass
        
        return actions
    
    def is_terminal(self):
        """Check if game is in terminal state"""
        return self.phase == GamePhase.GAME_OVER
    
    def get_final_scores(self):
        """Get final scores for terminal evaluation"""
        return self.scores.copy()
    
    def update(self):
        """Override update to use ISMCTS AI"""
        current_time = pygame.time.get_ticks()
        
        # Handle next round timer
        if self.next_round_timer > 0 and current_time >= self.next_round_timer:
            self.next_round_timer = 0
            self.start_new_round()
        
        # Handle AI moves with ISMCTS
        if self.phase == GamePhase.BIDDING:
            current_player = self.player_names[self.current_player_index]
            if not self.players[current_player]["is_human"]:
                if self.ai_timer == 0:
                    self.ai_timer = current_time + 500  # Half second delay for UI
                elif current_time >= self.ai_timer:
                    self.ai_timer = 0
                    try:
                        # Use ISMCTS for bidding
                        ai_bid = self.ai_players[current_player].get_bid(self)
                        self.process_bid(ai_bid)
                    except Exception as e:
                        # Fallback to random bid
                        ai_bid = random.randint(0, self.round_num)
                        self.process_bid(ai_bid)
        
        elif self.phase == GamePhase.PLAYING:
            current_player = self.player_names[self.current_player_index]
            if not self.players[current_player]["is_human"]:
                if self.ai_timer == 0:
                    self.ai_timer = current_time + 1000  # Longer delay for card play ISMCTS
                elif current_time >= self.ai_timer:
                    self.ai_timer = 0
                    try:
                        # Use ISMCTS for card play
                        card_to_play = self.ai_players[current_player].get_card_play(self)
                        if card_to_play:
                            self.play_card(card_to_play, current_player)
                    except Exception as e:
                        # Fallback to first legal card
                        hand = self.players[current_player]["hand"]
                        legal_cards = [card for card in hand 
                                     if self.can_play_card(card, current_player)]
                        if legal_cards:
                            self.play_card(legal_cards[0], current_player)