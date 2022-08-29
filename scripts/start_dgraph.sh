#!/bin/sh

DGRAPH_VERSION="v20.03.0"

docker run --rm -it \
  --name synapse-to-dgraph \
  -p 8000:8000 \
  -p 8080:8080 \
  -p 9080:9080 \
  "dgraph/standalone:${DGRAPH_VERSION}"
