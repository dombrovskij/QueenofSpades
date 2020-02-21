import numpy as np 
from random import shuffle
import random
from random import Random
import itertools
import operator
import pandas as pd
import matplotlib.pyplot as plt

class Cards:

    '''
    This class maintains the cards, shuffles them and deals them.
    '''

    def __init__(self):
        #Define the deck
        values = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        suites = ['H', 'S', 'C', 'D']
        self.deck = [(j,i) for j in values for i in suites]

    def shuffle(self, seed=False):
        #Shuffle the deck, if seed is true it will maintain the same shuffle
        if seed:
            myRandom = Random(8)
            myRandom.shuffle(self.deck)
        else:
            random.shuffle(self.deck)        

    def deal(self, n_players):
        #Deal the deck fully to n_players
        self.hands = [self.deck[i::n_players] for i in range(0, n_players)] #Every nth element in list

class Game:

    '''
    This class simulates the game 'Queen of Spades'.
    A full deck of cards gets dealt between n players. All of them lay off pairs of cards (based on value, suit doesn't matter).
    You're not allowed to lay off a pair containing the queen of spades. Then player 1 blindly picks a card from player n and lays of a pair if 
    he can. Then player 2 picks a card from player 1, lays off a pair if possible, etc.
    The loser is the player that holds the queen of spades when all other pairs have been discarded.
    '''

    def __init__(self, n_players, seed=False):

        self.n_players = n_players 
        self.c = Cards() #Deck of cards
        self.c.shuffle(seed=seed) #Shuffle it
        self.c.deal(self.n_players) #Deal to the players

        self.p_order = {} #Key = player whose turn it is, Value = player from whom player has to pick a card

        #Make them pick a card from the player 'before' them (so in opposite direction of playing direction)

        for i, p in enumerate(range(self.n_players)):
            if i == 0:
                self.p_order[p] = range(self.n_players)[-1]
            else:
                self.p_order[p] = range(self.n_players)[i-1]

        self.done = False #Keep track of whether a game is over or not
    
    def ditch_pairs(self, player):

        '''
        Lay off any pairs that the player is holding in his hand.
        '''

        #Loop through pairs
        for k,g in itertools.groupby(sorted(self.c.hands[player]), operator.itemgetter(0)): 
        
            g = [x for x in g]

            if ('Q','S') in g: #Queen of spades cannot be discarded
                g.remove(('Q','S'))

            while len(g) >= 2: #Need at least two cards to be able to have a pair

                del_pair = g[0:2]

                self.c.hands[player].remove(del_pair[0]) #Remove pair from hand
                self.c.hands[player].remove(del_pair[1])
                g.remove(del_pair[0]) #Remove pair from list we're looping through
                g.remove(del_pair[1])

    def check_done(self):

        #Done when all players 0 and one player a queen pair with (Q,S)

        queen_pair = False #Keep track of whether the Queen of Spades and any other queen is in the same hand
        total_cards = 0 #Count total cards still left in the game
        potential_loser = None #Keep track of potential loser (the one who has the queen pair including queen of spades)

        for p in range(self.n_players): #Loop through players
            total_cards += len(self.c.hands[p])

            if len(self.c.hands[p]) == 2: #If player only holding two cards

                firsts = [t[0] for t in self.c.hands[p]]
                seconds = [t[1] for t in self.c.hands[p]]

                if (firsts == ['Q','Q']) & ('S' in seconds): #Check whether a queen pair including queen of spades is in this hand
                    queen_pair = True 
                    potential_loser = p
        
        #If it turns out that somebody is holding the queen pair and the total cards in the game left is 2, then the game is over
        if (total_cards == 2) & queen_pair:
            self.loser = potential_loser
            self.done = True

    def readjust_order(self):

        '''
        When a player has an empty hand, they stop playing, so the player order needs to be readjusted.
        '''

        players = list(self.p_order.keys())
        new_players = players.copy()

        for q in players:
            #If hand is empty remove from player order
            if len(self.c.hands[q]) == 0:
                new_players.remove(q)

                if self.winner == None:
                    self.winner = q

                new_p_order = {}

                for i, p in enumerate(new_players):
                    if i == 0:
                        new_p_order[p] = new_players[-1]
                    else:
                        new_p_order[p] = new_players[i-1]
                self.p_order = new_p_order            

    def play(self, verbose=False):

        '''
        Play a game of Queen of Spades
        '''
        self.loser = None
        self.winner = None

        #Everybody ditches all the pairs they can first
        for p in range(self.n_players):
            self.ditch_pairs(p)

        self.check_done() #Check if game is over

        #licycle = itertools.cycle(range(self.n_players)) #Start cycling through players
        licycle = itertools.cycle(self.p_order.keys())
        p_turn = next(licycle)

        n_turns = 0

        
        while not self.done:
            self.readjust_order()
            if p_turn in self.p_order:
                
                pick_card = random.choice(self.c.hands[self.p_order[p_turn]]) #Pick random card from player
                self.c.hands[p_turn].append(pick_card) #Add that card to player's hand
                self.c.hands[self.p_order[p_turn]].remove(pick_card) #Remove card from other player's hand

                self.ditch_pairs(p_turn)
                self.check_done()

                n_turns += 1
                
                if verbose:
                    print('Turn: {}'.format(n_turns))
                    for p in range(self.n_players):
                        print('Player {}:'.format(p))
                        print(self.c.hands[p])

            p_turn = next(licycle) #Next player's turn
        self.readjust_order()
        return n_turns

def simulate(n_games, n_sims, n_players, verbose=False, seed=False):

    losses_frame = pd.DataFrame(columns=['p'+str(i) for i in range(n_players)])
    wins_frame = pd.DataFrame(columns=['p'+str(i) for i in range(n_players)])
    nturns_array = np.zeros((n_sims, n_games))

    for k in range(n_sims):
        count_losses = {}
        count_wins = {}
        for n in range(n_players):
            count_losses['p'+str(n)] = 0
            count_wins['p'+str(n)] = 0

        for n in range(n_games):
            G = Game(n_players, seed=seed)
            n_turns = G.play(verbose=verbose)
            count_losses['p'+str(G.loser)] += 1
            #If two or more players are out at same time winner is set to first player in ascending order for now...
            count_wins['p'+str(G.winner)] += 1
            nturns_array[k,n] = n_turns

        losses_frame = losses_frame.append(count_losses, ignore_index=True)
        wins_frame = wins_frame.append(count_wins, ignore_index=True)


    return losses_frame, wins_frame, nturns_array


'''
To do:
- Who starts with queen of spades
    - Does this give a lower/higher chance of losing/winning?
- Who discards most pairs in first turn --> probability of winning/losing
'''

l_frame, w_frame, n_frame = simulate(n_games = 1000, n_sims = 10, n_players = 4)

print(l_frame)
print(w_frame)
print(n_frame)
            
plt.boxplot(l_frame.T)
plt.show()

plt.boxplot(w_frame.T)
plt.show()

print(np.mean(n_frame, axis=1))
        
plt.boxplot(n_frame.T)
plt.show()

l_frame_seed, w_frame_seed, n_frame_seed = simulate(n_games = 1000, n_sims = 10, n_players = 4, verbose=False, seed=True)

print(l_frame_seed)
print(w_frame_seed)
print(n_frame_seed)
            
plt.boxplot(l_frame_seed.T)
plt.show()

plt.boxplot(w_frame_seed.T)
plt.show()

print(np.mean(n_frame_seed, axis=1))
        
plt.boxplot(n_frame_seed.T)
plt.show()