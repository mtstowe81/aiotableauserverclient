from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

import aiohttp
import tableauserverclient as TSC

T = TypeVar("T")


class http:
    HTTP_HEADER_ACCEPT = "accept"
    HTTP_HEADER_CONTENT_TYPE = "content-type"
    HTTP_HEADER_CONTENT_JSON = "application/json"
    HTTP_HEADER_CONTENT_XML = "application/xml"


class TableauClientAsync():
    def __init__(self, url: str, username: str, password: str, site_id: str, api_ver: str):
        super().__init__()
        self.__tableau_auth_body = {
            "credentials": {
                "name": username,
                "password": password,
                "site": {"contentUrl": site_id},
            }
        }
        self.__tableau_auth_headers = {
            http.HTTP_HEADER_CONTENT_TYPE: http.HTTP_HEADER_CONTENT_JSON,
            http.HTTP_HEADER_ACCEPT: http.HTTP_HEADER_CONTENT_JSON,
        }
        self.__tableau_client = aiohttp.ClientSession(
            base_url=f"{url}",
            raise_for_status=True,
        )
        self.__api_ver = api_ver

    @property
    def subscriptions(self):
        return TableauSubscriptionsEndpointAsync(self)

    @property
    def users(self):
        return TableauUsersEndpointAsync(self)

    async def refresh_auth(self):
        response = await self.__tableau_client.post(
            self.__get_url("/auth/signin"),
            json=self.__tableau_auth_body,
            headers=self.__tableau_auth_headers,
        )
        self.__tableau_auth_response = await response.json()

    async def sign_in(self):
        await self.refresh_auth()

    async def close(self):
        await self.__tableau_client.close()

    async def get_request(self, url: str):
        return await self.__tableau_client.get(
            self.__get_site_url(url), headers=self.__get_headers()
        )

    async def delete_request(self, url: str):
        return await self.__tableau_client.delete(
            self.__get_site_url(url), headers=self.__get_headers()
        )

    async def post_request(self, url: str, body: str):
        return await self.__tableau_client.post(
            self.__get_site_url(url),
            headers=self.__get_headers(),
            data=body,
        )

    async def put_request(self, url: str, body: dict):
        return await self.__tableau_client.put(
            self.__get_site_url(url),
            headers=self.__get_headers(),
            data=body,
        )

    def __get_headers(self):
        return {
            "X-Tableau-Auth": self.__tableau_auth_response["credentials"]["token"],
            http.HTTP_HEADER_CONTENT_TYPE: http.HTTP_HEADER_CONTENT_XML,
            http.HTTP_HEADER_ACCEPT: http.HTTP_HEADER_CONTENT_XML,
        }

    def __get_site_url(self, url: str):
        return self.__get_url(
            f"/sites/{self.__tableau_auth_response['credentials']['site']['id']}{url}"
        )

    def __get_url(self, url: str):
        return f"/api/{self.__api_ver}{url}"


class BaseTableauEndpointAsync(ABC, Generic[T]):
    def __init__(self, tableau_client: TableauClientAsync, endpoint: str):
        super().__init__()
        self._tableau_client = tableau_client
        self._endpoint = endpoint
        self._namespace = {"t": "http://tableau.com/api"}

    @abstractmethod
    def _from_response(self, data: str) -> List[T]:
        pass

    @abstractmethod
    def _to_post_request(self, entity: T):
        pass

    @abstractmethod
    def _to_put_request(self, entity: T):
        pass

    @abstractmethod
    def _get_entity_id(self, entity: T) -> str:
        pass

    @abstractmethod
    def _apply_req_options(self, req: TSC.RequestOptions):
        pass

    async def get(self, req: TSC.RequestOptions) -> List[T]:
        self._apply_req_options(req)
        query = "&".join(
            [f"{k}={v}" for k, v in req.get_query_params().items()])
        response = await self._tableau_client.get_request(f"{self._endpoint}?{query}")
        return self._from_response(await response.text())

    async def get_by_id(self, id: str) -> T:
        response = await self._tableau_client.get_request(f"{self._endpoint}/{id}")
        return self._from_response(await response.text())[0]

    async def update(self, entity: T) -> T:
        response = await self._tableau_client.put_request(
            f"{self._endpoint}/{self._get_entity_id(entity)}",
            self._to_put_request(entity),
        )
        return self._from_response(await response.text())[0]


class TableauUsersEndpointAsync(BaseTableauEndpointAsync[TSC.UserItem]):
    def __init__(self, tableau_client: TableauClientAsync):
        super().__init__(tableau_client, "/users")

    def _apply_req_options(self, req: TSC.RequestOptions):
        req._all_fields = True

    def _get_entity_id(self, entity: TSC.UserItem) -> str:
        return entity.id

    def _from_response(self, data: str) -> List[TSC.UserItem]:
        return TSC.UserItem.from_response(data, self._namespace)

    def _to_post_request(self, entity) -> TSC.server.request_factory.UserRequest:
        return TSC.server.RequestFactory.User.add_req(entity)

    def _to_put_request(self, entity) -> TSC.server.request_factory.UserRequest:
        return TSC.server.RequestFactory.User.update_req(entity, password=None)

    async def remove(self, id: str) -> None:
        await self._tableau_client.delete_request(f"{self._endpoint}/{id}")

    async def add(self, user_item: TSC.UserItem) -> TSC.UserItem:
        response = await self._tableau_client.post_request(
            self._endpoint, self._to_post_request(user_item)
        )
        return self._from_response(await response.text())[0]


class TableauSubscriptionsEndpointAsync(BaseTableauEndpointAsync[TSC.SubscriptionItem]):
    def __init__(self, tableau_client: TableauClientAsync):
        super().__init__(tableau_client, "/subscriptions")

    def _apply_req_options(self, req: TSC.RequestOptions):
        pass  # Skip, nothing to do here

    def _get_entity_id(self, entity: TSC.SubscriptionItem) -> str:
        return entity.id

    def _from_response(self, data: str) -> List[TSC.SubscriptionItem]:
        return TSC.SubscriptionItem.from_response(data, self._namespace)

    def _to_post_request(
        self, entity
    ) -> TSC.server.request_factory.SubscriptionRequest:
        return TSC.server.RequestFactory.Subscription.create_req(entity)

    def _to_put_request(self, entity) -> TSC.server.request_factory.SubscriptionRequest:
        return TSC.server.RequestFactory.Subscription.update_req(entity)

    async def delete(self, id: str) -> None:
        await self._tableau_client.delete_request(f"{self._endpoint}/{id}")

    async def create(
        self, subscription_item: TSC.SubscriptionItem
    ) -> TSC.SubscriptionItem:
        response = await self._tableau_client.post_request(
            self._endpoint, self._to_post_request(subscription_item)
        )
        return self._from_response(await response.text())[0]
