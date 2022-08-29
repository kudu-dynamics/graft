# Synapse to Dgraph

The goal of this effort is to translate the Synapse data model into a more common RDF ontology that can be reused by other Graph tools like Dgraph.


The effectively desired functionality can be described with the below procedures.

```
synapse_datamodel_to_dgraph_schema(model: Optional[synapse.datamodel.Model])

synapse_podes_to_dgraph_predicates(data: Dict)
```

## Getting Started

There is a `startup.sh` script in the folder to launch a local Dgraph instance for testing.

**NOTE**: there are often data/schema incompatibilities between versions

```
#!/bin/sh

docker run --rm -it \
  --name synapse-to-dgraph \
  -p 8000:8000 \
  -p 8080:8080 \
  -p 9080:9080 \
  dgraph/standalone:v2.0.0-beta
```

## Data Model Introspection + Loading

An essential aspect to both tasks above is programmatically accessing the Synapse data model.

1. Instantiate a Synapse datamodel and load all of the module definitions.
2. Iterate through the forms and scaffold out the Dgraph schema types.
3. Iterate through the properties for each form and generate predicates.
4. Profit.

Notable changes from previous attempts at this problem.

1. Leverage the existing `datamodel.py` module

```python
from typing import Generator, Tuple

import synapse.datamodel
import synapse.models


def load_model_defs() -> Generator[Tuple, None, None]:
    package = synapse.models
    prefix = package.__name__ + "."

    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        module = __import__(modname, fromlist="dummy")

        for item in module.__dict__.values():
            with suppress(AttributeError):
                for model_def in item.getModelDefs(None):
                    yield model_def


if __name__ == "__main__":
    model = synapse.datamodel.Model()
    model.addDataModels([md for md in load_model_defs() if md])
```

The entire datamodel is then populated with convenient mappings and collections for forms, types, etc.

### Forms

Each `synapse.datamodel.Form` object exposes a function called `getRefsOut` where the edges are laid out.

There are 3 different collections that are returned.

```python
for form_name, form_obj in self.model.forms.items():
    for k, v in form_obj.getRefsOut().items():
        print(form_name, k, v)
```

```
econ:acquired prop [('purchase', 'econ:purchase')]
econ:acquired ndef ['item']
econ:acquired array []

tel:txtmesg prop [('from', 'tel:phone'), ('to', 'tel:phone'), ('file', 'file:bytes')]
tel:txtmesg ndef []
tel:txtmesg array [('recipients', 'tel:phone')]
```

My understanding thus far is as follows:

- `prop`: `[(prop_name, edge_form_name), ...]` edges are one-to-one
- `ndef`: `[prop_name, ...]` edges are one-to-one
- `array`: `[(prop_name, edge_form_name)]` edges are one-to-many

My understanding is that the `prop` collections shows what form a property is an edge to.

I don't yet understand the `ndef` collection. I think it's the same as the above.

The array collection seems to denote when a property is a one-to-many edge.

The remaining properties of the form not in any of the above refsOut collections should all be "primitive" types.
