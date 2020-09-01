
from functools import reduce
import json
import requests
from block import Block
from transaction import Transaction
from wallet import Wallet
from utility.hash_util import hash_block
from utility.verification import Verification

MINING_REWARD=10

class Blockchain:
    def __init__(self, public_key, node_id):
        #  timestamp should not be current one for genesis block
        genesis_block = Block(0, "anything", [], 100, 0)
        self.__chain=[genesis_block]
        #  this is called transactions_pool
        self.__open_transactions=[]
        #  we should initialized set first and then load(). otherwise set will be loaded empty
        self.__peer_nodes=set()
        self.node_id= node_id
        #  whenever we create the blockchain, it will load from
        self.load_data()
        # we use this for "/broadcast-block"
        self.resolve_conflicts=False
        self.public_key=public_key

        #  peer nodes that we communicate


    def add_peer_node(self,node):
        # node is the url address of other peer
        self.__peer_nodes.add(node)
        self.save_data()


    def remove_peer_node(self,node):
        #  if node does not exist in the set, it wont throw error
        self.__peer_nodes.discard(node)
        self.save_data()


    def get_peer_nodes(self):
        # since sets are unordered, we cannnot use range to create a new obj
        # return self.__peer_nodes[:]
        return list(self.__peer_nodes)
        #  since list() already creates a new list, we do not need [:]

    def get_chain(self):
        # since sets are unordered, we cannnot use range to create a new obj
        # return self.__chain[:]
        #  since list() already creates a new list, we do not need [:]
        return list(self.__chain)

    def get_open_transactions(self):
        return self.__open_transactions[:]


    def load_data(self):
        try:
            with open('blockchain-{}.txt'.format(self.node_id), mode="r") as f:
                # this returns the array of the lines
                file_content = f.readlines()
                #  first line is our blockchain data,second is open transactions as String
                #  we have to deserialize the string
                #  [:-1] we do not want "\n"
                blockchain = json.loads(file_content[0][:-1])
                updated_blockchain = []
                # since we save transactions as OrderedDict, OrderedDict key word is also part of the transaction
                # but when we write with json. we lose 'OrderedDict'. now we add back
                for block in blockchain:
                    # since this block is loaded from the file, it is a dictinory
                    converted_tx = [Transaction(tx['sender'], tx['recipient'],tx['signature'], tx['amount']) for tx in
                                    block['transactions']]
                    # this is not a dictionary, it is a Block object
                    updated_block = Block(block['index'], block['previous_hash'], converted_tx, block['proof'],
                                          block['timestamp'])
                    updated_blockchain.append(updated_block)
                self.__chain = updated_blockchain
                open_transactions = json.loads(file_content[1])[:-1]
                updated_transactions = []
                for tx in open_transactions:
                    updated_transaction = Transaction(tx['sender'], tx['recipient'],tx['signature'], tx['amount'])
                    updated_transactions.append(updated_transaction)
                self.__open_transactions = updated_transactions
                peer_nodes=json.loads(file_content[2])
                self.__peer_nodes=set(peer_nodes)
        #  just handle the specific errors
        except (IOError, IndexError):
           print('handled exception...')
        #  this will always run. great for cleaning up
        finally:
            print("cleanUp!")

    def save_data(self):
        try:
            with open('blockchain.txt-{}'.format(self.node_id), mode="w") as f:
                # blockchain blocks are class objects now and json does not stringify those
                # we do not need to call .copy() because we are not manipulating the dict
                saveable_chain = [block.__dict__ for block in [
                    Block(block_el.index, block_el.previous_hash, [tx.__dict__ for tx in block_el.transactions],
                          block_el.proof, block_el.timestamp) for block_el in self.__chain]]
                f.write(json.dumps(saveable_chain))
                f.write('\n')
                saveable_tx = [tx.__dict__ for tx in self.__open_transactions]
                f.write(json.dumps(saveable_tx))
                f.write('\n')
                f.write(json.dumps(list(self.__peer_nodes)))
        except IOError:
            print('saving failed')

    def proof_of_work(self):
        last_block = self.__chain[-1]
        last_hash = hash_block(last_block)
        proof = 0
        while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
            proof += 1
        return proof

    def get_last_blockchain_value(self):
        if len(self.__chain) < 1:
            return None
        return self.__chain[-1]

    # we are checking the balance of the sender
    def get_balance(self,sender=None):
        if sender==None:
            if self.public_key==None:
                return None
            participiant=self.public_key
        else:
            participiant=sender
        # nested list comprohension. since block is an obj, we use dot notation
        tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participiant] for block in self.__chain]
        open_tx_sender = [tx.amount for tx in self.__open_transactions if tx.sender == participiant]
        tx_sender.append(open_tx_sender)
        # we are reducing the tx_sender list
        amount_sent = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0, tx_sender,
                             0)
        print("amount sent{}".format(tx_sender))
        tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participiant] for block in
                        self.__chain]
        amount_received = reduce(lambda tx_sum, tx_amt: tx_sum + sum(tx_amt) if len(tx_amt) > 0 else tx_sum + 0,
                                 tx_recipient, 0)
        return amount_received - amount_sent

    # optional args comes after
    def add_transaction(self, recipient, sender,signature, amount=1.0, is_receiving=False):
        # transaction={'sender':sender,"recipient":recipient,"amount":amount}
        # we have to make sure that order of transaction dict is always same.
        # if self.public_key==None:
        #     return False
        transaction = Transaction(sender, recipient, signature, amount)
        if Verification.verify_transaction(transaction, self.get_balance):
            self.__open_transactions.append(transaction)
            self.save_data()
            #  after we save the data we have to inform peer nodes about transaction
            if not is_receiving:
                # is_receiving checks if the node is receiving the tx or creating the tx
                # if we do not add this check, each peer would broadcast the tx to each other
                # this would make it very long request.
                # if not receiving means we created the tx so we are able to broadcast
                for node in self.__peer_nodes:
                    url = 'http://{}/broadcast-transaction'.format(node)
                    try:
                        # flask expects json data
                        response=requests.post(url, json={'sender': sender,
                                                          'recipient': recipient,
                                                          "amount": amount,
                                                          "signature": signature})
                        if response.status_code==400 or response.status_code==500:
                            print('transaction declined, needs resolving')
                            return False
                        if response.status_code==409:
                            self.resolve_conflicts=True
                    except requests.exceptions.ConnectionError:
                        # we continue to other node
                        continue
                return True
        return False

    def mine_block(self):
        if self.public_key==None:
            return None
        last_block = self.__chain[-1]
        # we can join only strings
        hashed_block = hash_block(last_block)
        proof = self.proof_of_work()
        # ----reward transactions are not part of the proof of work because they are added after block is built
        # reward_transaction={
        #     'sender':"MINING",
        #     'recipient':owner,
        #     'amount':MINING_REWARD
        # }
        #  self.public_key the node that did mining
        reward_transaction = Transaction('MINING', self.public_key, '', MINING_REWARD)
        #  we copied open_transactions because if adding block was not successful, our block will be destroyed
        #  So we will not be adding the mining reward to the open_transactions
        #  when we attempt to make a new block, open_transactions will not have mining reward
        copied_transactions = self.__open_transactions[:]
        for tx in copied_transactions:
            if not Wallet.verify_transaction(tx):
                return None
        #  we are not verifying the reward transactions
        copied_transactions.append(reward_transaction)
        block = Block(len(self.__chain), hashed_block, copied_transactions, proof)
        # our transactions are written in the file. now we are preventing transactions manually altered in there
        self.__chain.append(block)
        self.__open_transactions = []
        self.save_data()
        for node in self.__peer_nodes:
            url="http://{}/broadcast-block".format(node)
            # we use copy() cause we want to convert transactions too
            converted_block=block.__dict__.copy()
            converted_block['transactions']=[tx.__dict__ for tx in converted_block['transactions']]
            try:
                response=requests.post(url,json={'block':converted_block})
                if response.status_code==400 or response.status_code==500:
                    print('Block declined, needs resolving')
            except requests.exceptions.ConnectionError:
                continue
        return block

    def add_block(self,block):
        #  received block will be in dict format by Flask
        # transactions includes "reward_transactions" as well
        # but we cannot validate it. thats why we use "transactions[:-1]"
        # normally it should be first transaction of the next block and called COINBASE TRANSACTION
        # it has only one input called COINBASE
        transactions=[Transaction(tx['sender'],tx['recipient'],tx["signature"],tx['amount']) for tx in block['transactions']]
        proof_is_valid=Verification.valid_proof(transactions[:-1], block['previous_hash'], block['proof'])
        # incoming block's previous_hash should be equal to the last block's hash on the peer's chain
        hashes_match=hash_block(self.chain[-1])==block['previous_hash']
        if not proof_is_valid or not hashes_match:
            return False
        converted_block=Block(block['index'],block['previous_hash'],transactions,block['proof'],block['timestamp'])
        self.__chain.append(converted_block)
        stored_transactions=self.__open_transactions[:]
        for itx in block['transactions']:
            # checking if any transaction in the peer's open transactions is in transactions of incoming block
            for opentx in stored_transactions:
                # open_transactions are object
                if opentx.sender==itx['sender'] and opentx.recipient==itx['recipient'] and opentx.amount==itx['amount'] and opentx.signature==itx['signature']:
                    try:
                        # remove() might fail so we use try: except()
                        self.__open_transactions.remove(opentx)
                    except ValueError:
                        print('item was already removed')
        self.save_data()
        return True

    # applies the CONSENSUS
    def resolve(self):
        # we are looping over, so each time we get a new one we assign it here
        winner_chain=self.__chain
        # checking if our current chain has been replaced to clear the open transactions
        replace=False
        for node in self.__peer_nodes:
            url="http://{}/chain".format(node)
            try:
                response=requests.get(url)
                # this is a list
                node_chain=response.json()
                # we are converting block to an object
                # now we are converting transactions to object
                node_chain = [Block(block['index'], block['previous_hash'], [Transaction(
                    tx['sender'], tx['recipient'], tx['signature'], tx['amount']) for tx in block['transactions']],
                                    block['proof'], block['timestamp']) for block in node_chain]
                node_chain_length=len(node_chain)
                local_chain_length=len(winner_chain)
                if node_chain_length>local_chain_length and Verification.verify_chain(node_chain):
                    winner_chain=node_chain
                    replace=True
            except requests.exceptions.ConnectionError:
                continue
        # we resolved the conflicts so it is False now
        self.resolve_conflicts=False
        if replace:
            self.__open_transactions=[]
        self.save_data()
        return replace










































