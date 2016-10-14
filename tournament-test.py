from ethereum import tester, utils
from tournament import Tournament

weakcoin_code = open('amiller-weakcoin.se').read()

tester.gas_limit = 1000000

s = tester.state()

numplayers = 3
players = tester.keys[:numplayers]

t = Tournament(players, weakcoin_code, s)
t.play()
