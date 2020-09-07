#/*##########################################################################
# Copyright (C) 2019-2020 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
#############################################################################*/
__author__ = "V.A. Sole - ESRF Data Analysis"
__contact__ = "sole@esrf.fr"
__license__ = "MIT"
__copyright__ = "European Synchrotron Radiation Facility, Grenoble, France"
from collections import OrderedDict
from bliss.config import get_sessions_list
from bliss.config.settings import scan as rdsscan        
from bliss.data.node import get_node, get_nodes, DataNode, DataNodeContainer
from bliss.data.nodes.scan import Scan
from bliss.data.nodes.channel import ChannelDataNode

NODE_TYPE = {}
NODE_TYPE["Scan"] = Scan
NODE_TYPE["DataNode"] = DataNode
NODE_TYPE["DataNodeContainer"] = DataNodeContainer
NODE_TYPE["ChannelDataNode"] = ChannelDataNode

def get_node_list(node, node_type=None, name=None, db_name=None, dimension=None,
                  filter=None, unique=False, reverse=False, ignore_underscore=True):
    """
    Return list of nodes matching the given filter
    """
    if not hasattr(node, "name"):
        input_node = get_node(node)
    else:
        input_node = node
    if reverse:
        iterator = input_node.iterator.walk_from_last
    else:
        iterator = input_node.iterator.walk
    if node_type in NODE_TYPE.keys():
        node_type = NODE_TYPE[node_type]
    output_list = []
    # walk not waiting
    if node_type or name or db_name or dimension:
        for node in iterator(wait=False, filter=filter):
            if ignore_underscore and node.name.startswith("_"):
                continue
            if node_type and isinstance(node, node_type):
                output_list.append(node)
            elif name and (node.name == name):
                output_list.append(node)
            elif db_name and node.db_name == db_name:
                output_list.append(node)
            elif dimension:
                if hasattr(node, "shape"):
                    shape = node.shape
                    if len(shape) == dimension:
                        output_list.append(node)
                        print(node.name, node.db_name)
            if unique and len(output_list):
                break 
    else:
        for node in iterator(wait=False, filter=filter):
            #print(node.name, node.db_name, node)
            if ignore_underscore and node.name.startswith("_"):
                continue
            output_list.append(node)
            if unique:
                break
    return output_list

def get_session_scans(session):
    """
    Returns a sorted list of actual scans. Last scan is last.
    """
    nodes = list(_get_session_scans(session))
    nodes = sorted(nodes, key=lambda k: k.info["start_timestamp"])
    return nodes

def _get_session_scans(session):
    if hasattr(session, "name"):
        session_node = session
        session_name = session.name
    else:
        session_node =  get_node(session)
        session_name = session
    db_names = rdsscan( f"{session_name}:*_children_list",
                        count=1000000,
                        connection=session_node.db_connection,
                      )
    # we are interested on actual scans, therefore we do not take scans
    # whose name starts by underscore
    return ( node
             for node in get_nodes(
                *(db_name.replace("_children_list", "") for db_name in db_names)
             )
             if node is not None and node.type == "scan" and not node.name.startswith("_")
            )

def get_session_last_scan(session):
    return get_session_scans(session)[-1]

def get_session_filename(session):
    """
    Return filename associated to last session scan or an empty string
    """
    info = get_session_last_scan(session).info.get_all()
    return info.get("filename", "")

def get_scan_list(session_node):
    return get_node_list(session_node, node_type="Scan", filter="scan")

def get_data_channels(node):
    return get_node_list(node, node_type="ChannelDataNode", filter="channel")

def get_spectra(node, dimension=1):
    return get_node_list(node, filter="channel", dimension=1)

def get_filename(session_node):
    scan_list = get_scan_list(session_node)
    filename = ""
    if len(scan_list):
        info = scan_info(scan_list[-1])
        if "filename" in info:
            filename = info["filename"]
    return filename

def get_filenames(node):
    filenames = []
    if isinstance(node, NODE_TYPE["Scan"]):
        info = scan_info(node)
        if "filename" in info:
            filenames.append(info["filename"])
    else:
        scan_list = get_scan_list(node)
        for scan in scan_list:
            info = scan_info(scan)
            if "filename" in info:
                filename = info["filename"]
                if filename not in filenames:
                    filenames.append(filename)
    return filenames
    
def get_last_spectrum_instances(session_node, offset=None):
    sc = get_scan_list(session_node)
    sc.reverse()
    spectra = OrderedDict()
    if offset is None:
        if len(sc) > 10:
            start = 10
        else:
            start = 0
    else:
        start = offset
    for scan in sc:
        sp = get_spectra(scan)
        names = [(x, x.name) for x in sp]
        for obj, name in names:
            if name not in spectra:
                print("adding name ", obj.db_name, " scan = ", scan.name)
                spectra[name] = (obj, scan) 
    return spectra

def shortnamemap(names, separator=":"):
    """
    Map full Redis names to short (but still unique) names

    :param list(str) names:
    :param str separator:
    :returns dict:
    """
    if not names:
        return {}
    names = set(names)
    parts = [name.split(separator) for name in names]
    nparts = max(map(len, parts))
    parts = [([""] * (nparts - len(lst))) + lst for lst in parts]
    ret = {}
    for i in reversed(range(-nparts, 0)):
        joinednames = [separator.join(s for s in lst[i:] if s) for lst in parts]
        newnames = joinednames + list(ret.values())
        selection = [
            (idx, (separator.join(s for s in lst if s), name))
            for idx, (name, lst) in enumerate(zip(joinednames, parts))
            if newnames.count(name) == 1
        ]
        if selection:
            idx, tuples = list(zip(*selection))
            ret.update(tuples)
            parts = [lst for j, lst in enumerate(parts) if j not in idx]
    return ret
    
def get_scan_data(scan_node):
    data_channels = get_data_channels(scan_node)
    names = shortnamemap(x.name for x in data_channels)
    result = {}
    i = 0
    for channel in data_channels:
        short_name = names[channel.name]
        result[short_name] = channel.get_as_array(0, -1)
        i += 1
    return result

def scan_info(scan_node):
    return scan_node.info.get_all()
        
if __name__ == "__main__":
    import sys
    # get the available sessions
    scan_number = None
    reference = None
    if len(sys.argv) > 1:
        sessions = [sys.argv[1]]
        if len(sys.argv) > 2:
            scan_number = sys.argv[2]
    else:
        sessions = get_sessions_list()
    for session_name in sessions:
        print("SESSION <%s>"  % session_name)
        #connection = client.get_redis_connection(db=1)
        #while not DataNode.exists(session_name, None, connection):
        #    gevent.sleep(1)
        # get node
        session_node = get_node(session_name)
        if not session_node:
            print("\tNot Available")
            continue
        scans = get_session_scan_list(session_node)
        for scan in scans:
            filenames = get_filenames(scan)
            nFiles = len(filenames)
            if not nFiles:
                filename = "No FILE"
            else:
                if nFiles > 1:
                    print("WARNING, more than one file associated to scan")
                filename = filenames[-1]
            title = scan_info(scan).get("title", "No COMMAND")
            if scan_number:
                if scan.name.startswith("161"):
                    reference = scan
            else:
                print("\t%s %s %s"  % (scan.name, filename, title))
    if len(sessions) == 1:
        if reference:
            scan = reference
        else:
            scan = scans[-1]
        print("SCAN = %s" % scan)
        print("NAME = %s" % scan.name)
        print("TITLE = %s" % scan_info(scan).get("title", "No COMMAND"))
        counters = get_data_channels(scan)
        #for counter in counters:
        #    print(counter.name, counter.short_name, counter.dtype, counter.type, counter.info, counter.get_as_array(0, -1))
        print(get_scan_data(scan))
