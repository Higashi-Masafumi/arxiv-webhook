from pydantic import BaseModel, StrictInt, StrictStr


class ArxivInfo(BaseModel):
    title: StrictStr
    authors: list[StrictStr]
    summary: StrictStr
    publication_year: StrictInt

    def to_notion_properties(self) -> dict:
        return {
            "Title": {"title": [{"text": {"content": self.title}}]},
            "Authors": {
                "rich_text": [{"text": {"content": author}} for author in self.authors]
            },
            "Summary": {"rich_text": [{"text": {"content": self.summary}}]},
            "Publication Year": {"number": self.publication_year},
        }
