from time import time
from utility.printable import Printable
class Block(Printable):
    def __init__(self,index,previous_hash,transactions,proof,timestamp=None):
        self.index=index
        self.previous_hash=previous_hash
        self.timestamp=time() if timestamp is None else timestamp
        self.transactions=transactions
        self.proof=proof
    #  this allows us to define what should be output if we are printing this block
    #  ----we inherit this from Printable now--------
    # def __repr__(self):
    #     return 'Index:{}, Previous Hash: {}, Proof:{},Transactions: {}'.format(self.index,self.previous_hash,self.proof,self.transactions)


