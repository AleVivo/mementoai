from bson import ObjectId
from pydantic import PlainSerializer
from typing import Annotated

PyObjectId = Annotated[
    ObjectId,
    PlainSerializer(lambda v: str(v), return_type=str)
]