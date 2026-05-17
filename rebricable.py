import httpx
import time
import ssl
from urllib.parse import quote_plus

# Rebricable throttles requests more frequent than 1 second


def rate_limit(min_interval_seconds):
    last_called = [0.0]

    def decorator(func):
        def wrapper(*args, **kwargs):
            elapsed = time.monotonic() - last_called[0]
            wait_time = max(0, min_interval_seconds - elapsed)
            if wait_time > 0:
                time.sleep(wait_time)
            result = func(*args, **kwargs)
            last_called[0] = time.monotonic()
            return result
        return wrapper
    return decorator


def add_url(left, right):
    return left.rstrip('/') + '/' + right.lstrip('/')


class HttpProxy:
    def __init__(self, addr, cafile):
        self.addr = addr
        self.cafile = cafile


class Client:
    def __init__(self, rebricable_config: dict, http_proxy=None):
        self.__api_key = rebricable_config.get("api_key")
        self.__headers = {
            'Accept': 'application/json',
            'Authorization': f'key {self.__api_key}'
        }
        self._base_url = rebricable_config.get("base_url")
        if http_proxy:
            ctx = ssl.create_default_context(cafile=http_proxy.cafile)
            proxy = http_proxy.addr
        else:
            proxy = None
        # Create a reusable HTTP/2 client
        self.__client = httpx.Client(
            http2=True,
            verify=False,
            headers=self.__headers,
            proxy=proxy
        )
        # self.__client._transport._pool._proxy = httpx.Proxy("http://localhost:8080")
        # Shared throttled request method
        self.__throttled_request = rate_limit(1.0)(self.__request)

    def __request(self, method, endpoint, **kwargs):
        url = add_url(self._base_url, endpoint)
        return self.__client.request(method, url, **kwargs)

    def get_fetch_json(self, endpoint: str, form_data=None, json_data=None, params=None):
        try:
            response = self.__throttled_request(
                "GET", endpoint,
                params=params,
                data=form_data,
                json=json_data
            )
            response.raise_for_status()
            return response.json(), None
        except httpx.RequestError as e:
            return None, f"Request failed: {e}"
        except ValueError:
            return None, "Response was not valid JSON"

    def post_fetch_json(self, endpoint, form_data=None, json_data=None, params=None):
        headers = self.__headers.copy()
        if form_data:
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        try:
            response = self.__throttled_request(
                "POST", endpoint,
                headers=headers,
                params=params,
                data=form_data,
                json=json_data,
            )
            response.raise_for_status()
            return response.json(), None
        except httpx.RequestError as e:
            return None, f"Request failed: {e}"
        except ValueError:
            return None, "Response was not valid JSON"


def test_rate_limiter(client, endpoint):

    for i in range(5):
        start_ms = int(time.monotonic() * 1000)
        data, error = client.get_fetch_json(endpoint)
        end_ms = int(time.monotonic() * 1000)

        print(f"[{i+1}] Time: {end_ms} ms. Duration {end_ms-start_ms} ms.")
        if error:
            print(f"    Error: {error}")
        else:
            print(f"    Success: Received {len(data)} keys")


class User:
    def __init__(self, client: Client, rebricable_config: dict):
        self.__client = client

        name = rebricable_config.get("user", {}).get("login")
        passwd = rebricable_config.get("user", {}).get("passwd")
        if name is not None and passwd is not None:
            passwd = quote_plus(passwd)
            name = quote_plus(name)
            self.__login_form = f"username={name}&password={passwd}"
        else:
            self.__login_form = None
        self.__user_token = None

    def log_in(self):
        res, error = self.__client.post_fetch_json(
            "users/_token/", form_data=self.__login_form)
        if error:
            print(f"log in error: {error}")
            return None
        self.__user_token = res["user_token"]
        if self.__user_token:
            self._user_url = f"users/{self.__user_token}"
        return self.__user_token

    def get_fetch_json(self, endpoint: str, form_data=None, json_data=None, params=None):
        endpoint = add_url(self._user_url, endpoint)
        return self.__client.get_fetch_json(endpoint, form_data, json_data, params)


class LostParts:
    # init with result of GET lost_parts/
    def __init__(self, obj):
        self.obj = obj

    # get simple list of {part_num, color_id, lego_id, quantity}
    # part_num is part identifier independent of color (used by rebricable)
    # lego_id identifies part type and color combined (used in lego shop)
    def to_part_list(self):
        ret = []

        for result in self.obj["results"]:
            # each result is number of brick in given color
            # if there are more of the same parts lost but various colors,
            # each color is in separate result
            ret.append({
                "part_num": result["inv_part"]["part"]["part_num"],
                "color_id": result["inv_part"]["color"]["id"],
                "lego_id" : result["inv_part"]["color"]["element_id"],
                "quantity": result["inv_part"]["lost_quantity"]
            })
        return ret

    def to_set_list(self):
        ret = set()

        for result in self.obj["results"]:
            set_id = result["inv_part"]["set_num"]
            set_and_subset = set_id.split('-', 1)
            if len(set_and_subset) == 1:
                set_and_subset.append("")
            # splits <set_num>-<subset-num>
            # or to fig-<fig_num> in case of figurines
            ret.add((set_and_subset[0], set_and_subset[1]))
        return ret
