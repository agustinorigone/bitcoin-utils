import sys
from bitcoinutils.setup import setup
from bitcoinutils.utils import to_satoshis
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, Sequence, Locktime
from bitcoinutils.keys import P2pkhAddress, P2shAddress, PrivateKey
from bitcoinutils.script import Script
from bitcoinutils.proxy import NodeProxy 
from bitcoinutils.constants import TYPE_ABSOLUTE_TIMELOCK

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

    # get the P2PKH address to send the funds to from the fifth
    to_addr = P2pkhAddress(sys.argv[4])

    seq = Sequence(TYPE_ABSOLUTE_TIMELOCK, block_height)
    locktime = Locktime(block_height)

    # secret key needed to spend P2PKH that is wrapped by P2SH
    p2pkh_sk = PrivateKey(priv_key)
    p2pkh_pk = p2pkh_sk.get_public_key().to_hex()
    p2pkh_addr = p2pkh_sk.get_public_key().get_address()
    
    # create the redeem script - needed to sign the transaction
    redeem_script = Script([seq.for_script(), 'OP_CHECKLOCKTIMEVERIFY', 'OP_DROP', 'OP_DUP', 'OP_HASH160', p2pkh_addr.to_hash160(), 'OP_EQUALVERIFY', 'OP_CHECKSIG'])

    # create a P2SH address from a redeem script
    addr = P2shAddress.from_script(redeem_script)

    if(addr.to_string() != validation_addr):
        print("Validation address mismatch")
 

    # get a node proxy using default host and port
    proxy = NodeProxy('rpc_user', 'rpc_pass').get_proxy()

    # import the address as watch-only to the wallet
    proxy.importaddress(addr.to_string(),"p2sh wallet", False)

    # get the UTXOs list
    trxs = proxy.listunspent()

    total_amount = 0
    txinputs = []
    
    for trx in trxs:
        # check if the transaction belongs to the imported address (imported in line 48)
        if(addr.to_string() == trx['address']):
            txid = trx['txid']
            vout = trx['vout']
            total_amount += float(trx['amount'])

            # create transaction input from tx id of UTXO
            txin = TxInput(txid, vout, sequence=seq.for_input_sequence())

            # append transaction input to array
            txinputs.append(txin)
    #end for loop
    
    # create a transaction output with the total amount 
    # only for calculating the fees
    txout_just_for_calc_fees = TxOutput(to_satoshis(total_amount), to_addr.to_script_pub_key())
            
    # create transaction from inputs/outputs
    # only for calculating fees
    tx_just_for_calc_fees = Transaction(txinputs, [txout_just_for_calc_fees], locktime.for_transaction())

    # get the size of the transaction in bytes
    tx_size_bytes = len(tx_just_for_calc_fees.serialize())
    
    # get the size of the transaction in KB
    tx_size_kbytes = tx_size_bytes / 1024
    
    # get the fee in btc per kilo bytes (to be included in the next block)
    fees_data = proxy.estimatesmartfee(1)
    fee_in_btc_per_kbytes = fees_data['feerate']

    tx_fee_in_btc = tx_size_kbytes * float(fee_in_btc_per_kbytes)

    # create a transaction output with the total amount minus the fee
    txout = TxOutput(to_satoshis(total_amount - tx_fee_in_btc), to_addr.to_script_pub_key())

    tx = Transaction(txinputs, [txout], locktime.for_transaction())

    # print raw transaction
    print("\nRaw unsigned transaction:\n" + tx.serialize())
    
    # transaction index for signature
    i = 0

    # set the scriptSig (unlocking script) -- unlock the P2PKH (sig, pk) plus
    # the redeem script, since it is a P2SH
    for txin in txinputs:
        # create th signature for the txin, using the private key
        sig = p2pkh_sk.sign_input(tx, i, redeem_script)
        txin.script_sig = Script([sig, p2pkh_pk, redeem_script.to_hex()])
        i += 1
    
    signed_tx = tx.serialize()

    # print raw signed transaction ready to be broadcasted
    print("\nRaw signed transaction:\n" + signed_tx)
    print("\nTxId:", tx.get_txid())

    # check if the transaction is valid
    valid = proxy.testmempoolaccept([signed_tx])

    # broadcast the transaction to the network
    if(valid):
        proxy.sendrawtransaction(signed_tx)
    

if __name__ == "__main__":
    main()
