"""
The sinfo parser is used to convert nodes retrieved through a sinfo command on a cluster
to nodes in the format used by Clockwork.
"""

import json

# These functions are translators used in order to handle the values
# we could encounter while parsing a node dictionary retrieved from a
# sinfo command. They are shared with the job (sacct) parser
from slurm_state.helpers.parser_helper import copy, ignore, rename


# This map should contain all the fields that come from parsing a node entry
# Each field should be mapped to a handler that will process the string data
# and set the result in the output dictionary. You can ignore fields, by
# assigning them to 'ignore'

NODE_FIELD_MAP = {
    "architecture": rename("arch"),
    "burstbuffer_network_address": ignore,
    "boards": ignore,
    "boot_time": ignore,
    "comment": copy,
    "cores": copy,
    "cpu_binding": ignore,
    "cpu_load": ignore,
    "cpus": copy,
    "extra": ignore,
    "free_memory": ignore,
    "last_busy": copy,
    "features": copy,
    "active_features": ignore,
    "gres": copy,
    "gres_drained": ignore,
    "gres_used": ignore,
    "mcs_label": ignore,
    "name": copy,
    "next_state_after_reboot": ignore,
    "address": rename("addr"),
    "hostname": ignore,
    "state": copy,
    "state_flags": ignore,
    "next_state_after_reboot_flags": ignore,
    "operating_system": ignore,
    "owner": ignore,
    "partitions": ignore,
    "port": ignore,
    "real_memory": rename("memory"),
    "reason": copy,
    "reason_changed_at": copy,
    "reason_set_by_user": ignore,
    "slurmd_start_time": ignore,
    "sockets": ignore,
    "threads": ignore,
    "temporary_disk": ignore,
    "weight": ignore,
    "tres": copy,
    "slurmd_version": ignore,
    "alloc_memory": ignore,
    "alloc_cpus": ignore,
    "idle_cpus": ignore,
    "tres_used": copy,
    "tres_weighted": ignore,
}


# The node parser itself
def node_parser(f):
    """
    This function parses a report retrieved from a sinfo command (JSON format).
    It acts as an iterator, over all the parsed nodes.

    This is an example of such a command:
        sinfo --json


    Here is an example of some fields that could be encountered in a node of some
    fictitious (and illogical) values associated to these fields:
        {
            "architecture": "x86_64",
            "burstbuffer_network_address": "",
            "boards": 1,
            "boot_time": 1679345346,
            "comment": "",
            "cores": 20,
            "cpu_binding": 0,
            "cpu_load": 2000,
            "extra": "",
            "free_memory": 246,
            "cpus": 40,
            "last_busy": 1681387881,
            "features": "x86_64,turing,48gb",
            "active_features": "x86_64,turing,48gb",
            "gres": "gpu:rtx8000:8(S:0-1)",
            "gres_drained": "N\/A",
            "gres_used": "gpu:rtx8000:8(IDX:0-7),tpu:0",
            "mcs_label": "",
            "name": "node_name",
            "next_state_after_reboot": "invalid",
            "address": "node_addr",
            "hostname": "node_hostname",
            "state": "down",
            "state_flags": [
                "DRAIN"
            ],
            "next_state_after_reboot_flags": [
            ],
            "operating_system": "Linux 4.15.0-194-generic #205-Ubuntu SMP Fri Sep 16 19:49:27 UTC 2022",
            "owner": null,
            "partitions": [
                "debug"
            ],
            "port": 6812,
            "real_memory": 1800,
            "reason": "Sanity Check Failed",
            "reason_changed_at": 1679695880,
            "reason_set_by_user": "root",
            "slurmd_start_time": 1679345380,
            "sockets": 1,
            "threads": 1,
            "temporary_disk": 0,
            "weight": 1,
            "tres": "cpu=40,mem=386618M,billing=96,gres\/gpu=8",
            "slurmd_version": "23.02.1-ex",
            "alloc_memory": 0,
            "alloc_cpus": 0,
            "idle_cpus": 2,
            "tres_used": "cpu=26,mem=249G,gres\/gpu=8",
            "tres_weighted": 0
        },

    The expected output would then be these associations of keys and values:
        {
            "arch": "x86_64",
            "comment": "",
            "cores": 20,
            "cpus": 40,
            "last_busy": 1681387881,
            "features": "x86_64,turing,48gb",
            "gres": gpu:rtx8000:8(S:0-1),
            "name": "node_name",
            "address": "node_addr",
            "state": "down",
            "memory": 1800,
            "reason": "Sanity Check Failed",
            "reason_changed_at": 1679695880,
            "tres": "cpu=40,mem=386618M,billing=96,gres\/gpu=8",
            "tres_used": "cpu=26,mem=249G,gres\/gpu=8"
        }

    Parameters:
        f       JSON report retrieved from a sinfo command
    """
    # Load the JSON file generated by the sinfo command
    sinfo_data = json.load(f)
    # at this point, sinfo_data is a hierarchical structure of dictionaries and lists

    src_nodes = sinfo_data["nodes"]  # nodes is a list

    for src_node in src_nodes:
        res_node = (
            dict()
        )  # Initialize the dictionary which will store the newly formatted node data

        for k, v in src_node.items():
            # We will use a handler mapping to translate this
            translator = NODE_FIELD_MAP.get(k, None)

            if translator is None:
                # Raise an error if the node to parse contains a field we do not handle
                raise ValueError(f"Unknown field in sinfo node output: {k}")

            # Translate using the translator retrieved from NODE_FIELD_MAP
            translator(k, v, res_node)

        yield res_node
