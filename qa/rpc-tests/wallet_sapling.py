#!/usr/bin/env python2
# Copyright (c) 2018 The Zcash developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    assert_equal,
    start_nodes,
    wait_and_assert_operationid_status,
)

from decimal import Decimal

# Test wallet behaviour with Sapling addresses
class WalletSaplingTest(BitcoinTestFramework):

    def setup_nodes(self):
        return start_nodes(4, self.options.tmpdir, [[
            '-nuparams=5ba81b19:201', # Overwinter
            '-nuparams=76b809bb:201', # Sapling
        ]] * 4)

    def run_test(self):
        # Sanity-check the test harness
        assert_equal(self.nodes[0].getblockcount(), 200)

        # Activate Sapling
        self.nodes[2].generate(1)
        self.sync_all()

        taddr0 = self.nodes[0].getnewaddress()
        # Skip over the address containing node 1's coinbase
        self.nodes[1].getnewaddress()
        taddr1 = self.nodes[1].getnewaddress()
        saplingAddr0 = self.nodes[0].z_getnewaddress('sapling')
        saplingAddr1 = self.nodes[1].z_getnewaddress('sapling')

        # Verify addresses
        assert(saplingAddr0 in self.nodes[0].z_listaddresses())
        assert(saplingAddr1 in self.nodes[1].z_listaddresses())
        assert_equal(self.nodes[0].z_validateaddress(saplingAddr0)['type'], 'sapling')
        assert_equal(self.nodes[0].z_validateaddress(saplingAddr1)['type'], 'sapling')

        # Verify balance
        assert_equal(self.nodes[0].z_getbalance(saplingAddr0), Decimal('0'))
        assert_equal(self.nodes[1].z_getbalance(saplingAddr1), Decimal('0'))
        assert_equal(self.nodes[1].z_getbalance(taddr1), Decimal('0'))

        # Node 0 shields some funds
        # taddr -> Sapling
        #       -> taddr (change)
        recipients = []
        recipients.append({"address": saplingAddr0, "amount": Decimal('20')})
        myopid = self.nodes[0].z_sendmany(taddr0, recipients, 1, 0)
        wait_and_assert_operationid_status(self.nodes[0], myopid)

        self.sync_all()
        self.nodes[2].generate(1)
        self.sync_all()

        # Verify balance
        assert_equal(self.nodes[0].z_getbalance(saplingAddr0), Decimal('20'))
        assert_equal(self.nodes[1].z_getbalance(saplingAddr1), Decimal('0'))
        assert_equal(self.nodes[1].z_getbalance(taddr1), Decimal('0'))

        # Node 0 sends some shielded funds to node 1
        # Sapling -> Sapling
        #         -> Sapling (change)
        recipients = []
        recipients.append({"address": saplingAddr1, "amount": Decimal('15')})
        myopid = self.nodes[0].z_sendmany(saplingAddr0, recipients, 1, 0)
        wait_and_assert_operationid_status(self.nodes[0], myopid)

        self.sync_all()
        self.nodes[2].generate(1)
        self.sync_all()

        # Verify balance
        assert_equal(self.nodes[0].z_getbalance(saplingAddr0), Decimal('5'))
        assert_equal(self.nodes[1].z_getbalance(saplingAddr1), Decimal('15'))
        assert_equal(self.nodes[1].z_getbalance(taddr1), Decimal('0'))

        # Node 1 sends some shielded funds to node 0, as well as unshielding
        # Sapling -> Sapling
        #         -> taddr
        #         -> Sapling (change)
        recipients = []
        recipients.append({"address": saplingAddr0, "amount": Decimal('5')})
        recipients.append({"address": taddr1, "amount": Decimal('5')})
        myopid = self.nodes[1].z_sendmany(saplingAddr1, recipients, 1, 0)
        wait_and_assert_operationid_status(self.nodes[1], myopid)

        self.sync_all()
        self.nodes[2].generate(1)
        self.sync_all()

        # Verify balance
        assert_equal(self.nodes[0].z_getbalance(saplingAddr0), Decimal('10'))
        assert_equal(self.nodes[1].z_getbalance(saplingAddr1), Decimal('5'))
        assert_equal(self.nodes[1].z_getbalance(taddr1), Decimal('5'))

if __name__ == '__main__':
    WalletSaplingTest().main()
