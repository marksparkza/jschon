from __future__ import annotations

from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from jschon.exceptions import RelativeJSONPointerError
from jschon.json import JSON, JSONCompatible
from jschon.jsonpatch import JSONPatch, JSONPatchOperation, PatchOp
from jschon.jsonpointer import JSONPointer, RelativeJSONPointer
from jschon.jsonschema import JSONSchema, Scope
from jschon.output import JSONSchemaOutputFormatter

__all__ = [
    'JSONTranslationSchema',
    'TranslationScope',
    'TranslationOutputFormatter',
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

    def evaluate(self, instance: JSON, scope: TranslationScope = None) -> Scope:
        if self.t9n_source is not None:
            try:
                source = self.t9n_source.evaluate(instance)
            except RelativeJSONPointerError:
                return scope
        else:
            source = instance

        super().evaluate(source, scope)

        if scope.valid and self.t9n_leaf:
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
                scope.add_translation_patch(self.t9n_scheme, scope.t9n_target, value)

        return scope

    def _make_value(self, instance: JSON) -> JSONCompatible:
        result = instance.value

        if isinstance(self.t9n_filter, str):
            if filter_fn := _translation_filters.get(self.t9n_filter):
                result = filter_fn(result)
        elif isinstance(self.t9n_filter, dict):
            result = self.t9n_filter.get(result, result)

        if self.t9n_cast == 'boolean':
            result = bool(result)
        elif self.t9n_cast == 'integer':
            result = int(result)
        elif self.t9n_cast == 'number':
            result = Decimal(f'{result}')
        elif self.t9n_cast == 'string':
            result = str(result)

        return result


TranslationFilter = Callable[[JSONCompatible], JSONCompatible]
_translation_filters: Dict[str, TranslationFilter] = {}


def translation_filter(name: str = None):
    def decorator(f):
        filter_name = name if isinstance(name, str) else f.__name__
        _translation_filters[filter_name] = f
        return f

    return decorator(name) if callable(name) else decorator


class TranslationScope(Scope):
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


class TranslationOutputFormatter(JSONSchemaOutputFormatter):

    def create_output(self, scope: Scope, format: str, **kwargs: Any) -> JSONCompatible:
        def visit(node: Scope):
            if node.valid:
                if hasattr(node, 't9n_patchops'):
                    try:
                        yield from node.t9n_patchops[scheme]
                    except (KeyError, TypeError):
                        pass
                for child in node.iter_children():
                    yield from visit(child)

        if format in ('patch', 'translation'):
            try:
                scheme = kwargs.pop('scheme')
            except KeyError:
                raise TypeError("Missing keyword argument 'scheme'")

            patch = JSONPatch(*(patchop for patchop in visit(scope)))
            if format == 'patch':
                return patch.aslist()
            else:
                return patch.evaluate(None)

        return super().create_output(scope, format, **kwargs)
