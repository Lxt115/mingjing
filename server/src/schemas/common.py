from pydantic import BaseModel


def to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class CamelModel(BaseModel):
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "alias_generator": to_camel,
    }


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: object = None
    timestamp: float = 0
