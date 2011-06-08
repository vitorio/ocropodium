"""
Utils for dealing with Nodes/Plugins.
"""

import json
import node
import types



class NodeEncoder(json.JSONEncoder):
    """
    Encoder for JSONifying nodes.
    """
    def default(self, n):
        """
        Flatten node for JSON encoding.
        """
        if issubclass(n, node.Node):
            return dict(
                name=n.name,
                description=n.description,
                arity=n.arity,
                stage=n.stage,
                parameters=n.parameters(),
            )
        return super(NodeEncoder, self).default(n)            




