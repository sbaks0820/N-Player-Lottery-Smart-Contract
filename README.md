# N-Player-Lottery-Smart-Contract
Smart Contract to handle single coin flip, with python code that sets up tournament and executed it.

Files:
* `amiller-weakcoin.se` - Smart contract written in Serpent that handles a single, biased coin flip with two players.
* `tournament.py` - Python code that takes in a list of players (private keys of players) and executes an N-way coin flip game, a.k.a an N-way lottery.
* `tournament-test.py` - This is the executable. Inside, specify the number of players you want to play with. Currently takes keys from the `pyethereum.tester` which only provides a maximum of 10 keys. However, an arbitraty number of keys can be generated and used.

To run the tournament, change the number of players in `tournament-test.py` and run it.

### TODO: 
- [ ] Have tournament create contracts on actual blockchain instead of pyethereum tester.
- [ ] Force players to interact with contracts instead of simulating it.
- [ ] Will make the trivial change of taking in the number of players as an input soon. 
- [ ] There are likely many ways to make the code shorter, but that's left for another day.
