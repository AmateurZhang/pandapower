# -*- coding: utf-8 -*-

# Copyright (c) 2016 by University of Kassel and Fraunhofer Institute for Wind Energy and Energy
# System Technology (IWES), Kassel. All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE file.

from __future__ import division
from builtins import str
__author__ = "Tobias Dess, Jan-Hendrik Menke, Leon Thurner"

import pandapower as pp
import pplog

logger = pplog.getLogger(__name__)
try:
    from pandapower.run import _pd2ppc
except:
    logger.error('cannot import _pd2ppc')
from pandapower.run import reset_results, _select_is_elements
import numpy as np
from scipy.io import savemat


def pd2mat(net, filename, init="flat", calculate_voltage_angles=False, trafo_model="t",
          enforce_q_lims=False):
    """
    Store network in Pypower/Matpower format as mat-file
    Convert 0-based python to 1-based Matlab
    Take care of a few small details

    **INPUT**:
        * net - The Pandapower format network
        * filename - File path + name of the mat file which is created
    """

    # convert to matpower
    net["converged"] = False
    if not init == "results":
        reset_results(net)

    # select elements in service (time consuming, so we do it once)
    is_elems = _select_is_elements(net)

    init_results = True if init == "results" else False
    # convert pandapower net to ppc
    ppc, bus_lookup = _pd2ppc(net, is_elems, calculate_voltage_angles, enforce_q_lims,
                              trafo_model, init_results)

    ppc["busnames"] = list(net.bus.name.values)
    ppc["linenames"] = list(net.line.name.values) + list(net.trafo.name.values)
    # Matlab is one-based, so all entries (buses, lines, gens) have to start with 1 instead of 0
    if len(np.where(ppc["bus"][:, 0] == 0)[0]):
        ppc["bus"][:, 0] = ppc["bus"][:, 0] + 1
        ppc["gen"][:, 0] = ppc["gen"][:, 0] + 1
        ppc["branch"][:, 0:2] = ppc["branch"][:, 0:2] + 1
    # adjust for the matpower converter -> taps should be 0 when there is no transformer, but are 1
    ppc["branch"][np.where(ppc["branch"][:, 8] == 1), 8] = 0
    # version is a string
    ppc["version"] = str(ppc["version"])
    # delete unnecessary fields (for now)
    if None in ppc["busnames"]:
        del ppc["busnames"]
    if None in ppc["linenames"]:
        del ppc["linenames"]
    savemat(filename, ppc)

def ppc_to_mpc(ppc, filename):
    """
    Store network in Pypower/Matpower format as mat-file
    Convert 0-based python to 1-based Matlab
    Take care of a few small details

    **INPUT**:
        * net - The Pandapower format network
        * filename - File path + name of the mat file which is created
    """

    # convert to matpower
    # Matlab is one-based, so all entries (buses, lines, gens) have to start with 1 instead of 0
    if len(np.where(ppc["bus"][:, 0] == 0)[0]):
        ppc["bus"][:, 0] = ppc["bus"][:, 0] + 1
        ppc["gen"][:, 0] = ppc["gen"][:, 0] + 1
        ppc["branch"][:, 0:2] = ppc["branch"][:, 0:2] + 1
    # adjust for the matpower converter -> taps should be 0 when there is no transformer, but are 1
    ppc["branch"][np.where(ppc["branch"][:, 8] == 1), 8] = 0
    # version is a string
    ppc["version"] = str(ppc["version"])
    savemat(filename, ppc)

if __name__ == "__main__":
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, vn_kv=.4)
    b2 = pp.create_bus(net, vn_kv=.4)
    pp.create_ext_grid(net, b1)
    pp.create_line(net, b1, b2, 1., std_type="NAYY 4x50 SE")
    pp.create_line(net, b1, b2, 1., std_type="NAYY 4x50 SE", in_service=False)
    pp.runpp(net)
    pd2mat(net, "test.m")