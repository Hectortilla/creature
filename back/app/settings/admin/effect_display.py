import html
import json

from markupsafe import Markup
from sqlmodel import Session, select

from app.database import engine
from app.models.db.effect import Effect


def effect_summary(owner_kind: str, owner_id: int | None) -> Markup:
    """Render effect atoms attached to an ability, attack, or association."""
    if owner_id is None:
        return Markup("<span class='text-muted'>Sin efectos</span>")

    with Session(engine) as session:
        rows = session.exec(
            select(Effect)
            .where(Effect.owner_kind == owner_kind)
            .where(Effect.owner_id == owner_id)
            .order_by(Effect.sort_order, Effect.id)
        ).all()

    if not rows:
        return Markup("<span class='text-muted'>Sin efectos</span>")

    items = []
    for row in rows:
        trigger = row.trigger or "PASSIVE"
        enabled = "" if row.enabled else " <span class='badge bg-secondary'>inactivo</span>"
        params = html.escape(json.dumps(row.params or {}, ensure_ascii=False, sort_keys=True, indent=2))
        script = f" · script: <code>{html.escape(row.script_id)}</code>" if row.script_id else ""
        notes = f"<div class='text-muted small'>{html.escape(row.notes)}</div>" if row.notes else ""
        items.append(
            "<li class='mb-3'>"
            f"<div><strong>{html.escape(row.atom_type)}</strong> · <code>{html.escape(trigger)}</code>{script}{enabled}</div>"
            f"{notes}"
            f"<pre class='mt-2 mb-0 p-2 bg-light border rounded'><code>{params}</code></pre>"
            "</li>"
        )

    return Markup("<ul class='mb-0 ps-3'>" + "".join(items) + "</ul>")
