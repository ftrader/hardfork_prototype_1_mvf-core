#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF network separation functionality (TRIG)
#
# on node 0 and 1, block height trigger is set to height 100
# on node 2, block height trigger is set to height 200
#

import os

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *


class MVF_NSEP_Netmagic_Test(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 4)

    def start_all_nodes(self):
        self.nodes = []
        self.is_network_split = False
        self.nodes.append(start_node(0, self.options.tmpdir,
                            ["-forkheight=100", ]))
        self.nodes.append(start_node(1, self.options.tmpdir,
                            ["-forkheight=100", ]))
        self.nodes.append(start_node(2, self.options.tmpdir,
                            ["-forkheight=200", ]))

    def setup_network(self):
        self.start_all_nodes()
        connect_nodes(self.nodes[0], 1)
        connect_nodes(self.nodes[1], 2)
        connect_nodes(self.nodes[2], 0)

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
        for n in xrange(len(self.nodes)):
            assert_equal(False, self.is_fork_triggered_on_node(n)
                                or self.prior_fork_detected_on_node(n))
        print "Fork did not trigger prematurely"

        # check that fork triggers for node 0 at height 100 but not on node 1
        self.nodes[0].generate(1)
        self.sync_all()
        assert_equal(100, self.nodes[0].getblockcount())
        assert_equal(100, self.nodes[1].getblockcount())
        assert_equal(100, self.nodes[2].getblockcount())
        assert_equal(True,  self.is_fork_triggered_on_node(0))
        assert_equal(True,  self.is_fork_triggered_on_node(0))
        assert_equal(False, self.prior_fork_detected_on_node(0))
        assert_equal(True, self.is_fork_triggered_on_node(1))
        assert_equal(False, self.prior_fork_detected_on_node(1))
        assert_equal(False, self.is_fork_triggered_on_node(2))
        assert_equal(False, self.prior_fork_detected_on_node(2))
        print "Fork triggered successfully on nodes 0+1 (block height 100)"

        # check nodes 0+1 no longer accept from node 2
        self.nodes[2].generate(100) 
        time.sleep(5)
        for n in xrange(len(self.nodes)):
            print "block count on node %s: %s" % (n, self.nodes[n].getblockcount())
        assert_equal(100, self.nodes[0].getblockcount())
        assert_equal(100, self.nodes[1].getblockcount())


if __name__ == '__main__':
    MVF_NSEP_Netmagic_Test().main()
