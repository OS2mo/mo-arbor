from uuid import UUID

from .base_model import BaseModel


class GetFacet(BaseModel):
    facets: "GetFacetFacets"


class GetFacetFacets(BaseModel):
    objects: list["GetFacetFacetsObjects"]


class GetFacetFacetsObjects(BaseModel):
    uuid: UUID


GetFacet.update_forward_refs()
GetFacetFacets.update_forward_refs()
GetFacetFacetsObjects.update_forward_refs()
