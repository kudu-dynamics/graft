import sys

from graft.ingest.dgraph import DgraphUploader
from graft.translate.synapse import dgraph_schema_from_datamodel


def main(argv=None):
    schema = dgraph_schema_from_datamodel()
    print(schema)
    if input("upload? (y/n): ") == "y":
        DgraphUploader().set_schema(schema)
    return 0


if __name__ == "__main__":
    sys.exit(main())
