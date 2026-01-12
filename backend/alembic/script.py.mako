from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

<%
def _strip_autogen_markers(block: str | None) -> str | None:
    if not block:
        return block
    lines = [line for line in block.splitlines() if not line.lstrip().startswith("# ###")]
    return "\n".join(lines)
%>

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${_strip_autogen_markers(upgrades) if upgrades else "pass"}


def downgrade() -> None:
    ${_strip_autogen_markers(downgrades) if downgrades else "pass"}
