from collections import OrderedDict
from functools import partial
from typing import Any

from dependency_provider import DependencyProvider


class TransactionContext:
    """A context spanning a single transaction for execution of a function"""

    dependency_provider_factory = DependencyProvider

    def __init__(self, dependency_provider: DependencyProvider = None, *args, **kwargs):
        self.dependency_provider = (
            dependency_provider or self.dependency_provider_factory(*args, **kwargs)
        )
        self._on_enter_transaction_context = lambda ctx: None
        self._on_exit_transaction_context = lambda ctx, exception=None: None
        self._middlewares = []
        self._handlers_iterator = lambda alias: iter([])

    def configure(
        self,
        on_enter_transaction_context=None,
        on_exit_transaction_context=None,
        middlewares=None,
        handlers_iterator=None,
    ):
        if on_enter_transaction_context:
            self._on_enter_transaction_context = on_enter_transaction_context
        if on_exit_transaction_context:
            self._on_exit_transaction_context = on_exit_transaction_context
        if middlewares:
            self._middlewares = middlewares
        if handlers_iterator:
            self._handlers_iterator = handlers_iterator

    def begin(self):
        """Should be used to start a transaction"""
        self._on_enter_transaction_context(self)

    def end(self, exception=None):
        """Should be used to commit/end a transaction"""
        self._on_exit_transaction_context(self, exception)

    def iterate_handlers_for(self, alias: str):
        yield from self._handlers_iterator(alias)

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.end(exc_val)

    def _wrap_with_middlewares(self, handler_func):
        p = handler_func
        for middleware in self._middlewares:
            p = partial(middleware, self, p)
        return p

    def call(self, func, *func_args, **func_kwargs) -> Any:
        if type(func) is str:
            try:
                func = next(self._handlers_iterator(alias=func))
            except StopIteration:
                raise ValueError(f"Handler not found", func)

        dp = self.dependency_provider.copy(ctx=self)
        resolved_kwargs = dp.resolve_func_params(func, func_args, func_kwargs)
        p = partial(func, **resolved_kwargs)
        wrapped_handler = self._wrap_with_middlewares(p)
        result = wrapped_handler()
        return result

    def emit(self, event: str, *args, **kwargs) -> dict[callable, Any]:
        """Emit an event and call all event handlers immediately"""
        all_results = OrderedDict()
        for handler in self._handlers_iterator(alias=event):
            result = self.call(handler, *args, **kwargs)
            all_results[handler] = result
        return all_results

    def get_dependency(self, identifier: Any) -> Any:
        """Get a dependency from the dependency provider"""
        return self.dependency_provider.get_dependency(identifier)

    def __getitem__(self, item) -> Any:
        return self.get_dependency(item)