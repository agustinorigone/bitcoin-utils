import sys
from bitcoinutils.setup import setup
from bitcoinutils.keys import P2shAddress, PublicKey
from bitcoinutils.script import Script

def main():
    # always remember to setup the network
    setup('testnet')

    #
    # This script creates a P2SH address containing a CHECKLOCKTIMEVERIFY plus
    # a P2PKH locking funds with a key as well as for a specific block height
    #

    # block height, funds will be locked until the specified block height is reached
    block_height = int(sys.argv[1])

    # get the PublicKey object from the raw public key
    pub = PublicKey(sys.argv[2])

    # get the address (from the public key)
    p2pkh_addr = pub.get_address()
    
    # create the redeem script
    redeem_script = Script([block_height, 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(), 'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    # create a P2SH address from a redeem script
    addr = P2shAddress.from_script(redeem_script)
    print(addr.to_string())

if __name__ == "__main__":
    main()
