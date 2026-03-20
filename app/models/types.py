from bson import ObjectId
from pydantic import BeforeValidator, PlainSerializer
from typing import Annotated

PyObjectId = Annotated[
    ObjectId,
    BeforeValidator(lambda v: ObjectId(v) if isinstance(v, str) else v),
    PlainSerializer(lambda v: str(v), return_type=str),
]