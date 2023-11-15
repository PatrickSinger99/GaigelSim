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

    def get_action(self):
        # TODO TEMP
        return random.randint(1, 6)


class GaigelSim:
    card_types = {"k": "karo", "h": "herz", "p": "pik", "z": "kreuz"}
    card_values = {0: "sieben", 2: "bube", 3: "dame", 4: "könig", 10: "zehn", 11: "ass"}
    moves = {1: "play_card_1", 2: "play_card_2", 3: "play_card_3", 4: "play_card_4", 5: "play_card_5"}

    def __init__(self, players: int):
        # Initialize game variables
        self.card_stack = Queue(maxsize=48)
        self.players = Queue(maxsize=players)
        self.card_under_stack = None
        self.trumpf = None
        self.card_round_stack = []
        self.current_player = None

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
        self.hand_out_cards()
        self.select_starting_player()

    def __str__(self):
        return_string = (f"[CARD STACK] ({self.card_stack.qsize()} cards) "
                         f"{', '.join([card.val() for card in self.card_stack.queue])}")

        return_string += f"\n[CARD UNDER STACK] {self.card_under_stack.val()}"
        return_string += f"\n[TRUMPF] {self.trumpf}"
        return_string += f"\n[CURRENT ROUND STACK] {', '.join([card.val() for card in self.card_round_stack])}"

        for player in self.players.queue:
            return_string += (f"\n[PLAYER: {player.name}] {'(current turn) ' if player == self.current_player else ''}"
                              f"({len(player.cards_hand)} cards, {player.points} points) "
                              f"{', '.join([card.val() if card is not None else 'empty' for card in player.cards_hand.values()])}")  #

        return return_string

    def shuffle_stack(self):
        random.shuffle(self.card_stack.queue)

    def hand_out_cards(self):
        # Hand out first 3 cards for every player
        for i in range(1, 4):
            for player in self.players.queue:
                player.cards_hand[i] = self.card_stack.get()

        # Define card under stack (Trumpf)
        self.card_under_stack = self.card_stack.get()
        self.trumpf = self.card_under_stack.type

        # Hand out last 2 cards for every player
        for i in range(4, 6):
            for player in self.players.queue:
                player.cards_hand[i] = self.card_stack.get()

    def select_starting_player(self):
        self.current_player = random.choice(self.players.queue)

        # Rotate player queue to selected player
        while self.players.queue[0] != self.current_player:
            rotated_player = self.players.get()
            self.players.put(rotated_player)

    def play_round(self):

        # PART 1: Every player plays a card
        for _ in range(self.players.qsize()):
            self.current_player = self.players.get()
            self.players.put(self.current_player)

            player_action = self.current_player.get_action()

            # Place card
            if 1 <= player_action <= 5:
                print(self.current_player.name, "played", self.current_player.cards_hand[player_action].val())

                # Add selected card to current round stack and remove from players hand
                self.card_round_stack.append(self.current_player.cards_hand[player_action])
                self.current_player.cards_hand[player_action] = None

        # TODO select winner

        # PART 2: Every player draws a card starting at the winner
        for _ in range(self.players.qsize()):
            # TODO
            pass


if __name__ == '__main__':
    sim = GaigelSim(3)
    print(sim)
    sim.play_round()
    print(sim)
