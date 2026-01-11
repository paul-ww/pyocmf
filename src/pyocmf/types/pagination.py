from typing import Annotated

from pydantic.types import StringConstraints

TransactionContext = Annotated[str, StringConstraints(pattern=r"^T([0-9]+)$")]
FiscalContext = Annotated[str, StringConstraints(pattern=r"^F([0-9]+)$")]
PaginationString = TransactionContext | FiscalContext
