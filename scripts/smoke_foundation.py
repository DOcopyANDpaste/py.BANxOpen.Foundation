"""NX smoke test for BANxOpen Foundation. Read-only: the part is left exactly as it was.

Run in NX 2606 with a part open (ideally one with bodies and BA_REQ requirements written by the C# bead tool):
    File > Execute > Journal (Alt+F8) > this file

Checks, in the Listing Window:
  1. logging reaches NX (syslog + Listing Window with BANXOPEN_DEBUG=1)
  2. NxSessionContext.try_initialize, application name, UF is_alive
  3. UndoScope rolls back an uncommitted scope without error
  4. BodyResolver resolves every body back from its BodyId
  5. The requirement store reads and audits a domain written by the C# tools (no refresh: nothing is written)
"""

import logging
import os
import sys
import traceback
from pathlib import Path

# Run straight from the repo: put src/ on the path unless the package is already deployed.
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import NXOpen  # noqa: E402

from banxopen.foundation.nx import (  # noqa: E402
    BodyResolver,
    NxSessionContext,
    UndoScope,
    create_requirement_store,
    install_nx_logging,
)

DOMAIN = os.environ.get("BANXOPEN_SMOKE_DOMAIN", "SHEETMETAL.BEAD")


def main() -> None:
    session = NXOpen.Session.GetSession()
    lw = session.ListingWindow
    lw.Open()

    def say(line: str) -> None:
        lw.WriteLine(line)

    try:
        settings = install_nx_logging(session)
        logging.getLogger("banxopen.smoke").info("Foundation smoke test started.")
        say(f"[1] logging installed: target={settings.target.value} debug={settings.debug}")

        started = NxSessionContext.try_initialize()
        if not started.ok or started.value is None:
            say(f"[2] FAILED: {started.error_code}: {started.message}")
            return
        ctx = started.value
        say(
            f"[2] context ok: part={ctx.work_part.Name} app='{ctx.current_application}' "
            f"sheet_metal={ctx.is_sheet_metal_application} ui={'yes' if ctx.ui else 'no'}"
        )

        with UndoScope(ctx.session, "BANxOpen smoke (rolled back)"):
            pass  # not committed: must roll back silently
        say("[3] UndoScope rolled back an uncommitted scope")

        resolver = BodyResolver(ctx)
        bodies = resolver.refresh()
        unresolved = [b.Name for b in bodies if resolver.resolve(BodyResolver.body_id(b)) is None]
        alive = sum(1 for b in bodies if ctx.is_alive(b.Tag))
        say(f"[4] bodies={len(bodies)} alive={alive} unresolved={unresolved or 'none'}")
        for body in bodies[:5]:
            say(f"      {BodyResolver.body_id(body)}  ({body.Name})")

        store = create_requirement_store(ctx)
        read = store.read(DOMAIN)
        say(f"[5] domain {DOMAIN}: {len(read.requirements)} requirement(s), {len(read.errors)} error(s)")
        for stored in read.requirements:
            s = stored.spec
            say(f"      {s.key} / {s.aspect}: {s.rule} -> {stored.status.value}")
        for error in read.errors:
            say(f"      read error: {error}")
        for line in store.audit(DOMAIN):
            say(f"      audit: {line}")
        say("Smoke test finished.")
    except Exception:  # report everything: this is a diagnostic journal
        say("Smoke test crashed:\n" + traceback.format_exc())


if __name__ == "__main__":
    main()
