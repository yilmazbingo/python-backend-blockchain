from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii


#  wallet refers to keys. it is like a keychain
#  users control the coins  by signing transactions with the keys
#  we are implementing deterministic wallet type
#  wallets are completely independent of bitcoin protocol
class Wallet:
    def __init__(self,node_id):
        #  private key is used to sign the transactions
        self.private_key=None
        #  public key is used to receive funds
        self.public_key=None
        self.node_id=node_id

    #  we create new keys here
    def create_keys(self):
        private_key, public_key = self.generate_keys()
        self.private_key=private_key
        self.public_key=public_key

    def generate_keys(self):
        # those keys are in binary format.
        # Crypto.Random is the function that generates the random key.
        private_key=RSA.generate(1024, Crypto.Random.new().read)
        public_key=private_key.publickey()
        # DER is a binary format for data structures described by ASN.
        # from hex we decode it to ascii characters
        return binascii.hexlify(private_key.exportKey(format="DER")).decode('ascii'), binascii.hexlify(public_key.exportKey(format="DER")).decode('ascii')

    def save_keys(self):
        if self.public_key and self.private_key:
            try:
                with open('wallet-{}.txt'.format(self.node_id), mode='w') as f:
                    f.write(self.public_key)
                    f.write('\n')
                    f.write(self.private_key)
                return True

            except(IOError, IndexError):
                print('Saving wallet failed')
                return False

    #  we are returnig True or False for the if condition check in node.py
    def load_keys(self):
        try:
            with open('wallet-{}.txt'.format(self.node_id), mode='r') as f:
                keys=f.readlines()
                public_key=keys[0][:-1]
                private_key=keys[1]
                self.public_key = public_key
                self.private_key = private_key
            return True
        except(IOError,IndexError):
            print("loading wallet failed")
            return False

    def sign_transaction(self,sender,recipient,amount):
        # unhexlify() takes hex data and displays it in tuples of binary.
        signer=PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
        # h=hash since hash is reserved key
        h=SHA256.new((str(sender)+str(recipient)+str(amount)).encode('utf8'))
        signature=signer.sign(h)
        return binascii.hexlify(signature).decode('ascii')

    # this checks if the signature is valid
    @staticmethod
    def verify_transaction(transaction):
        #  converting to binary
        public_key=RSA.importKey(binascii.unhexlify(transaction.sender))
        verifier=PKCS1_v1_5.new(public_key)
        h=SHA256.new((str(transaction.sender)+str(transaction.recipient)+str(transaction.amount)).encode('utf8'))
        return verifier.verify(h, binascii.unhexlify(transaction.signature))


