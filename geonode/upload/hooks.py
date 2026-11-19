#########################################################################
#
# Copyright (C) 2026 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
import logging
import typing
from abc import ABC, abstractmethod

from django.conf import settings
from django.utils.module_loading import import_string

from geonode.resource.models import ExecutionRequest
from geonode.upload.handlers.base import BaseHandler

logger = logging.getLogger("importer")


class _Action(typing.NamedTuple):
    event: str
    priority: int
    callback: typing.Callable


class ImporterHooks:
    """
    Registry of the callbacks fired on the lifecycle of an ExecutionRequest.
    Events are named <action>.<phase>, "*" matches any action or phase
    """

    PHASES: typing.Tuple[str, ...] = ("started", "completed", "partially_failed", "failed")

    def __init__(self):
        # in registration order: the stable sort in __callbacks_for relies on it
        self._actions: typing.List[_Action] = []

    def add_action(self, event: str, callback: typing.Callable, priority: int = 10) -> None:
        self.__validate_event(event)
        self._actions.append(_Action(event, priority, callback))

    def remove_action(self, event: str, callback: typing.Callable) -> None:
        self._actions = [_a for _a in self._actions if (_a.event, _a.callback) != (event, callback)]

    def do_action(self, phase: str, execution: ExecutionRequest, **kwargs) -> None:
        """
        Run the callbacks matching the execution action and the phase.
        A failing callback is logged and never stops the others.
        """
        actions = self.__callbacks_for(execution.action, phase)
        if not actions:
            return

        handler = self.__load_handler(execution)
        for action in actions:
            try:
                action.callback(execution, handler, **kwargs)
            except Exception:
                logger.exception(
                    f"Importer hook {action.callback} for event {action.event} "
                    f"failed on execution {execution.exec_id}"
                )

    def reset(self) -> None:
        self._actions = []

    def register_subscribers(self) -> None:
        """
        Register the subscribers listed in IMPORTER_HOOK_SUBSCRIBERS.
        It only adds callbacks: the ones added directly with add_action are kept
        """
        for module_path in settings.IMPORTER_HOOK_SUBSCRIBERS:
            subscriber = import_string(module_path)
            if not issubclass(subscriber, BaseImporterSubscriber):
                raise TypeError(f"{module_path} is not a subclass of BaseImporterSubscriber")
            subscriber().register(self)

    def __validate_event(self, event: str) -> None:
        action, _, phase = event.rpartition(".")
        # the action is not validated: out-of-tree handlers can define their own
        if not action or phase not in (*self.PHASES, "*"):
            raise ValueError(
                f"Invalid importer hook event '{event}', expected <action>.<phase> with phase in {self.PHASES}"
            )

    def __callbacks_for(self, action: str, phase: str) -> typing.List[_Action]:
        # every event the action and phase can match, exact or wildcard: only callbacks subscribed to one of them run
        _events = {f"{action}.{phase}", f"*.{phase}", f"{action}.*", "*.*"}
        return sorted((_a for _a in self._actions if _a.event in _events), key=lambda _a: _a.priority)

    def __load_handler(self, execution: ExecutionRequest) -> typing.Optional[typing.Type[BaseHandler]]:
        if not (_path := (execution.input_params or {}).get("handler_module_path")):
            return None
        # broad on purpose: a broken handler module must not break the status transition firing the event
        try:
            return import_string(_path)
        except Exception as e:
            logger.warning(f"Handler {_path} not available for execution {execution.exec_id}", exc_info=e)
            return None


importer_hooks = ImporterHooks()


class BaseImporterSubscriber(ABC):
    """
    Out-of-tree code subscribes to the importer events by subclassing this
    and listing it in IMPORTER_HOOK_SUBSCRIBERS
    """

    @abstractmethod
    def register(self, hooks: ImporterHooks) -> None:
        """Add the subscriber callbacks to the hooks"""
