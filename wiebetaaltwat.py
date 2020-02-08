"""
Python wrapper for the WieBetaaltWat-API

"""
import json
import datetime
import requests


def to_euro(balance: float) -> str:
    """Format fractional to euro's"""
    if balance >= 0:
        return '€{:,.2f}'.format(balance)
    else:
        balance = balance * -1
        return '-€{:,.2f}'.format(balance)


class WieBetaaltWat(object):
    """Connect with WieBetaaltWat"""
    def __init__(self, email: str = None, password: str = None, cookie: str = None):
        assert email and password or cookie
        self.base_url = "https://api.wiebetaaltwat.nl"
        self.headers = {"Accept-Version": "2"}
        if not cookie:
            cookie = self._get_cookie(email, password)
        self.headers.update({"Cookie": cookie})

    def _get_cookie(self, email: str, password: str) -> str:
        """Log in and get a cookie"""
        url = f"{self.base_url}/api/users/sign_in"
        data = {"user": {"email": email,
                         "password": password}}
        req = self._post(url=url, data=data)
        return f"_wbw_rails_session={req.cookies.get('_wbw_rails_session')}"

    def _get(self, url: str) -> json:
        """Send a GET request to WBW"""
        req = requests.request('get', url, headers=self.headers)
        if req.status_code == 200:
            return json.loads(req.text)
        else:
            print(req.status_code)
            print(req.text)
            raise ConnectionError

    def _post(self, url: str, data: dict = None) -> requests:
        """Send a POST request to WBW"""
        formatted_data = str(data).replace("'", '"').replace("None", "null")
        headers = self.headers
        headers.update({'Content-Type': 'application/json;charset=UTF-8'})
        req = requests.request('post', url, data=formatted_data, headers=headers)
        if req.status_code == 201:
            return req
        else:
            print(req.status_code)
            print(req.text)
            raise ConnectionError

    def get_lists(self) -> dict:
        """Get wbw lists"""
        url = f"{self.base_url}/api/lists"
        json_value = self._get(url)
        result = {}
        for wbw_list in json_value['data']:
            result.update({wbw_list['list']['id']: {'name': wbw_list['list']['name']}})
        return result

    def get_list_by_name(self, name) -> str:
        """Get list ID by list name"""
        lists = self.get_lists()
        for key, value in lists.items():
            if value['name'].lower() == name.lower():
                return key

    def get_balance(self, list_id: str) -> dict:
        """Get balances from a list"""
        url = f"{self.base_url}/api/lists/{list_id}/balance"
        json_value = self._get(url)
        result = {}
        for member in json_value["balance"]["member_totals"]:
            result.update({member["member_total"]["member"]["id"]: {
                'balance': member["member_total"]["balance_total"]["fractional"] / 100,
                'nickname': member["member_total"]["member"]["nickname"]}})
        return result

    def get_balance_user(self, list_id: str, nickname: str = None, user_id=None) -> str:
        """Get balance by nickname or user_id in a list"""
        assert nickname or user_id, "Expected nickname or user_id, both were given"
        balance = self.get_balance(list_id)
        for key, value in balance.items():
            if nickname:
                if value["nickname"].lower() == nickname.lower():
                    return value["euro"]
            elif user_id:
                if key == user_id:
                    return value["euro"]

    def get_user_id_by_nickname(self, list_id: str, nickname: str) -> str:
        """Get user ID from list by nickname"""
        balance = self.get_balance(list_id)
        for key, value in balance.items():
            value_name = value.get("nickname")
            if value_name:
                if value_name.lower() == nickname.lower():
                    return key

    def get_nickname_by_user_id(self, list_id: str, user_id: str) -> str:
        balance = self.get_balance(list_id)
        for key, value in balance.items():
            if key == user_id:
                return value.get("nickname")

    def get_expenses(self, list_id: str) -> list:
        """Get expenses made from a list"""
        url = f"{self.base_url}/api/lists/{list_id}/expenses"
        json_value = self._get(url)
        result = []
        for expense in json_value["data"]:
            if expense["expense"]["status"] != "deleted":
                result.append({'description': expense["expense"]["name"],
                               'value': to_euro(expense["expense"]["amount"]["fractional"]),
                               })
        return result

    def add_expense(self, list_id: str, description: str, payer_id: str, share_ids: list, amount: float,
                    date: str = None):
        """Add an expense to a list"""
        url = f"{self.base_url}/api/lists/{list_id}/expenses"
        amount = int(amount * 100)
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")

        shares_attributes = []
        for share_id in share_ids:
            shares_attributes.append({"member_id": share_id, "amount": amount/len(share_ids), "multiplier": 1})
        data = {"expense": {"name": description, "payed_by_id": payer_id, "payed_on": date,
                            "amount": amount, "shares_attributes": shares_attributes}}
        return self._post(url, data=data)


def test():
    import redacted
    from pprint import pprint
    wbw = WieBetaaltWat(redacted.EMAIL, redacted.PASSWORD)
    lists = wbw.get_lists()

    for list_id in lists.keys():
        pprint(wbw.get_balance(list_id))


if __name__ == '__main__':
    test()
