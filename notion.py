from logging import getLogger
from typing import overload
from notion_py_client import Field, NotionAsyncClient, NotionPage, UpdatePageParameters
from notion_py_client.helper import NotionMapper, NotionPropertyDescriptor
from notion_py_client.properties import (
    TitleProperty,
    RichTextProperty,
    NumberProperty,
    UrlProperty,
    NotionPropertyType,
)
from notion_py_client.requests import (
    TitlePropertyRequest,
    RichTextPropertyRequest,
    NumberPropertyRequest,
    UrlPropertyRequest,
)
from notion_py_client.requests.page_requests import CreatePageParameters
from pydantic import StrictStr
from models import ArxivInfo


class ArxivInfoNotionMapper(NotionMapper[ArxivInfo]):
    title_field: NotionPropertyDescriptor[
        TitleProperty, TitlePropertyRequest, StrictStr
    ] = Field(
        notion_name="Title",
        parser=lambda x: x.title[0].plain_text,
        request_builder=lambda x: TitlePropertyRequest(
            title=[{"text": {"content": x}}]
        ),
    )
    authors_field: NotionPropertyDescriptor[
        RichTextProperty, RichTextPropertyRequest, list[StrictStr]
    ] = Field(
        notion_name="Authors",
        parser=lambda x: [item.plain_text for item in x.rich_text],
        request_builder=lambda x: RichTextPropertyRequest(
            rich_text=[{"text": {"content": author}} for author in x]
        ),
    )
    summary_field: NotionPropertyDescriptor[
        RichTextProperty, RichTextPropertyRequest, StrictStr
    ] = Field(
        notion_name="Summary",
        parser=lambda x: x.rich_text[0].plain_text,
        request_builder=lambda x: RichTextPropertyRequest(
            rich_text=[{"text": {"content": x}}]
        ),
    )
    url_field: NotionPropertyDescriptor[UrlProperty, UrlPropertyRequest, StrictStr] = (
        Field(
            notion_name="Link",
            parser=lambda x: x.url if x.url is not None else "",
            request_builder=lambda x: UrlPropertyRequest(url=x),
        )
    )
    publication_date_field: NotionPropertyDescriptor[
        NumberProperty, NumberPropertyRequest, int
    ] = Field(
        notion_name="Publication Year",
        parser=lambda x: (
            x.number if x.number is not None and type(x.number) is int else 0
        ),
        request_builder=lambda x: NumberPropertyRequest(number=x),
    )

    def to_domain(self, notion_page: NotionPage) -> ArxivInfo:
        properties = notion_page.properties
        title_prop = properties[self.title_field.notion_name]
        if title_prop.type != NotionPropertyType.TITLE:
            raise ValueError("Invalid property type for title")
        authors_prop = properties[self.authors_field.notion_name]
        if authors_prop.type != NotionPropertyType.RICH_TEXT:
            raise ValueError("Invalid property type for authors")
        url_prop = properties[self.url_field.notion_name]
        if url_prop.type != NotionPropertyType.URL:
            raise ValueError("Invalid property type for URL")
        summary_prop = properties[self.summary_field.notion_name]
        if summary_prop.type != NotionPropertyType.RICH_TEXT:
            raise ValueError("Invalid property type for summary")
        publication_year_prop = properties[self.publication_date_field.notion_name]
        if publication_year_prop.type != NotionPropertyType.NUMBER:
            raise ValueError("Invalid property type for publication year")
        return ArxivInfo(
            page_id=notion_page.id,
            title=self.title_field.parse(title_prop),
            authors=self.authors_field.parse(authors_prop),
            summary=self.summary_field.parse(summary_prop),
            publication_year=self.publication_date_field.parse(publication_year_prop),
            url=self.url_field.parse(url_prop),
        )

    def build_update_properties(self, model: ArxivInfo) -> UpdatePageParameters:
        if model.page_id is None:
            raise ValueError("page_id is required for updating a Notion page")
        return UpdatePageParameters(
            page_id=model.page_id,
            properties={
                self.title_field.notion_name: self.title_field.build_request(
                    model.title
                ),
                self.authors_field.notion_name: self.authors_field.build_request(
                    model.authors
                ),
                self.summary_field.notion_name: self.summary_field.build_request(
                    model.summary
                ),
                self.publication_date_field.notion_name: self.publication_date_field.build_request(
                    model.publication_year
                ),
            },
        )

    def build_create_properties(
        self, datasource_id: StrictStr, model: ArxivInfo
    ) -> CreatePageParameters:
        raise NotImplementedError("Create page is not implemented yet.")


class NotionPaperRepository:
    def __init__(self, notion_client: NotionAsyncClient):
        self._notion_client = notion_client
        self._mapper = ArxivInfoNotionMapper()
        self._logger = getLogger(__name__)

    async def update_paper(self, model: ArxivInfo) -> None:
        self._logger.info(f"Updating Notion page for arxiv_id: {model.title}")
        await self._notion_client.pages.update(
            params=self._mapper.build_update_properties(model=model)
        )

    def parse_payload(self, payload: dict) -> ArxivInfo:
        notion_page = NotionPage(**payload["data"])
        return self._mapper.to_domain(notion_page)
