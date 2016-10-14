from ethereum import tester,utils
import bitcoin
import os
import random
from math import log
import copy

class Tournament():
    # Helper functions
    oneether = 10E21
    tobytearr = lambda self, n, L: [] if L == 0 else self.tobytearr(n / 256, L - 1)+[n % 256]
    zfill = lambda self, s: (32-len(s))*'\x00' + s

    active_players = []
    # Tree is list of levels of coins
    tree = []   
    d = {}
   
    def __init__(self, players, coin, s):
        self.N = len(players)
        self.active_players = copy.copy(players)
        self.s = s
        self.keys = players
        # list of pub keys for players
        self.addresses = [utils.privtoaddr(x) for x in self.keys]   
        # list of pub keys in hex
        self.hexkeys = [long(x.encode('hex'),16) for x in self.addresses]
        # mapping from hex pub key to priv key
        self.hextok = dict(zip(self.hexkeys,self.keys))
        # mapping from raw pub key to priv key
        self.p2p = dict(zip(self.keys, self.addresses))
        # code for coin representing individual coin flip
        self.coin = coin
        # create the game
        self.setup()

    # setup the game with correct tree stucture and biases
    def setup(self):
        # create game tree
        original, roots = self.create(self.N)
        self.createlayers(roots[0])

        # setup leaves to only have one player
        i = len(self.tree)-1
        for j in range(len(self.tree[i])):
            self.tree[i][j].initialize(self.p2p[self.active_players[j]],self.p2p[self.active_players[j]],0,0,-1,-1,-1,1,1)

        time = 0
        for i in range(len(self.tree)-2, -1, -1):
            for j in range(len(self.tree[i])):
                dn = self.d[self.tree[i][j]]
                child1 = self.d[dn[0]]
                if dn[0] and dn[1]:
                #    child1 = self.d[dn[0]]
                    child2 = self.d[dn[1]]
                    self.tree[i][j].initialize(0,0, self.tree[i+1][2*j].address, self.tree[i+1][2*j+1].address,20*time, 20*time+10, 20*time+20,child1[2],child1[2]+child2[2])
                elif dn[0]:
                 #   child1 = self.d[dn[0]]
                    self.tree[i][j].initialize(0,0, self.tree[i+1][2*j].address, self.tree[i+1][2*j].address, 20*time, 20*time+10, 20*time+20, child1[2],child1[2])    
        
        print '\nCurrent Players'
        for i in range(self.N):
            print long(self.p2p[self.active_players[i]].encode('hex'),16)

    # Execute the tournament until there is a winner
    def play(self):
        # track players' commits and randomness
        secrets = {}
        commits = {}

        # Start at the level abve the leaves
        for i in range(len(self.tree)-2,-1,-1):
            print '\nNEW ROUND'
            print '\nCommitting....'
            for j in range(len(self.tree[i])):
                dn = self.d[self.tree[i][j]]
                # Commit for first player
                secrets[self.active_players[2*j]] = os.urandom(32)
                commits[self.active_players[2*j]] = utils.sha3(self.zfill(self.p2p[self.active_players[2*j]])+secrets[self.active_players[2*j]]) 
                self.tree[i][j].commit(commits[self.active_players[2*j]], sender=self.active_players[2*j])
                # Commit for second player if exists
                if dn[0] and dn[1]:
                    secrets[self.active_players[2*j+1]] = os.urandom(32)
                    commits[self.active_players[2*j+1]] = utils.sha3(self.zfill(self.p2p[self.active_players[2*j+1]])+secrets[self.active_players[2*j+1]])
                    
                    self.tree[i][j].commit(commits[self.active_players[2*j+1]], sender=self.active_players[2*j+1])

            # mine for next phase
            self.s.mine(10) 

            print '\nRevealing...'
            for j in range(len(self.tree[i])):
                dn = self.d[self.tree[i][j]]
                # Only reveal for coins with 2 players, in cases with 1, p1 is promoted (bias updates)
                if dn[0] and dn[1]:
                    self.tree[i][j].open(secrets[self.active_players[2*j]], sender=self.active_players[2*j])
                    self.tree[i][j].open(secrets[self.active_players[2*j+1]], sender=self.active_players[2*j+1])
            
            # mine to end this round
            self.s.mine(10)
            winners = []

            # figure out the winners
            for j in range(len(self.tree[i])):
                winner = self.tree[i][j].getWinner()
                winners.append(self.hextok[winner])
        
            # update active players
            self.active_players = winners
            print '\nCurrent Players:'
            for j in range(len(self.active_players)):
                print long(self.p2p[self.active_players[j]].encode('hex'),16)
                    
    # Convert binary tree structure to list of lists representing nodes on each level
    def createlayers(self, root):
        level = [root]
        while level:
            nextlevel = list()
            for n in level:
                dn = self.d[n]
                if dn[0]: nextlevel.append(dn[0])
                if dn[1]: nextlevel.append(dn[1])
            self.tree.append(level)
            level = nextlevel

    # create a complete binary tree with depth N
    def createtree(self,N):
        d = self.d
        if N == 0:
            c = self.s.abi_contract(self.coin)
            d[c] = (None, None, 1, 0)
            return c
    
        c = self.s.abi_contract(self.coin)
        t1 = self.createtree(N-1)
        t2 = self.createtree(N-1)
    
        # d[c] = (child1, child2, # leaves, height)
        d[c] = (t1, t2, d[t1][2]+d[t2][2], max(d[t1][3],d[t2][3])+1)
        return c

    # split N into complete binary trees and merge them together
    # all leaves are on the same level and each path from the root to a leaf
    #       traverses log(N) nodes
    # Analogous to creating a complete binary tree and removing subtrees   
    #       until num_leaves = N
    def create(self,N):
        d = self.d
        roots = []
        z = 0
        # create maximum power of 2 trees
        while z < N:
            po2 = int(log(N-z,2))
            r = self.createtree(po2)
            roots.append(r)
            z += 2**po2

        originalroots = copy.copy(roots)
        # only attempts to merge if there is more than one tree
        if len(roots) > 1:
            # merge smallest treest first
            for i in range(len(roots)-1, 0, -1):
                # difference in tree heights
                diff = d[roots[i-1]][3] - d[roots[i]][3]
                # choose which root to extend
                if diff > 0:
                    node = i
                else:
                    node = i
                # add nodes to root of smaller tree until 2 trees have same height
                # adds vertial line of nodes
                last = roots[node]
                h = d[last][3]
                for j in range(int(diff)):
                    c = self.s.abi_contract(self.coin)
                    # attach new node to root
                    d[c] = (last,None,d[last][2],h+1)
                    last = c
                    h += 1
                roots[node] = last
                c = self.s.abi_contract(self.coin)
                # merge two subtrees with a new root
                d[c] = (roots[i-1], roots[i], d[roots[i]][2]+d[roots[i-1]][2], max(d[roots[i]][3],d[roots[i-1]][3])+1)
                roots[i-1] = c
                 
        return (originalroots, roots)

    # print out a tree rooted at r
    # and add '*' nodes in mark
    def printtree(self,r,mark):
        d = self.d
        q = []
        q.append(r)
        level = 0
        last = d[r][3]
        while len(q) != 0:
            c = q.pop()
            if d[c][3] < last:
                print '\n'
                last = d[c][3]
            if c in mark:
                print str(c)+'*',
            else:
                print c,
            if d[c][0] is not None:
                q.insert(0, d[c][0])
            if d[c][1] is not None:
                q.insert(0, d[c][1])
