from utility.hash_util import hash_string_256,hash_block
from wallet import Wallet

class Verification:
    # The class method takes the class as parameter to know about the state of that class.
    # Class method can access and modify the class state.
    @classmethod
    def verify_chain(cls, blockchain):
        for (index, block) in enumerate(blockchain):
            #  becuase first block is genesis block
            if index == 0:
                continue
            if block.previous_hash != hash_block(blockchain[index - 1]):
                return False
            # we are excluding the reward transactions because they are not part of the proof
            if not cls.valid_proof(block.transactions[:-1], block.previous_hash, block.proof):
                print("proof of work is invalid")
                return False
        return True

    #  it is not using any class attr or methods
    @staticmethod
    def valid_proof(transactions, last_hash, proof):
        # Create a string with all the hash inputs
        # If no encoding is specified, UTF-8 will be used.
        guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
        guess_hash = hash_string_256(guess)
        return guess_hash[0:2] == "00"

    # Static methods do not know about class state.
    # These methods are used to do some utility tasks by taking some parameters.
    @staticmethod
    def verify_transaction(transaction, get_balance, check_funds=True):
        if check_funds:
            sender_balance = get_balance(transaction.sender)
            return sender_balance >= transaction.amount and Wallet.verify_transaction(transaction)
        else:
            return Wallet.verify_transaction(transaction)

    @classmethod
    def verify_transactions(cls, open_transactions, get_balance):
        return all([cls.verify_transaction(tx, get_balance,False) for tx in open_transactions])


