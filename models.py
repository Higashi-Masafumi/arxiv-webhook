from pydantic import BaseModel, StrictInt, StrictStr


class ArxivInfo(BaseModel):
    page_id: StrictStr | None = None
    title: StrictStr
    authors: list[StrictStr]
    summary: StrictStr
    url: StrictStr
    publication_year: StrictInt
