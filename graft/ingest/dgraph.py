import os
import random
import time
from typing import Any

import pydgraph


__all__ = ["DgraphUploader"]


class DgraphUploader:
    def __init__(self, idx: Any = 0):
        """
        The DgraphUploader actor must initialize its own Dgraph connection
        as it cannot be serialized.

        The idx parameter is provided as a means of identifying individual
        actors.
        """
        # DEV: Cannot serialize the live Dgraph connection.
        self.host = os.getenv("DGRAPH_HOST", "127.0.0.1")
        self.port = os.getenv("DGRAPH_PORT", "9080")
        self.idx = idx

        self.client_stub = pydgraph.DgraphClientStub(f"{self.host}:{self.port}")
        self.client = pydgraph.DgraphClient(self.client_stub)

    def set_schema(self, schema: str):
        """
        Update the Dgraph server's schema.
        """
        self.client.alter(pydgraph.Operation(schema=schema))

    def transact(self, query, mutations, **kwargs):
        """
        Low-level function to actually perform transactions.

        (idx, result, exception)
        """
        exception = None
        result = None
        while True:
            try:
                txn = self.client.txn()

                txn_mutations = []
                if isinstance(mutations, str):
                    # Legacy nquads string-based mutation.
                    mutations = [(None, mutations)]
                for cond, nquads in mutations:
                    # Support a list of cond, nquads string pairs.
                    txn_mutations.append(txn.create_mutation(cond=cond, set_nquads=nquads))

                req = txn.create_request(query=query, mutations=txn_mutations, commit_now=True)
                result = txn.do_request(req)
                break
            except pydgraph.errors.AbortedError:
                # DEV: Avoid thundering herd problem.
                time.sleep(random.random())
                continue
            except Exception as e:
                exception = e
                break
            finally:
                txn.discard()
        return (self.idx, result, exception)
