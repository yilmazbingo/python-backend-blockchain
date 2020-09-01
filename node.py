from flask import Flask,jsonify,request,send_from_directory
from flask_cors import CORS
from wallet import Wallet
from blockchain import Blockchain
app=Flask(__name__)


#  now this app is open to other clients too
CORS(app)

@app.route('/',methods=['GET'])
def get_ui():
    return send_from_directory("ui","node.html")


@app.route('/network',methods=['GET'])
def get_network_ui():
    return send_from_directory("ui","network.html")

@app.route('/wallet',methods=['POST'])
def create_keys():
    #  we generate keys, save them and instantiate a blockchain
    wallet.create_keys()
    if wallet.save_keys():
        global blockchain
        blockchain=Blockchain(wallet.public_key,port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            "funds":blockchain.get_balance()
        }
        return jsonify(response),201
    else:
        response={
            'message':"saving the wallet keys failed"
        }
        return jsonify(response),500


@app.route('/wallet',methods=['GET'])
def load_keys():
    # this is why we are returning true in load_keys()
    # first we have to send the POST request so keys are generated and saved
    if wallet.load_keys():
        global blockchain
        blockchain = Blockchain(wallet.public_key,port)
        response = {
            'public_key': wallet.public_key,
            'private_key': wallet.private_key,
            "funds": blockchain.get_balance()
        }
        return jsonify(response), 201
    else:
        response = {
            'message': "Loading the wallet keys failed"
        }
        return jsonify(response), 500





# we do not broadcast our transactions here because that transaction is already signed by receiver node
# we broadcast to "/broadcast-transaction"
@app.route("/transaction",methods=['POST'])
def add_transaction():
    if not wallet.public_key:
        response={
            "message":"no wallet is set up"
        }
        return jsonify(response),400
    values=request.get_json()
    if not values:
        response={
            "message":"No data found"
        }
        return jsonify(response),400
    required_fields=['recipient','amount']
    #  checking if all the fields in required fields in incoming VALUES
    if not all(field in values for field in required_fields):
        response={
            "message":"required data is missing"
        }
        return jsonify(response),400
    recipient=values['recipient']
    amount=values['amount']
    signature=wallet.sign_transaction(wallet.public_key,recipient,amount)
    success=blockchain.add_transaction(recipient,wallet.public_key,signature,amount)
    if success:
        response={
            "message":"Transactions is created sccessfully",
            "transaction":{
                "sender":wallet.public_key,
                "recipient":recipient,
                "amount":amount,
                "signature":signature
            },
            "funds":blockchain.get_balance()
        }
        return jsonify(response),201
    else:
        response={
            "message":"Creating transaction failed"
        }
        return jsonify(response),500


@app.route('/broadcast-transaction', methods=['POST'])
def broadcast_transaction():
    values=request.get_json()
    if not values:
        response={
            "message":"no data found"
        }
        return jsonify(response),400
    required_data=['sender',"recipient","amount","signature"]
    if not all(key in values for key in required_data):
        response={
            "message":"missing data!"
        }
        return jsonify(response),400
    success=blockchain.add_transaction(values['recipient'],
                                       values['sender'],
                                       values['signature'],
                                       values['amount'],
                                       is_receiving=True)
    # is_receiving=True means we did not create this tx, it got broadcasted by the creator
    # that way we are not gonna broadcast this tx to other peer nodes
    # if you check add_transaction() it broadcasts the tx if it is the one who created it.
    if success:
        response={
            "message":"Successfully added transaction",
            'transaction':{
                'sender':values['sender'],
                'recipient':values['recipient'],
                'signature':values['signature'],
                'amount':values['amount']

            }
        }
        return jsonify(response),201
    else:
        response={
            'message':"creating a transaction failed"
        }
        return jsonify(response),500

@app.route("/broadcast-block", methods=['POST'])
def broadcast_block():
    values=request.get_json()
    if not values:
        response={
            "message":"No data found"
        }
        return jsonify(response),400
    if "block" not in valus:
        response={
            "message":"Some data is missing"
        }
        return jsonify(response),400
    block=values['block']
    # checking if incoming block's index equals to current node's last block's index+1
    if block['index']==blockchain.chain[-1].index+1:
        if blockchain.add_block(block):
            response={
                "message":"Block added"
            }
            return jsonify(response), 201
        else:
            response={
                "message":"Block seems is invalid"
            }
            return jsonify(response),409
    # we apply CONSENSUS here
    elif block['index']>blockchain.chain[-1].index:
        response={
            "message":"Blockchain seems to differ from local blockchain"
        }
        blockchain.resolve_conflicts=True
        return jsonify(response),200

    else:
        response={
            "message":"Blockchain seems to be shorter, block not addeed"
        }
        # 409 signals data is sent is invalid
        return jsonify(response),409
@app.route("/balance",methods=["GET"])
def get_balance():
    balance=blockchain.get_balance()
    if balance != None:
        response={
            "message":"fetched balance successfully",
            "funds":balance
        }
        return jsonify(response),200
    else:
        response={"message":"loading baalance failed",
                  "wallet_set_up":wallet.public_key!=None}
        return jsonify(response),500

@app.route("/resolve-conflicts",methods=['POST'])
def resolve_conflicts():
    # it returns true or false
    replaced=blockchain.resolve()
    if replaced:
        response={
            "message":"Chain was replaced"
        }
    else:
        response={
            "message":"local chain kept"
        }
    return jsonify(response),200



@app.route("/mine",methods=['POST'])
def mine():
    # this signals that our local chain is not in sync
    if blockchain.resolve_conflicts:
        response={
            "message":"Resolve conflicts first, block not added"
        }
        return jsonify(response),409
    block=blockchain.mine_block()
    #  we send the mined block but first we need to convert it to dict to be able to jsonify
    if block:
        # we use copy() to manipulate the transactions
        dict_block = block.__dict__.copy()
        # since "block" is dict now, we cannot use the dot notation
        dict_block['transactions'] = [tx.__dict__ for tx in dict_block['transactions']]
        # we pass the public key into blockchain in /wallet. so we need to call that first
        response={
            'message':"Block added succesfully",
            'block':dict_block,
            "funds":blockchain.get_balance()
        }
        return jsonify(response),200
    else:
        response={'message':"adding a block failed",
                  'wallet_set_up':wallet.public_key!=None}
        return jsonify(response),500


@app.route('/chain',methods=['GET'])
def get_chain():
    chain_snapshot=blockchain.get_chain()
    # we have to convert chain_snapshot dict first for jsonify package
    dict_chain_snapshot=[block.__dict__.copy() for block in chain_snapshot]
    # transactions inside blocks have to be converted too
    for dict_block in dict_chain_snapshot:
        # no dot notation here because we converted the blocks to dict
        dict_block['transactions']=[tx.__dict__ for tx in dict_block['transactions']]
    return jsonify(dict_chain_snapshot),200



@app.route('/transactions',methods=['GET'])
def get_open_transactions():
    transactions=blockchain.get_open_transactions()
    dict_transactions=[tx.__dict__ for tx in transactions]

    return jsonify(dict_transactions),200


@app.route('/node',methods=['POST'])
def add_node():
    #  values is a dict
    values=request.get_json()
    if not values:
        response={
            'message':'no data attached'
        }
        return jsonify(response),400
    if 'node' not in values:
        response={
            "message":"no node data found"
        }
        return jsonify(response),400
    #  same as values['node']
    node=values.get('node')
    #  we do not need wallet here
    blockchain.add_peer_node(node)
    response={
        'message':'Node added successfully',
        # get_peer_nodes returns list
        'all nodes':blockchain.get_peer_nodes()
    }
    return jsonify(response),201


@app.route("/node/<node_url>",methods=['DELETE'])
def remove_node(node_url):
    if node_url=="" or node_url==None:
        response={
            "message":"no node found"
        }
        return jsonify(response),400

    blockchain.remove_peer_node(node_url)
    response={
        "message":"Node removed",
        "current nodes":blockchain.get_peer_nodes()
    }
    return jsonify(response),200


@app.route("/nodes",methods=["GET"])
def get_nodes():
    nodes=blockchain.get_peer_nodes()
    response={
        "all nodes":nodes
    }
    return jsonify(response),200

if __name__=='__main__':
    # this helps us add command line arguments
    from argparse import ArgumentParser
    parser=ArgumentParser()
    # it accepts only one argument
    parser.add_argument("-p", '--port',type=int, default=5000)
    args=parser.parse_args()
    print(args)
    port=args.port
    #  all functions above will be executed after this part
    #  when we initialize an instance, private and public keys are None
    #  we are passing port here because we want each peer has their own txt files
    wallet = Wallet(port)
    blockchain = Blockchain(wallet.public_key,port)
    app.run(host='0.0.0.0',port=port)


