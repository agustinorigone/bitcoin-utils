import sys
from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey
from bitcoinutils.script import Script
from bitcoinutils.proxy import NodeProxy

def main():
    # always remember to setup the network
    setup('testnet')

    #
    # This script spends from a P2SH address containing a CLTV+P2PKH script
    #
    
    # get the block height from the second argument
    block_height = int(sys.argv[1])

    # get the private key from the third argument
    priv_key = sys.argv[2]

    # get the P2SH address from the forth argument (it will be used for double checking)
    validation_addr = sys.argv[3]

    # secret key needed to spend P2PKH that is wrapped by P2SH
    p2pkh_sk = PrivateKey(priv_key)
    p2pkh_pk = p2pkh_sk.get_public_key().to_hex()
    p2pkh_addr = p2pkh_sk.get_public_key().get_address()
    
    # create the redeem script - needed to sign the transaction
    redeem_script = Script([block_height, 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(), 'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    # create a P2SH address from a redeem script
    addr = P2shAddress.from_script(redeem_script)

    if(addr.to_string() != validation_addr):
        print("Validation address mismatch")
 

    # get a node proxy using default host and port
    proxy = NodeProxy('agustin', 'agustin123').get_proxy()

    # call the node's listtransactions JSON-RPC method
    transactions = proxy.importaddress(addr.to_string())
    print(transactions)


if __name__ == "__main__":
    main()
