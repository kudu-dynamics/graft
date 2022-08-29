"""
This module provides endpoints for translating the Synapse data model to other
backend systems.
"""
from contextlib import suppress
import inspect
import pkgutil
from typing import Any, Dict, Generator, List, Optional, Tuple

import synapse.datamodel as SDM
import synapse.lib.types as SLT
import synapse.models as SM

import graft.translate.utils as utils


__all__ = [
    "dgraph_schema_from_datamodel",
    "dgraph_translate_form",
    "dgraph_translate_node",
]


# DEV: refer to `synapse.datamodel.Model.__init__`
SYN_PRIMITIVE_TYPES = [
    # Array
    "Bool",
    "Comp",
    "Data",
    "Edge",
    "Guid",
    "Hex",
    "IntBase",
    # Ival
    "Latitude",
    "LatLong",
    "Loc",
    "Longitude",
    # Ndef
    # NodeProp
    # Range
    "StrBase",
    # SynTag
    # Time
    # TimeEdge
]

# DEV: Given a Synapse model python type, provide a mapping to corresponding
#      Dgraph types.
SYN_TYPE_TO_BASE = {
    "Bool": "bool",
    "Comp": "",
    "Data": "string",
    "Edge": "",
    "FileBytes": "string",
    "Fqdn": "string",
    "Guid": "string",
    "Hex": "string",
    "Imei": "string",
    "Imsi": "string",
    "IntBase": "int",
    # DEV: IPv4 as a string is a notable deviation from the Synapse
    #      model.
    "IPv4": "string",
    "IPv6": "string",
    "Latitude": "float",
    "LatLong": "geo",
    "Loc": "string",
    "Longitude": "float",
    "Phone": "string",
    "SemVer": "string",
    "StrBase": "string",
}

# Singleton object to cache a model once it has been formed.
SYN_MODEL = None


# Utilities


def _blank_translation() -> Dict:
    return {
        "unique": False,
        "predicate": None,
        "value": None,
        "synapse_form": None,
        "dgraph_type": None,
        "is_edge": False,
        "edge_predicate": None,
    }


def _make_translation() -> Dict:
    """
    Inspects the caller's locals dictionary for special keyword variables.
    """
    result = {}

    frame = inspect.currentframe()
    try:
        ldict = frame.f_back.f_locals
        result.update(_blank_translation())
        for k, v in ldict.items():
            if k in result:
                result[k] = v
    finally:
        del frame
    return result


def _unpack_translation(data):
    """
    Inspects the caller's locals dictionary and updates it with special keyword
    variables from the provided translation data.
    """
    frame = inspect.currentframe()
    try:
        ldict = frame.f_back.f_locals
        for k, v in data.items():
            ldict[k] = v
    finally:
        del frame


def _load_model_defs() -> Generator[Tuple, None, None]:
    """
    Walk the Synapse models module hierarchy and import model definitions from
    them.
    """
    package = SM
    prefix = package.__name__ + "."

    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        module = __import__(modname, fromlist="dummy")
        for item in module.__dict__.values():
            with suppress(AttributeError):
                for model_def in item.getModelDefs(None):
                    yield model_def


def _load_model() -> SDM.Model:
    global SYN_MODEL
    if not SYN_MODEL:
        SYN_MODEL = SDM.Model()
        SYN_MODEL.addDataModels([md for md in _load_model_defs() if md])
    return SYN_MODEL


def _get_dgraph_type(prop: SDM.Prop, is_form: bool = False) -> Optional[SLT.Type]:
    """
    Given a Synapse datamodel property (or form) object, return the corresponding
    Dgraph type.
    """
    # Get the base type.
    base_classes = inspect.getmro(prop.type.__class__)
    idx = base_classes.index(SLT.Type)
    base_class_name = base_classes[idx - 1].__name__
    if not is_form and base_class_name not in SYN_PRIMITIVE_TYPES:
        return "[uid]"
    with suppress(KeyError):
        return SYN_TYPE_TO_BASE[base_class_name]
    return f"TODO {base_class_name}"


def _format_predicate(predicate_name: str, predicate_type: str) -> str:
    index = ""
    with suppress(KeyError):
        index = {
            "bool": "@index(bool)",
            "float": "@index(float)",
            "geo": "@index(geo)",
            "int": "@index(int)",
            "string": "@index(hash)",
        }[predicate_type]
    return f"<{predicate_name}>: {predicate_type} {index} ."


def _format_type(form_name: str, predicates: List[str]) -> str:
    type_name = utils.pascalify(form_name)
    result = ""
    result += f"type {type_name} {{\n"
    result += "\n".join(f"    <{pred}>" for pred in predicates)
    result += "\n}\n"
    return result


# API endpoints


def dgraph_schema_from_datamodel(model: Optional[SDM.Model] = None) -> str:
    """
    If no model is provided, one will be generated from introspecting the
    Synapse module.
    """
    if not model:
        model = _load_model()

    predicates = []
    types = []

    for form_name in model.forms.keys():
        form_predicates = list(dgraph_translate_form(form_name, model))
        predicates.extend(_format_predicate(*pred_pair[:2]) for pred_pair in form_predicates)
        types.append(_format_type(form_name, [x[0] for x in form_predicates]))

    result = ""
    result += "\n".join(predicates) + "\n"
    result += "\n"
    result += "\n".join(types)
    return result


def dgraph_translate_form(
    form_name: str, model: Optional[SDM.Model] = None
) -> Generator[Tuple[str, str, str], None, None]:
    """
    Given a Synapse form, yield all of the corresponding Dgraph predicates for
    the properties.

    (dgraph_predicate, dgraph_type, form_name)
    """
    if not model:
        model = _load_model()

    form_object = model.forms[form_name]

    # Translate a primary property if necessary.
    # DEV: as an example, compound nodes do not need to retain the redundant
    #      compound node string as the Dgraph upsert procedure would check
    #      for the existing of each significant edge.
    # DEV: assumption is that the primary property is never an edge.
    dgraph_predicate = utils.dotify(form_name)
    dgraph_type = _get_dgraph_type(form_object, is_form=True)
    if dgraph_type:
        yield (dgraph_predicate, dgraph_type, form_name)

    # Create a map for which properties are edges.
    edge_map = {}
    for coll_name, coll_obj in form_object.getRefsOut().items():
        dgraph_type = "[uid]" if coll_name == "array" else "uid"
        for item_obj in coll_obj:
            item_name = item_obj if isinstance(item_obj, str) else item_obj[0]
            edge_map[item_name] = dgraph_type

    for prop_name, prop_obj in form_object.props.items():
        # DEV: Ignore these for now.
        if prop_name in [".created", ".seen"]:
            continue

        dgraph_predicate = utils.dotify(f"{form_name}.{prop_name}")
        dgraph_type = edge_map.get(prop_name, _get_dgraph_type(prop_obj))
        if dgraph_type:
            yield (dgraph_predicate, dgraph_type, prop_obj.typedef[0])


def dgraph_translate_node(node: Tuple[Tuple, Dict], model: Optional[SDM.Model] = None) -> Generator[Dict, None, None]:
    if not model:
        model = _load_model()

    (form, value), info = node

    predicate_map = {
        "dgraph.type": (None, None),
    }
    for predicate in dgraph_translate_form(form, model):
        dgraph_predicate, dgraph_type, form_name = predicate
        predicate_map[dgraph_predicate] = (dgraph_type, form_name)

    def match(predicate: str, value: Any, **kwargs) -> Dict:
        # DEV: Ignore global properties for now.
        if ".." in predicate:
            return {}
        if predicate not in predicate_map:
            return {}
        dgraph_type, synapse_form = predicate_map[predicate]
        is_edge = dgraph_type in ("uid", "[uid]")
        if is_edge:
            edge_predicate = utils.dotify(synapse_form)  # noqa: F841
        result = _make_translation()
        result.update(kwargs)
        return result

    # Match the primary property.
    primary = match(utils.dotify(form), value, unique=True)
    if primary:
        yield primary

    # Yield the Dgraph type.
    yield match("dgraph.type", utils.pascalify(form))

    # Match any secondary properties that are present.
    for prop, value in info.get("props", {}).items():
        secondary = match(f"{utils.dotify(form)}.{prop}", value)
        if not secondary:
            continue
        yield secondary
