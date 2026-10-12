from typing import Any
from uuid import UUID

from .acknowledge_event import AcknowledgeEvent
from .async_base_client import AsyncBaseClient
from .create_class import CreateClass
from .create_class import CreateClassClassCreate
from .create_facet import CreateFacet
from .create_facet import CreateFacetFacetCreate
from .create_org_unit import CreateOrgUnit
from .create_org_unit import CreateOrgUnitOrgUnitCreate
from .declare_event_listener import DeclareEventListener
from .declare_event_listener import DeclareEventListenerEventListenerDeclare
from .enums import FileStore
from .fetch_event import FetchEvent
from .fetch_event import FetchEventEventFetch
from .get_class import GetClass
from .get_class import GetClassClasses
from .get_org_unit import GetOrgUnit
from .get_org_unit import GetOrgUnitOrgUnits
from .get_org_unit_history import GetOrgUnitHistory
from .get_org_unit_history import GetOrgUnitHistoryOrgUnits
from .input_types import ClassCreateInput
from .input_types import EventSendInput
from .input_types import FacetCreateInput
from .input_types import ListenerCreateInput
from .input_types import OrganisationUnitCreateInput
from .input_types import OrganisationUnitTerminateInput
from .input_types import OrganisationUnitUpdateInput
from .list_events import ListEvents
from .list_events import ListEventsEvents
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
                    parent {
                      uuid
                    }
                    unit_type {
                      uuid
                    }
                    org_unit_level {
                      uuid
                    }
                  }
                  validities {
                    validity {
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

    async def create_facet(self, input: FacetCreateInput) -> CreateFacetFacetCreate:
        query = gql("""
            mutation CreateFacet($input: FacetCreateInput!) {
              facet_create(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return CreateFacet.parse_obj(data).facet_create

    async def create_class(self, input: ClassCreateInput) -> CreateClassClassCreate:
        query = gql("""
            mutation CreateClass($input: ClassCreateInput!) {
              class_create(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return CreateClass.parse_obj(data).class_create

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

    async def declare_event_listener(
        self, input: ListenerCreateInput
    ) -> DeclareEventListenerEventListenerDeclare:
        query = gql("""
            mutation DeclareEventListener($input: ListenerCreateInput!) {
              event_listener_declare(input: $input) {
                uuid
              }
            }
            """)
        variables: dict[str, object] = {"input": input}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return DeclareEventListener.parse_obj(data).event_listener_declare

    async def list_events(self, listener: UUID) -> ListEventsEvents:
        query = gql("""
            query ListEvents($listener: UUID!) {
              events(filter: {listeners: {uuids: [$listener]}}) {
                objects {
                  subject
                }
              }
            }
            """)
        variables: dict[str, object] = {"listener": listener}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return ListEvents.parse_obj(data).events

    async def fetch_event(self, listener: UUID) -> FetchEventEventFetch | None:
        query = gql("""
            query FetchEvent($listener: UUID!) {
              event_fetch(filter: {listener: $listener}) {
                token
                subject
              }
            }
            """)
        variables: dict[str, object] = {"listener": listener}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return FetchEvent.parse_obj(data).event_fetch

    async def acknowledge_event(self, token: Any) -> bool:
        query = gql("""
            mutation AcknowledgeEvent($token: EventToken!) {
              event_acknowledge(input: {token: $token})
            }
            """)
        variables: dict[str, object] = {"token": token}
        response = await self.execute(query=query, variables=variables)
        data = self.get_data(response)
        return AcknowledgeEvent.parse_obj(data).event_acknowledge

    async def get_org_unit_history(self, uuid: UUID) -> GetOrgUnitHistoryOrgUnits:
        query = gql("""
            query GetOrgUnitHistory($uuid: UUID!) {
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
        return GetOrgUnitHistory.parse_obj(data).org_units
