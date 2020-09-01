from collections import OrderedDict
class Transaction():
    def __init__(self,sender,recipient,signature,amount):
        self.sender=sender
        self.recipient=recipient
        self.amount=amount
        self.signature=signature

    # we need order the transactions in order to get the same hash value everytime.
    def to_ordered_dict(self):
        return OrderedDict([('sender',self.sender),('recipient',self.recipient),('amount',self.amount)])


    #  repr returns only strings
    def __repr__(self):
        return str(self.__dict__)


