"""Maps between `BodyId` and live NXOpen bodies in the work part."""

# NX 2412's Python stubs declare instance methods without `self`, type enum members as int and give collections
# no __iter__; these rules would only report those stub defects here. Everything else is still checked.
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportReturnType=false
# pyright: reportCallIssue=false, reportGeneralTypeIssues=false

import logging
from typing import TYPE_CHECKING

from banxopen.foundation.model.ids import BodyId

if TYPE_CHECKING:
    import NXOpen

    from banxopen.foundation.nx_adapters.session_context import NxSessionContext

_log = logging.getLogger(__name__)


class BodyResolver:
    """Callers that need live state call `refresh()` first, so the lookup never survives across calls."""

    def __init__(self, context: NxSessionContext) -> None:
        self._context = context
        self._bodies_by_id: dict[BodyId, NXOpen.Body] = {}

    def refresh(self) -> list[NXOpen.Body]:
        """Rescan the work part's bodies. Returns all of them, in NX order."""
        bodies: list[NXOpen.Body] = []
        by_id: dict[BodyId, NXOpen.Body] = {}
        for body in self._context.work_part.Bodies:
            bodies.append(body)
            body_id = BodyResolver.body_id(body)
            if body_id in by_id:
                _log.warning(
                    "Body '%s' (JournalIdentifier='%s', Tag=%s) collides with an already-scanned body on BodyId '%s' "
                    "— the earlier body will be overwritten in the lookup.",
                    body.Name,
                    body.JournalIdentifier,
                    body.Tag,
                    body_id,
                )
            by_id[body_id] = body
        self._bodies_by_id = by_id
        return bodies

    def resolve(self, body_id: BodyId) -> NXOpen.Body | None:
        return self._bodies_by_id.get(body_id)

    @staticmethod
    def body_id(body: NXOpen.Body) -> BodyId:
        # VERIFY (carried from C#): that JournalIdentifier survives save/close/reopen.
        return BodyId(body.JournalIdentifier)
