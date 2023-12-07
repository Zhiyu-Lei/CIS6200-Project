import random
from random import random, shuffle
import numpy as np
from typing import List


def DeckCreator():
    card_list = []
    suits = ["S", "C", "H", "D"]

    for s in suits:
        for i in range(2, 15):
            card_list.append((i, s))

    shuffle(card_list)

    return card_list


class HeartsGame:
    def __init__(self):
        self.player_cards = [[] for i in range(4)]
        self.player_trick_value = [0] * 4
        self.player_scores = [0] * 4
        self.current_pile = []
        self.current_suit = None
        self.first_player = 0

        self.NewHand()

    def NewHand(self):
        self.Shuffle()
        for i in range(4):
            for j in range(13):
                self.player_cards[i].append(self.deck.pop())

    def Shuffle(self):
        self.deck = DeckCreator()

    def PlayAction(self, player, card):
        if card in self.player_cards[player]:
            self.player_cards[player].remove(card)
            self.current_pile.append((player, card))

            if self.current_suit == None:
                self.current_suit = card[1]
            
            return True

        else:
            print("Card not in player's hand")

            return False

    def EvaluatePile(self):
        winning_player = 0
        winning_value = 0
        pile_value = 0

        for player, card in self.current_pile:
            if card[1] == self.current_suit and card[0] > winning_value:
                winning_player = player
                winning_value = card[0]
            if card[1] == "H":
                pile_value += 1
            elif card[1] == "S" and card[0] == 12:
                pile_value += 13

        self.player_trick_value[winning_player] += pile_value
        self.first_player = winning_player
        self.current_pile = []
        self.current_suit = None

        return winning_player, pile_value

    def UpdateScores(self):
        if 26 in self.player_trick_value:
            self.player_trick_value = [0 if self.player_trick_value[i] == 26 else 26 for i in range(4)]
        for i in range(len(self.player_scores)):
            self.player_scores[i] += self.player_trick_value[i]
            self.player_trick_value[i] = 0

    def PlayerInput(self, player):
        while(True):
            print("Current Player: " + str(player))
            print("Current Suit: " + str(self.current_suit))
            print("Current Pile: " + str(self.current_pile))
            print("Current Hand: " + str(self.player_cards[player]))
            card_str = input("Play Card: ")
            card = (int(card_str[0:-1]), card_str[-1])
            if self.PlayAction(player, card):
                break

    def PlayerGame(self):
        for i in range(13):
            for i in range(4):
                self.PlayerInput((i + self.first_player) % 4)
            print(self.EvaluatePile())
            print(self.player_trick_value)
        self.UpdateScores()
        print(self.player_scores)


class BJTrainer:
    """BJ and CFR problem definitions. P:PASS D:DRAW I:INSURANCE U:UNINSURANCE"""

    NUM_ACTIONS = 2
    # str -> Node
    nodeMap = dict()

    class Node:
        """Information set node class definition."""

        def __init__(self):
            """Kuhn node definitions."""
            self.infoSet: str = ""
            self.NUM_ACTIONS = BJTrainer().NUM_ACTIONS
            self.regretSum = np.zeros(self.NUM_ACTIONS, dtype=float)
            self.strategy = np.zeros(self.NUM_ACTIONS, dtype=float)
            self.strategySum = np.zeros(self.NUM_ACTIONS, dtype=float)

        def getStrategy(self, realizationWeight: float):
            """Get current information set mixed strategy through regret-matching."""
            normalizingSum: float = 0
            for a in range(self.NUM_ACTIONS):
                self.strategy[a] = self.regretSum[a] if self.regretSum[a] > 0 else 0
                normalizingSum += self.strategy[a]
            for a in range(self.NUM_ACTIONS):
                if normalizingSum > 0:
                    self.strategy[a] /= normalizingSum
                else:
                    self.strategy[a] = 1 / self.NUM_ACTIONS
                self.strategySum[a] += realizationWeight * self.strategy[a]
            return self.strategy

        def getAverageStrategy(self):
            """Get average information set mixed strategy across all training iterations."""
            avgStrategy = np.zeros(self.NUM_ACTIONS, dtype=float)
            normalizingSum: float = sum(self.strategySum)
            for a in range(self.NUM_ACTIONS):
                if normalizingSum > 0:
                    avgStrategy[a] = self.strategySum[a] / normalizingSum
                else:
                    avgStrategy[a] = 1 / self.NUM_ACTIONS
            return avgStrategy

        def __str__(self):
            """Get information set string representation."""
            return f"{self.infoSet}: {self.getAverageStrategy()}"

    def __init__(self):
        pass

    def train(self, iterations: int) -> None:
        game = HeartsGame()
        util: float = 0
        for i in range(iterations):
            """Shuffle cards. and give two cards to player and dealer"""
            game.NewHand()
            util += self.cfr(game, "", 1, 1, 1, 1)

        with open("output_file1", "w") as file:
            for n in self.nodeMap.values():
                file.write(str(n) + "\n")

        print(f"Average game value: {util / iterations}")

    def cfr(self, game: HeartsGame, history: str, p0: float, p1: float, p2: float, p3: float) -> float:
        """Counterfactual regret minimization iteration."""
        num_rounds = len(history)
        player = num_rounds % 4

        """Return payoff for terminal states. """

        if num_rounds >= 4:
            gaining_player, pile_value = game.EvaluatePile()
            return (16 - pile_value) / 16

        infoSet: str = f"{game.player_cards[player]} {history} "

        """Get information set node or create it if nonexistant. """
        node = self.nodeMap.get(infoSet)

        if node is None:
            node = self.Node()
            node.infoSet = infoSet
            self.nodeMap[infoSet] = node
            

        """For each action, recursively call cfr with additional history and probability. """
        strategy: float = node.getStrategy(p0)
        util: float = np.zeros(self.NUM_ACTIONS, dtype=float)
        nodeUtil: float = 0
        for a in range(self.NUM_ACTIONS):
            nextHistory = history + ("p" if a == 0 else "b")

            match player:
                case 0:
                    util[a] = self.cfr(game, nextHistory, p0 * strategy[a], p1, p2, p3)
                case 1:
                    util[a] = self.cfr(game, nextHistory, p0, p1 * strategy[a], p2, p3)
                case 2:
                    util[a] = self.cfr(game, nextHistory, p0, p1, p2 * strategy[a], p3)
                case 3:
                    util[a] = self.cfr(game, nextHistory, p0, p1, p2, p3 * strategy[a])

            nodeUtil += strategy[a] * util[a]

        """For each action, compute and accumulate counterfactual regret. """
        for a in range(self.NUM_ACTIONS):
            regret: float = util[a] - nodeUtil
            node.regretSum[a] += regret

        return nodeUtil


def main():
    iterations: int = 10000
    trainer: BJTrainer = BJTrainer()
    trainer.train(iterations)
    #game = HeartsGame()
    #game.PlayerGame()


if __name__ == "__main__":
    main()
