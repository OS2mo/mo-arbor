from typing import Any
from uuid import UUID

from ._testing__acknowledge_event import TestingAcknowledgeEvent
from ._testing__create_class import TestingCreateClass
from ._testing__create_class import TestingCreateClassClassCreate
from ._testing__create_facet import TestingCreateFacet
from ._testing__create_facet import TestingCreateFacetFacetCreate
from ._testing__declare_event_listener import TestingDeclareEventListener
from ._testing__declare_event_listener import (
    TestingDeclareEventListenerEventListenerDeclare,
)
from ._testing__fetch_event import TestingFetchEvent
from ._testing__fetch_event import TestingFetchEventEventFetch
from ._testing__get_org_unit_history import TestingGetOrgUnitHistory
from ._testing__get_org_unit_history import TestingGetOrgUnitHistoryOrgUnits
from .async_base_client import AsyncBaseClient
from .create_org_unit import CreateOrgUnit
from .create_org_unit import CreateOrgUnitOrgUnitCreate
from .enums import FileStore
from .get_class import GetClass
from .get_class import GetClassClasses
from .get_org_unit import GetOrgUnit
from .get_org_unit import GetOrgUnitOrgUnits
from .input_types import ClassCreateInput
from .input_types import EventSendInput
from .input_types import FacetCreateInput
from .input_types import ListenerCreateInput
from .input_types import OrganisationUnitCreateInput
from .input_types import OrganisationUnitTerminateInput
from .input_types import OrganisationUnitUpdateInput
from .list_files import ListFiles
from .list_files import ListFilesFiles
from .read_file import ReadFile
from .read_file import ReadFileFiles
from .send_event import SendEvent
from .terminate_org_unit import TerminateOrgUnit
from .terminate_org_unit import TerminateOrgUnitOrgUnitTerminate
from .update_org_unit import UpdateOrgUnit
from .update_org_unit import UpdateOrgUnitOrgUnitUpdate


def gql(q: str) -> str:
    return q


class GraphQLClient(AsyncBaseClient):
    async def get_org_unit(self, uuid: UUID) -> GetOrgUnitOrgUnits:
        query = gql("""
            query GetOrgUnit($uuid: UUID!) {
              org_units(filter: {uuids: [$uuid], from_date: null, to_date: null}) {
                objects {
                  current {
                    user_key
                    name
                    parent_response {
                      uuid
                    }
                    unit_type_response {
                      uuid
                    }
                    unit_level_response {
                      uuid
                    }
                  }
                  validities {
                    validity {
                      from
                      to
                    }
                  }
                }
              }
            }
            """)
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return GetOrgUnit.parse_obj(data).org_units

    async def get_class(self, facet: str, user_key: str) -> GetClassClasses:
        query = gql("""
            query GetClass($facet: String!, $user_key: String!) {
              classes(filter: {facet: {user_keys: [$facet]}, user_keys: [$user_key]}) {
                objects {
                  uuid
                }
              }
            }
            """)
        variables: dict[str, object] = {"facet": facet, "user_key": user_key}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return GetClass.parse_obj(data).classes

    async def create_org_unit(
        self, input: OrganisationUnitCreateInput
    ) -> CreateOrgUnitOrgUnitCreate:
        query = gql("""
            mutation CreateOrgUnit($input: OrganisationUnitCreateInput!) {
              org_unit_create(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return CreateOrgUnit.parse_obj(data).org_unit_create

    async def update_org_unit(
        self, input: OrganisationUnitUpdateInput
    ) -> UpdateOrgUnitOrgUnitUpdate:
        query = gql("""
            mutation UpdateOrgUnit($input: OrganisationUnitUpdateInput!) {
              org_unit_update(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return UpdateOrgUnit.parse_obj(data).org_unit_update

    async def terminate_org_unit(
        self, input: OrganisationUnitTerminateInput
    ) -> TerminateOrgUnitOrgUnitTerminate:
        query = gql("""
            mutation TerminateOrgUnit($input: OrganisationUnitTerminateInput!) {
              org_unit_terminate(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TerminateOrgUnit.parse_obj(data).org_unit_terminate

    async def list_files(self, file_store: FileStore) -> ListFilesFiles:
        query = gql("""
            query ListFiles($file_store: FileStore!) {
              files(filter: {file_store: $file_store}) {
                objects {
                  file_name
                }
              }
            }
            """)
        variables: dict[str, object] = {"file_store": file_store}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return ListFiles.parse_obj(data).files

    async def read_file(self, file_store: FileStore, file_name: str) -> ReadFileFiles:
        query = gql("""
            query ReadFile($file_store: FileStore!, $file_name: String!) {
              files(filter: {file_store: $file_store, file_names: [$file_name]}) {
                objects {
                  base64_contents
                }
              }
            }
            """)
        variables: dict[str, object] = {
            "file_store": file_store,
            "file_name": file_name,
        }
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return ReadFile.parse_obj(data).files

    async def send_event(self, input: EventSendInput) -> bool:
        query = gql("""
            mutation SendEvent($input: EventSendInput!) {
              event_send(input: $input)
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return SendEvent.parse_obj(data).event_send

    async def _testing__declare_event_listener(
        self, input: ListenerCreateInput
    ) -> TestingDeclareEventListenerEventListenerDeclare:
        query = gql("""
            mutation _Testing_DeclareEventListener($input: ListenerCreateInput!) {
              event_listener_declare(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingDeclareEventListener.parse_obj(data).event_listener_declare

    async def _testing__fetch_event(
        self, listener: UUID
    ) -> TestingFetchEventEventFetch | None:
        query = gql("""
            query _Testing_FetchEvent($listener: UUID!) {
              event_fetch(filter: {listener: $listener}) {
                subject
                token
              }
            }
            """)
        variables: dict[str, object] = {"listener": listener}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingFetchEvent.parse_obj(data).event_fetch

    async def _testing__acknowledge_event(self, token: Any) -> bool:
        query = gql("""
            mutation _Testing_AcknowledgeEvent($token: EventToken!) {
              event_acknowledge(input: {token: $token})
            }
            """)
        variables: dict[str, object] = {"token": token}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingAcknowledgeEvent.parse_obj(data).event_acknowledge

    async def _testing__create_facet(
        self, input: FacetCreateInput
    ) -> TestingCreateFacetFacetCreate:
        query = gql("""
            mutation _Testing_CreateFacet($input: FacetCreateInput!) {
              facet_create(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingCreateFacet.parse_obj(data).facet_create

    async def _testing__create_class(
        self, input: ClassCreateInput
    ) -> TestingCreateClassClassCreate:
        query = gql("""
            mutation _Testing_CreateClass($input: ClassCreateInput!) {
              class_create(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingCreateClass.parse_obj(data).class_create

    async def _testing__get_org_unit_history(
        self, uuid: UUID
    ) -> TestingGetOrgUnitHistoryOrgUnits:
        query = gql("""
            query _Testing_GetOrgUnitHistory($uuid: UUID!) {
              org_units(filter: {uuids: [$uuid], from_date: null, to_date: null}) {
                objects {
                  validities {
                    name
                    validity {
                      from
                      to
                    }
                  }
                }
              }
            }
            """)
        variables: dict[str, object] = {"uuid": uuid}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return TestingGetOrgUnitHistory.parse_obj(data).org_units
