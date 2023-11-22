import random
from queue import Queue


class Card:
    card_types = {"k": "karo", "h": "herz", "p": "pik", "z": "kreuz"}
    card_values = {0: "sieben", 2: "bube", 3: "dame", 4: "könig", 10: "zehn", 11: "ass"}
    card_id_count = 0

    def __init__(self, card_value: int, card_type: str):
        # Set Card Type and Value
        self.value = card_value
        self.type = card_type

        # Set ID
        self.id = Card.card_id_count
        Card.card_id_count += 1

    def __str__(self):
        return f"[CARD] {Card.card_types[self.type]} {Card.card_values[self.value]} ({self.value})\n"

    def val(self):
        """
        Returns a short card string to identify the card. Example: "k0", "h3", etc.
        :return: String containing card type and value
        """
        return self.type + str(self.value)


class Player:
    player_id_count = 0

    def __init__(self, name: str):
        # Set Player Properties
        self.name = name
        self.points = 0
        self.cards_hand = {1: None, 2: None, 3: None, 4: None, 5: None}
        self.cards_played = []

        # Set ID
        self.id = Player.player_id_count
        Player.player_id_count += 1

    def get_num_cards(self):
        """
        Gets the number of cards the player has on hand
        :return: Integer number of cards
        """
        return sum(1 for value in self.cards_hand.values() if value is not None)

    def get_action(self, state):
        """
        Returns an action for the given state by the simulation. This can be integrated into a RL Agent etc.
        :param state: State of the current simulation. Array of card value indices
        :return: Player action choice
        """
        # TODO TEMP currently picks random. State not used
        possible_moves = [key for key, value in self.cards_hand.items() if value is not None]
        return random.choice(possible_moves)


class GaigelSim:
    card_types = {"k": "karo", "h": "herz", "p": "pik", "z": "kreuz"}
    card_values = {0: "sieben", 2: "bube", 3: "dame", 4: "könig", 10: "zehn", 11: "ass"}
    moves = {0: "switch_trump_suit", 1: "play_card_1", 2: "play_card_2", 3: "play_card_3", 4: "play_card_4",
             5: "play_card_5", 6: "melding", 7: "second_ace", 8: "higher"}  # TODO not used

    # TODO: Eröffnungsrunde Höher bzw zweites ass
    # TODO: Melden
    # TODO: Ass unter stapel eintauschen
    # TODO: Farbe bekennen
    # TODO: Group play (Über kreuz)

    def __init__(self, players: int, verbose: bool = False):

        # General Game state variables
        self.card_stack = Queue(maxsize=48)
        self.players = Queue(maxsize=players)
        self.trump_suit = None  # trump card under stack
        self.trump = None  # "Trumpf"
        self.match_color = False  # "Farben bekennen" if card stack is empty
        self.game_over = False
        self.game_winners = []
        self.verbose = verbose

        # Round variables
        self.card_round_stack = []  # Cards placed in a round. Gets reset each round
        self.card_placed_by = []  # Tracks which player placed which card in the card_round_stack
        self.current_player = None  # Player that has the next turn

        # Game time tracking
        self.current_round = 0
        self.current_turn = 0  # The progress within one round (Depending on the number of players)

        # State translation lookups. Get filled during deck creation
        self.ids_by_card = {None: 0}
        self.cards_by_id = {0: None}
        self.trump_ids = {item[0]: i for i, item in enumerate(GaigelSim.card_types.items())}

        # Create new deck. (Standard "Württembergisches Blatt" 48 cards, 2 of each type)
        card_id = 1
        for card_type in GaigelSim.card_types.keys():
            for card_value in GaigelSim.card_values.keys():
                # Add 2 cards for every possible type to the stack
                self.card_stack.put(Card(card_value, card_type))
                self.card_stack.put(Card(card_value, card_type))

                # Assign an id to every card type (Used for observation space)
                self.ids_by_card[card_type + str(card_value)] = card_id
                self.cards_by_id[card_id] = card_type + str(card_value)
                card_id += 1

        # Create players
        for i in range(players):
            self.players.put(Player("player_" + str(i + 1)))

    def __str__(self):
        return_string = f"{'='*30} Round {self.current_round} | Turn {self.current_turn} {'='*30}\n"
        banner_width = len(return_string)

        return_string += (f"[CARD STACK] ({self.card_stack.qsize()} cards) "
                          f"{', '.join([card.val() for card in self.card_stack.queue])}")

        if self.match_color:
            return_string += "--MATCH COLOR ACTIVE--"

        return_string += f"\n[TRUMP SUIT] {self.trump_suit.val()}"
        return_string += f" | [TRUMP] {self.trump}"
        return_string += f" | [CURRENT ROUND STACK] {', '.join([card.val() for card in self.card_round_stack])}"

        for player in self.players.queue:
            return_string += (f"\n[PLAYER: {player.name}] {'(current turn) ' if player == self.current_player else ''}"
                              f"({player.get_num_cards()} cards, {player.points} points) "
                              f"{', '.join([card.val() if card is not None else '-' for card in player.cards_hand.values()])}")

        return_string += "\n" + "="*(banner_width - 1)

        return return_string

    def shuffle_stack(self):
        """
        Randomly shuffles the card stack
        """
        random.shuffle(self.card_stack.queue)

        if self.verbose:
            print("[STATUS] Shuffled card stack")

    def hand_out_cards(self):
        """
        Hands out cards from the stack to all players according to gaigel rules. First hand out 3 rounds of cards,
        then select the trump suit, the hand out the remaining 2 rounds of cards.
        """

        if self.verbose:
            print("[STATUS] Handing out cards to players")

        # Hand out first 3 cards for every player
        for i in range(1, 4):
            for _ in range(self.players.qsize()):
                self.draw_card_and_rotate()

        # Define card under stack (trump suit)
        self.trump_suit = self.card_stack.get()
        self.trump = self.trump_suit.type

        # Hand out last 2 cards for every player
        for i in range(4, 6):
            for _ in range(self.players.qsize()):
                self.draw_card_and_rotate()

    def select_starting_player(self):
        """
        Selects a random starting player and rotates queue to that player
        """
        self.current_player = random.choice(self.players.queue)

        # Rotate player queue to selected player
        self.rotate_queue_to_player(self.current_player)

        if self.verbose:
            print(f"[STATUS] Selected starting player {self.current_player.name}")

    def rotate_queue_to_player(self, player):
        """
        Rotates the player queue to the specified player
        :param player: Player class instance
        """
        while self.players.queue[0] != player:
            rotated_player = self.players.get()
            self.players.put(rotated_player)

    def draw_card(self, player):
        """
        Gives the specified player a card from the stack
        :param player: Player class instance
        """
        empty_slot = list(player.cards_hand.keys())[list(player.cards_hand.values()).index(None)]
        player.cards_hand[empty_slot] = self.card_stack.get()

        if self.verbose:
            print(f"[ACTION] {player.name} draws card {player.cards_hand[empty_slot].val()}")

    def draw_card_and_rotate(self):
        """
        Gives the current player a card from the stack and rotates the current player queue once forward
        """
        # Select next player and put them back in the queue
        self.current_player = self.players.get()
        self.players.put(self.current_player)

        # Draw card from stack
        self.draw_card(self.current_player)

    def determine_round_winner(self):
        """
        Counts up all played cards during current round and selects round winner. Winners points are added.
        :return: Player class instance of winner
        """
        start_type = self.card_round_stack[0].type
        card_round_values = []

        # Calculate points for every card
        for card in self.card_round_stack:
            card_value = card.value
            # Add 1000 if it is a trump
            if card.type == self.trump:
                card_value += 1000
            # Add 100 if it is a round start type
            elif card.type == start_type:
                card_value += 100

            card_round_values.append(card_value)

        # Determine winner by card score
        winner_index = card_round_values.index(max(card_round_values))
        winner = self.card_placed_by[winner_index]

        # Add points for winner
        played_cards_points = sum([card.value for card in self.card_round_stack])
        winner.points += played_cards_points

        if self.verbose:
            print(f"[STATUS] {winner.name} wins the round (+{played_cards_points} points)")

        return winner

    def determine_game_winner(self):
        """
        Sets the game winner in the class variable. Multiple winners are possible
        :return: Game winner(s)
        """
        max_points = max([player.points for player in self.players.queue])

        for player in self.players.queue:
            if player.points == max_points:
                self.game_winners.append(player)

        return self.game_winners

    def validate_move(self, player, move_id):
        """
        Takes a player and move id and checks if the move is valid in the current state of the game
        :param player: Player class instance
        :param move_id: move id of the players action according to the class variable "moves"
        :return: Boolean if move is valid or not
        """

        # CASE: Play card from hand
        if 1 <= move_id <= 5:
            # Check if player has card on position
            if player.cards_hand[move_id] is None:
                if self.verbose:
                    print(f"[INVALID MOVE] {player.name} tried playing card in position {move_id}, but has no card "
                          f"in position {move_id}")
                return False

            # Check if match color is followed, if active
            if self.match_color and len(self.card_round_stack) > 0:
                type_to_be_matched = self.card_round_stack[0].type
                player_hand_card_types = [card.type if card is not None else card for card in player.cards_hand.values()]
                player_has_type = True if type_to_be_matched in player_hand_card_types else False

                if player_has_type and player.cards_hand[move_id].type != type_to_be_matched:
                    print(f"[INVALID MOVE] {player.name} tried playing card type {player.cards_hand[move_id].type}, "
                          f"when type match for type {type_to_be_matched} is active")
                    return False

        # All checks passed
        return True

    def validate_game_over(self):
        """
        Checks if a game over condition is reached. Game over if player cards are empty or player has over 101 points
        :return: Boolean if game over
        """

        for player in self.players.queue:
            if player.get_num_cards() == 0 or player.points >= 101:
                self.game_over = True
                return self.game_over

        return self.game_over

    def get_state(self, player):
        """
        Get state for a player. This can be used to train decision making for a player agent
        State space: [0-3, 0-24 * 5, 0-24 * (players-1)]
        :param player: Player class instance
        :return: state array including ids for all cards on the players hand and cards placed in the round
        """
        # First part: trump
        trump_state = self.trump_ids[self.trump]

        # Second part: player hand
        hand_card_vals = [card.val() if card is not None else card for card in player.cards_hand.values()]
        hand_state = [self.ids_by_card[card_val] for card_val in hand_card_vals]

        # Third part: round stack
        stack_state = [self.ids_by_card[card.val()] for card in self.card_round_stack]
        while len(stack_state) != self.players.qsize() - 1:  # -1 bc a state with all players cards placed is finished
            stack_state.append(0)

        return {"trump_state": trump_state, "hand_state": hand_state, "stack_state": stack_state}

    def play_round(self):
        """
        Advances the simulation one round. Every player places a card, draws a new one, and determines a winner
        """

        # Reset current turn count and increment round count
        self.current_round += 1
        self.current_turn = 0

        # Reset turn variables
        self.card_round_stack = []
        self.card_placed_by = []

        if self.verbose:
            print(f"[STATUS] Starting round {self.current_round}")

        # PART 1: Every player plays a card
        for _ in range(self.players.qsize()):
            # Select next player and put them back in the queue
            self.current_player = self.players.get()
            self.players.put(self.current_player)

            # Advance turn count
            self.current_turn += 1

            # Get player action. Repeat if move was not valid
            while True:
                player_action = self.current_player.get_action(state=self.get_state(self.current_player))
                if self.validate_move(self.current_player, player_action):
                    break

            # Place card
            if 1 <= player_action <= 5:
                if self.verbose:
                    print(f"[ACTION] {self.current_player.name} played "
                          f"{self.current_player.cards_hand[player_action].val()}")

                # Add selected card to current round stack and remove from players hand
                self.card_round_stack.append(self.current_player.cards_hand[player_action])
                self.current_player.cards_hand[player_action] = None
                self.card_placed_by.append(self.current_player)

        # Select winner and rotate player queue to them
        winner = self.determine_round_winner()
        self.rotate_queue_to_player(winner)

        # PART 2: Every player draws a card starting at the winner
        for _ in range(self.players.qsize()):
            if self.card_stack.qsize() > 0 and not self.match_color:
                self.draw_card_and_rotate()
            else:
                # Stack used up. Rotate player without drawing card (Ab hier farbe bekennen)
                self.current_player = self.players.get()
                self.players.put(self.current_player)
                if not self.match_color and self.verbose:
                    print(f"[STATUS] {self.current_player.name} skipped card draw due to empty stack")

        # Switch to farbe bekennen, if stack is empty
        if self.card_stack.qsize() == 0:
            self.match_color = True

        # Check game over conditions
        if self.validate_game_over():

            self.determine_game_winner()

            if self.verbose:
                print(f"[STATUS] Game over. {'Winner is' if len(self.game_winners) == 1 else 'Winners are'} "
                      f"{', '.join([winner.name for winner in self.game_winners])}")

    def run(self):
        """
        Runs a complete gaigel simulation until game over
        """
        if self.verbose:
            print(f"[STATUS] Starting Gaigel simulation with {self.players.qsize()} players")

        # Initial actions
        self.shuffle_stack()
        self.select_starting_player()
        self.hand_out_cards()

        # Game loop
        while not self.game_over:
            self.play_round()
            if self.verbose:
                print(self)


if __name__ == '__main__':
    sim = GaigelSim(3, verbose=True)
    sim.run()
