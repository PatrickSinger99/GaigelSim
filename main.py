import random
from queue import Queue


class Card:
    card_types = {"k": "karo", "h": "herz", "p": "pik", "z": "kreuz"}
    card_values = {0: "sieben", 2: "bube", 3: "dame", 4: "könig", 10: "zehn", 11: "ass"}
    card_id_count = 0

    def __init__(self, card_value, card_type):
        # Set Card Type and Value
        self.value = card_value
        self.type = card_type

        # Set ID
        self.id = Card.card_id_count
        Card.card_id_count += 1

    def __str__(self):
        return f"[CARD] {Card.card_types[self.type]} {Card.card_values[self.value]} ({self.value})\n"

    def val(self):
        return self.type + str(self.value)


class Player:
    player_id_count = 0

    def __init__(self, name):
        # Set Player Properties
        self.name = name
        self.points = 0
        self.cards_hand = {1: None, 2: None, 3: None, 4: None, 5: None}
        self.cards_played = []

        # Set ID
        self.id = Player.player_id_count
        Player.player_id_count += 1

    def get_num_cards(self):
        return sum(1 for value in self.cards_hand.values() if value is not None)

    def get_action(self):
        # TODO TEMP
        possible_moves = [key for key, value in self.cards_hand.items() if value is not None]
        return random.choice(possible_moves)


class GaigelSim:
    card_types = {"k": "karo", "h": "herz", "p": "pik", "z": "kreuz"}
    card_values = {0: "sieben", 2: "bube", 3: "dame", 4: "könig", 10: "zehn", 11: "ass"}
    moves = {1: "play_card_1", 2: "play_card_2", 3: "play_card_3", 4: "play_card_4", 5: "play_card_5"}

    # TODO: Eröffnungsrunde Höher bzw zweites ass
    # TODO: Melden
    # TODO: Ass unter stapel eintauschen
    # TODO: Farbe bekennen
    # TODO: Valid Move function

    def __init__(self, players: int):
        # Initialize game variables
        self.card_stack = Queue(maxsize=48)
        self.players = Queue(maxsize=players)
        self.trump_suit = None  # trump card under stack
        self.trump = None
        self.match_color = False
        self.card_round_stack = []
        self.card_placed_by = []  # Tracks which player placed which card in the card_round_stack
        self.current_player = None
        self.game_over = False

        # Game time tracking
        self.current_round = 0
        self.current_turn = 0  # The progress within one round (Depending on the number of players)

        # Create new deck
        for card_type in GaigelSim.card_types.keys():
            for card_value in GaigelSim.card_values.keys():
                # Add 2 cards for every possible type to the stack
                self.card_stack.put(Card(card_value, card_type))
                self.card_stack.put(Card(card_value, card_type))

        # Create players
        for i in range(players):
            self.players.put(Player("player_" + str(i + 1)))

        # Initial actions
        self.shuffle_stack()
        self.select_starting_player()
        self.hand_out_cards()

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
        random.shuffle(self.card_stack.queue)

    def hand_out_cards(self):
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
        self.current_player = random.choice(self.players.queue)

        # Rotate player queue to selected player
        self.rotate_queue_to_player(self.current_player)

        print(f"[STATUS] Selected starting player {self.current_player.name}")

    def rotate_queue_to_player(self, player):
        while self.players.queue[0] != player:
            rotated_player = self.players.get()
            self.players.put(rotated_player)

    def draw_card(self, player):
        empty_slot = list(player.cards_hand.keys())[list(player.cards_hand.values()).index(None)]
        player.cards_hand[empty_slot] = self.card_stack.get()
        print(f"[ACTION] {player.name} draws card {player.cards_hand[empty_slot].val()}")

    def draw_card_and_rotate(self):
        # Select next player and put them back in the queue
        self.current_player = self.players.get()
        self.players.put(self.current_player)

        # Draw card from stack
        self.draw_card(self.current_player)

    def determine_winner(self):
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
        winner.points += self.card_round_stack[winner_index].value

        print(f"[STATUS] {winner.name} wins the round")

        return winner

    def validate_game_over(self):
        for player in self.players.queue:
            if player.get_num_cards() == 0:
                self.game_over = True
                return self.game_over

        return self.game_over

    def play_round(self):

        # Reset current turn count and increment round count
        self.current_round += 1
        self.current_turn = 0

        # Reset turn variables
        self.card_round_stack = []
        self.card_placed_by = []

        # PART 1: Every player plays a card
        for _ in range(self.players.qsize()):
            # Select next player and put them back in the queue
            self.current_player = self.players.get()
            self.players.put(self.current_player)

            # Advance turn count
            self.current_turn += 1

            player_action = self.current_player.get_action()

            # Place card
            if 1 <= player_action <= 5:
                print(f"[ACTION] {self.current_player.name} played {self.current_player.cards_hand[player_action].val()}")

                # Add selected card to current round stack and remove from players hand
                self.card_round_stack.append(self.current_player.cards_hand[player_action])
                self.current_player.cards_hand[player_action] = None
                self.card_placed_by.append(self.current_player)

        # Select winner and rotate player queue to them
        winner = self.determine_winner()
        self.rotate_queue_to_player(winner)

        # PART 2: Every player draws a card starting at the winner
        for _ in range(self.players.qsize()):
            if self.card_stack.qsize() > 0 and not self.match_color:
                self.draw_card_and_rotate()
            else:
                # Stack used up. Rotate player without drawing card (Ab hier farbe bekennen)
                self.current_player = self.players.get()
                self.players.put(self.current_player)
                if not self.match_color:
                    print(f"{self.current_player.name} skipped card draw due to empty stack")

        # Switch to farbe bekennen, if stack is empty
        if self.card_stack.qsize() == 0:
            self.match_color = True

        # Check game over conditions
        if self.validate_game_over():
            print("[STATUS] Game over")

    def run(self):
        while not self.game_over:
            self.play_round()
            print(self)


if __name__ == '__main__':
    sim = GaigelSim(3)
    sim.run()

