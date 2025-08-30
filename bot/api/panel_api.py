from typing import List, Dict, Union, Optional
import requests
from dataclasses import dataclass

@dataclass
class Service:
    service: int
    name: str
    type: str
    category: str
    rate: str
    min: str
    max: str
    refill: bool
    cancel: bool

class PanelAPI:
    """Client for interacting with JustAnotherPanel API"""
    
    BASE_URL = "https://justanotherpanel.com/api/v2"

    def __init__(self, api_key: str):
        """Initialize the API client with the API key"""
        self.api_key = api_key
        self.session = requests.Session()

    def _make_request(self, action: str, **params) -> dict:
        """Make a request to the API with the given action and parameters"""
        data = {
            "key": self.api_key,
            "action": action,
            **params
        }
        
        response = self.session.post(self.BASE_URL, json=data)
        response.raise_for_status()
        return response.json()

    def get_services(self) -> List[Service]:
        """Get list of available services"""
        response = self._make_request("services")
        return [Service(**service) for service in response]

    def add_order(
        self,
        service: int,
        link: str,
        quantity: int,
        runs: Optional[int] = None,
        interval: Optional[int] = None
    ) -> Dict[str, int]:
        """Add a new order"""
        params = {
            "service": service,
            "link": link,
            "quantity": quantity
        }
        
        if runs is not None:
            params["runs"] = runs
        if interval is not None:
            params["interval"] = interval

        return self._make_request("add", **params)

    def get_order_status(self, order_id: int) -> dict:
        """Get status of a single order"""
        return self._make_request("status", order=order_id)

    def get_multiple_order_status(self, order_ids: List[int]) -> dict:
        """Get status of multiple orders"""
        orders = ",".join(str(order_id) for order_id in order_ids)
        return self._make_request("status", orders=orders)

    def create_refill(self, order_id: int) -> Dict[str, int]:
        """Create a refill for an order"""
        return self._make_request("refill", order=order_id)

    def create_multiple_refills(self, order_ids: List[int]) -> List[dict]:
        """Create refills for multiple orders"""
        orders = ",".join(str(order_id) for order_id in order_ids)
        return self._make_request("refill", orders=orders)

    def get_refill_status(self, refill_id: int) -> dict:
        """Get status of a single refill"""
        return self._make_request("refill_status", refill=refill_id)

    def get_multiple_refill_status(self, refill_ids: List[int]) -> List[dict]:
        """Get status of multiple refills"""
        refills = ",".join(str(refill_id) for refill_id in refill_ids)
        return self._make_request("refill_status", refills=refills)

    def cancel_orders(self, order_ids: List[int]) -> List[dict]:
        """Cancel multiple orders"""
        orders = ",".join(str(order_id) for order_id in order_ids)
        return self._make_request("cancel", orders=orders)

    def get_balance(self) -> dict:
        """Get user balance"""
        return self._make_request("balance")
