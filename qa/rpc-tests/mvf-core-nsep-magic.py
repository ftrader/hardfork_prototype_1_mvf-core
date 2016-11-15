#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF network separation functionality (TRIG)
#
# on node 0 and 1, block height trigger is set to height 100
# on node 2 and 3, block height trigger is set to height 999999 (don't trigger during test)
#
# blocks are generated on node 0 to trigger the fork.
# it is checked that nodes 0 and 1 are still peers with each other,
# but not with nodes 2 and 3, and vice versa.
#
# some more blocks are generated on the different nodes to check that
# two separate chains are being formed.

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *


class MVF_NSEP_Netmagic_Test(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 4)

    def start_all_nodes(self):
        self.nodes = []
        self.is_network_split = False    # not in the beginning it isn't
        self.nodes.append(start_node(0, self.options.tmpdir,
                            ["-forkheight=100", ]))
        self.nodes.append(start_node(1, self.options.tmpdir,
                            ["-forkheight=100", ]))
        self.nodes.append(start_node(2, self.options.tmpdir,
                            ["-forkheight=999999", ]))
        self.nodes.append(start_node(3, self.options.tmpdir,
                            ["-forkheight=999999", ]))

    def setup_network(self):
        self.start_all_nodes()
        # connect them all to each other
        connect_nodes(self.nodes[0], 1)
        connect_nodes(self.nodes[0], 2)
        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 2)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[2], 3)

    def prior_fork_detected_on_node(self, node=0):
        """ check in log file if prior fork has been detected and return true/false """
        nodelog = self.options.tmpdir + "/node%s/regtest/debug.log" % node
        marker_found = search_file(nodelog, "MVF: found marker config file")
        return (len(marker_found) > 0)

    def is_fork_triggered_on_node(self, node=0):
        """ check in log file if fork has triggered and return true/false """
        # MVF-Core TODO: extend to check using RPC info about forks
        nodelog = self.options.tmpdir + "/node%s/regtest/debug.log" % node
        hf_active = (search_file(nodelog, "isMVFHardForkActive=1") and
                     search_file(nodelog, "enabling isMVFHardForkActive"))
        fork_actions_performed = search_file(nodelog, "MVF: performing fork activation actions")
        return (len(hf_active) > 0 and len(fork_actions_performed) == 1)

    def run_test(self):
        # check that fork does not triggered before the height
        print "Generating 99 pre-fork blocks"
        for b in range(99):
            self.nodes[0].generate(1)
        self.sync_all()
        print "synching blocks"
        sync_blocks(self.nodes[:4])
        print "synching mempools"
        sync_mempools(self.nodes[:4])
        print "checking that fork did not trigger on any node"
        for n in xrange(len(self.nodes)):
            assert_equal(False, self.is_fork_triggered_on_node(n)
                                or self.prior_fork_detected_on_node(n))
        print "Fork did not trigger prematurely"

        print "checking block height = 99 on all nodes"
        assert_equal(99, self.nodes[0].getblockcount())
        assert_equal(99, self.nodes[1].getblockcount())
        assert_equal(99, self.nodes[2].getblockcount())
        assert_equal(99, self.nodes[3].getblockcount())

        print "generating fork block on node 0"
        self.nodes[0].generate(1)
        print "synching blocks on nodes 0+1"
        sync_blocks(self.nodes[:2])
        print "synching mempools on nodes 0+1"
        sync_mempools(self.nodes[:2])
        print "synching blocks on nodes 2+3"
        sync_blocks(self.nodes[2:])
        print "synching mempools on nodes 2+3"
        sync_mempools(self.nodes[2:])

        assert_equal(100, self.nodes[0].getblockcount())
        assert_equal(100, self.nodes[1].getblockcount())
        assert_equal( 99, self.nodes[2].getblockcount())
        assert_equal( 99, self.nodes[3].getblockcount())
        # check nodes 0, 1 have forked
        for n in (0,1):
           assert_equal(True,  self.is_fork_triggered_on_node(n))
           assert_equal(False, self.prior_fork_detected_on_node(n))
        # ... and nodes 2, 3 have not
        for n in (2,3):
            assert_equal(False, self.is_fork_triggered_on_node(n))
            assert_equal(False, self.prior_fork_detected_on_node(n))
        print "Fork triggered successfully on nodes 0+1 (block height 100)"
        print "Fork NOT triggered on nodes 2+3 (block height 99)"

        # check that the chains are now separate
        print "generating another post-fork block on node 0"
        self.nodes[0].generate(1)
        print "synching blocks on nodes 0+1"
        sync_blocks(self.nodes[:2])
        print "synching mempools on nodes 0+1"
        sync_mempools(self.nodes[:2])
        print "synching blocks on nodes 2+3"
        sync_blocks(self.nodes[2:])
        print "synching mempools on nodes 2+3"
        sync_mempools(self.nodes[2:])
        assert_equal(101, self.nodes[0].getblockcount())
        assert_equal(101, self.nodes[1].getblockcount())
        assert_equal( 99, self.nodes[2].getblockcount())
        assert_equal( 99, self.nodes[3].getblockcount())

        print "generating 3 blocks on node 2"
        self.nodes[2].generate(3)
        print "synching blocks on nodes 0+1"
        sync_blocks(self.nodes[:2])
        print "synching mempools on nodes 0+1"
        sync_mempools(self.nodes[:2])
        print "synching blocks on nodes 2+3"
        sync_blocks(self.nodes[2:])
        print "synching mempools on nodes 2+3"
        sync_mempools(self.nodes[2:])
        assert_equal(101, self.nodes[0].getblockcount())
        assert_equal(101, self.nodes[1].getblockcount())
        assert_equal(102, self.nodes[2].getblockcount())
        assert_equal(102, self.nodes[3].getblockcount())

if __name__ == '__main__':
    MVF_NSEP_Netmagic_Test().main()
