"""Helper functions for calling the business simulator games
"""

from argparse import Action
import requests
import ast
import json
from dataclasses import dataclass

@dataclass
class ParkResponse:
    status_code: int
    message: str
    data: dict
    error: bool

def _handle_response(response) -> ParkResponse:
    if response.status_code == 404:
        raise ValueError(f"Endpoint not found: {response.url}\n full response: {response}")
    if response.status_code not in [200, 400, 500]:
        print(response)
        print(f"Unexpected response: {response.json()}")
        data = response.json()
        message = f"Unexpected status code: {response.status_code}"
    else:
        try:
            message, data = response.json()["message"], response.json()["data"]
        except json.JSONDecodeError:
            print("Server error, did not get message or data:")
            print(response)
            import traceback
            print(traceback.format_exc())
            raise 
    return ParkResponse(status_code=response.status_code, message=message, data=data, error=response.status_code != 200)

def create_url(host: str, port: str, endpoint: str) -> str:
    """Create a URL from the given host, port, and endpoint.

    Args:
        host: The host name or IP address.
        port: The port number.
        endpoint: The API endpoint.

    Returns:
        A formatted URL string.
    """
    return "http://{0}:{1}/v1/{2}".format(host, port, endpoint)

def get_endpoint(host: str, port: str, endpoint: str, params: dict, session = None) -> ParkResponse:
    """Send a GET request for a specified endpoint.

    Args:
        host: The host of the API.
        port: The port of the API.
        endpoint: The specific endpoint to call.
        params: The parameters to include in the GET request.

    Returns:
        The JSON response from the API as a ParkResponse.
    """
    if(session is None):
        session = requests

    response = session.get(create_url(host, port, endpoint), params = params)
    return _handle_response(response)


def put_endpoint(host: str, port: str, endpoint: str, data: dict, session = None) -> ParkResponse:
    """Send a PUT request to a specified endpoint.

    Args:
        host: The host of the endpoint.
        port: The port of the endpoint.
        endpoint: The specific endpoint to send the request to.
        data: The data to be sent in the PUT request, which must include 'x' and 'y' keys.

    Returns:
        The JSON response from the server as a ParkResponse.
    """
    try:
        x = data.pop('x')
        y = data.pop('y')
    except KeyError:
        return ParkResponse(status_code=400, message=f"Modification actions require 'x' and 'y' as keyword arguments", data={}, error=True)
    if(session is None):
        session = requests
    r = session.put(create_url(host, port, endpoint + "/{0}/{1}".format(x, y)), json = data)
    return _handle_response(r)


def post_endpoint(host: str, port: str, endpoint: str, data: dict, session = None) -> ParkResponse:
    """Send a POST request to a specified endpoint.

    Args:
        host: The host of the endpoint.
        port: The port of the endpoint.
        endpoint: The specific endpoint to send the request to.
        data: The data to be sent in the POST request.

    Returns:
        The JSON response from the server as a ParkResponse.
    """
    if(session is None):
        session = requests
    
    r = session.post(create_url(host, port, endpoint), json = data)
    return _handle_response(r)

def delete_endpoint(host: str, port: str, endpoint: str, data: dict, session = None) -> ParkResponse:
    """Send a DELETE request to a specific endpoint.

    Args:
        host: The host of the endpoint.
        port: The port of the endpoint.
        endpoint: The specific endpoint.
        data: A dictionary containing data for the delete request, must include an 'id' key.

    Returns:
        The JSON response from the delete request as a ParkResponse.
    """
    try:
        x, y = data.pop('x'), data.pop('y')
    except KeyError:
        return ParkResponse(status_code=400, message=f"Deletion actions require 'x' and 'y' as keyword arguments", data={}, error=True)
    if session is None:
        session = requests
    r = session.request(method = "delete", url = create_url(host, port, endpoint + "/{0}/{1}".format(x, y)), json = data)
    return _handle_response(r)

def delete_park_endpoint(host: str, port: str, park_id: str, session = None) -> ParkResponse:
    """Delete a park.
    """
    if session is None:
        session = requests
    r = session.request(method = "delete", url = create_url(host, port, "park/delete_park/{0}".format(park_id)))
    return _handle_response(r)

def _get_raw_value(arg):
    if(isinstance(arg, ast.Constant)):
        return arg.value 
    elif(isinstance(arg, ast.List)):
        return [
            _get_raw_value(x) for x in arg.elts
        ]
    elif(isinstance(arg, ast.Dict)):
        return {
            _get_raw_value(key) : _get_raw_value(value) for key,value in zip(arg.keys, arg.values)
        }
    elif(isinstance(arg, ast.UnaryOp)):
        if(isinstance(arg.op, ast.USub)):
            return -1 * int(arg.operand.value)
    return None

def get_action_name_and_args(action: str) -> tuple[str, dict]:
    """
    Get the action name and arguments from a string.
    action is a string of the form of a python function call, e.g. "action_name(arg1=value1, arg2=value2, ...)"

    Args:
        action: The action string.

    Returns:
        A tuple containing the action name and arguments.
    """
    action_tree = ast.parse(action)
    action_name = action_tree.body[0].value.func.id
    action_args = {x.arg : _get_raw_value(x.value) for x in action_tree.body[0].value.keywords}
    return action_name, action_args