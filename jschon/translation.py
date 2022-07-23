from __future__ import annotations

from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union

from jschon.exceptions import RelativeJSONPointerError
from jschon.json import JSON, JSONCompatible
from jschon.jsonpatch import JSONPatch, JSONPatchOperation, PatchOp
from jschon.jsonpointer import JSONPointer, RelativeJSONPointer
from jschon.jsonschema import JSONSchema, Result
from jschon.output import output_formatter

__all__ = [
    'JSONTranslationSchema',
    'TranslationResult',
    'TranslationFilter',
    'translation_filter',
]


class NoValue:
    pass


class JSONTranslationSchema(JSONSchema):

    def __init__(
            self,
            *args: Any,
            scheme: str = None,
            **kwargs: Any,
    ) -> None:
        self.t9n_scheme: Optional[str] = scheme
        self.t9n_source: Optional[RelativeJSONPointer] = None
        self.t9n_const: Optional[JSONCompatible] = NoValue
        self.t9n_concat: Optional[Tuple[RelativeJSONPointer, ...]] = None
        self.t9n_sep: str = ''
        self.t9n_filter: Optional[Union[str, Dict[str, JSONCompatible]]] = None
        self.t9n_cast: Optional[str] = None
        self.t9n_leaf: bool = True
        super().__init__(*args, **kwargs)

    def evaluate(self, instance: JSON, result: TranslationResult = None) -> Result:
        if self.t9n_source is not None:
            try:
                source = self.t9n_source.evaluate(instance)
            except RelativeJSONPointerError:
                return result
        else:
            source = instance

        super().evaluate(source, result)

        if result.valid and self.t9n_leaf:
            if self.t9n_const is not NoValue:
                value = self.t9n_const
            elif self.t9n_concat is not None:
                value = []
                for item in self.t9n_concat:
                    try:
                        value += [self._make_value(item.evaluate(source))]
                    except RelativeJSONPointerError:
                        pass
                if value:
                    value = self.t9n_sep.join(str(v) for v in value)
                else:
                    value = NoValue
            else:
                value = self._make_value(source)

            if value is not NoValue:
                result.add_translation_patch(self.t9n_scheme, result.t9n_target, value)

        return result

    def _make_value(self, instance: JSON) -> JSONCompatible:
        value = instance.value

        if isinstance(self.t9n_filter, str):
            if filter_fn := _translation_filters.get(self.t9n_filter):
                value = filter_fn(value)
        elif isinstance(self.t9n_filter, dict):
            value = self.t9n_filter.get(value, value)

        if self.t9n_cast == 'boolean':
            value = bool(value)
        elif self.t9n_cast == 'integer':
            value = int(value)
        elif self.t9n_cast == 'number':
            value = float(value)
        elif self.t9n_cast == 'string':
            value = str(value)

        return value


TranslationFilter = Callable[[JSONCompatible], JSONCompatible]
_translation_filters: Dict[str, TranslationFilter] = {}


def translation_filter(name: str = None):
    def decorator(f):
        filter_name = name if isinstance(name, str) else f.__name__
        _translation_filters[filter_name] = f
        return f

    return decorator(name) if callable(name) else decorator


class TranslationResult(Result):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.t9n_target: Optional[JSONPointer] = None
        self.t9n_patchops: Optional[Dict[str, List[JSONPatchOperation]]] = None

    def add_translation_patch(
            self,
            scheme: str,
            target: JSONPointer,
            value: JSONCompatible,
    ) -> None:
        if self.t9n_patchops is None:
            self.t9n_patchops = {}
        self.t9n_patchops.setdefault(scheme, [])
        self.t9n_patchops[scheme] += [JSONPatchOperation(
            op=PatchOp.ADD,
            path=target,
            value=value,
        )]

    def init_array(self, scheme: str, array_path: JSONPointer) -> None:
        self.globals.setdefault(scheme, {})
        self.globals[scheme].setdefault('arrays', {})
        if array_path not in self.globals[scheme]['arrays']:
            self.globals[scheme]['arrays'][array_path] = 0
            self.add_translation_patch(scheme, array_path, [])

    def next_array_index(self, scheme: str, array_path: JSONPointer) -> int:
        next_index = self.globals[scheme]['arrays'][array_path]
        self.globals[scheme]['arrays'][array_path] += 1
        return next_index

    def init_object(self, scheme: str, object_path: JSONPointer) -> None:
        self.globals.setdefault(scheme, {})
        self.globals[scheme].setdefault('objects', set())
        if object_path not in self.globals[scheme]['objects']:
            self.globals[scheme]['objects'] |= {object_path}
            self.add_translation_patch(scheme, object_path, {})


@output_formatter
def patch(result: Result, scheme: str, ignore_validity: bool = False) -> JSONCompatible:
    return JSONPatch(*_visit(result, scheme, ignore_validity)).aslist()


@output_formatter
def translation(result: Result, scheme: str, ignore_validity: bool = False) -> JSONCompatible:
    return JSONPatch(*_visit(result, scheme, ignore_validity)).evaluate(None)


def _visit(node: Result, scheme: str, ignore_validity: bool) -> Iterator[JSONPatchOperation]:
    if ignore_validity or node.valid:
        if hasattr(node, 't9n_patchops'):
            try:
                yield from node.t9n_patchops[scheme]
            except (KeyError, TypeError):
                pass
        for child in node.children.values():
            yield from _visit(child, scheme, ignore_validity)
