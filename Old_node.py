from blockchain import Blockchain
from utility.verification import Verification
from wallet import Wallet

class Node:
    #  every Node should havve its local copy of blockchain
    def __init__(self):
        #  in order to write this to the file it has to be string.
        # self.id=str(uuid4())
        self.wallet=Wallet()
        self.wallet.create_keys()
        self.blockchain = Blockchain(self.wallet.public_key)

    def get_transaction_value(self):
        tx_recipient = input("Enter the recipient of the transaction")
        tx_amount = float(input("your transaction amount please"))
        # Notice that we didn’t use parentheses in the return statement.
        # That’s because you can return a tuple by separating each item with a comma, as shown in the above example.
        # “It is actually the comma which makes a tuple, not the parentheses,” the documentation points out.
        # However, parentheses are required with empty tuples or to avoid confusion.
        return tx_recipient, tx_amount

    def get_user_choice(self):
        user_input = input("your choice")
        return user_input

    def print_blockchain_elements(self):
        for block in self.blockchain.get_chain():
            print("outputting block")
            print(block)
        else:
            print('-' * 20)

    def listen_for_input(self):
        waiting_for_input = True
        while waiting_for_input:
            print("Please choose")
            print('1:Add a new transaction value')
            print('2: Mine a new block')
            print("3: output the blockchain blocks")
            print("4: check transaction validity")
            print("5: Create wallet")
            print('6: load wallet')
            print('7: Save keys')
            print("q : Quit ")
            user_choice = self.get_user_choice()
            if user_choice == '1':
                # this holds a tuple and we unpack
                tx_data = self.get_transaction_value()
                recipient, amount = tx_data
                signature=self.wallet.sign_transaction(self.wallet.public_key,recipient,amount)
                #  we skipped the sender. that's why amount=amount
                if self.blockchain.add_transaction(recipient, self.wallet.public_key,signature, amount=amount):
                    print("Added Transaction!")
                else:
                    print('Transaction failed')
                print(self.blockchain.get_open_transactions())
            elif user_choice == "2":
                if not self.blockchain.mine_block():
                    print('Mining failed. Got no wallet')

            elif user_choice == "3":
                self.print_blockchain_elements()

            elif user_choice == "4":

                if Verification.verify_transactions(self.blockchain.get_open_transactions, self.blockchain.get_balance):
                    print("all transactions are valid")
                else:
                    print('there are invalid transactions')

            elif user_choice=="5":
                self.wallet.create_keys()
                self.blockchain =Blockchain(self.wallet.public_key)

            elif user_choice=="6":
                self.wallet.load_keys()
                self.blockchain=Blockchain(self.wallet.public_key)

            elif user_choice == "7":
                self.wallet.save_keys()


            elif user_choice == "q":
                waiting_for_input = False
            else:
                print("input was invalid, please take avlue from the list")

            if not Verification.verify_chain(self.blockchain.get_chain()):
                self.print_blockchain_elements()
                print("invalid blockchain")
                break
            print('Balance of {}:{:6.2f}'.format(self.wallet.public_key, self.blockchain.get_balance()))
            print(self.blockchain)
        else:
            print("user left")

        print("Done!")

if __name__=='__main__':
    node=Node()
    node.listen_for_input()