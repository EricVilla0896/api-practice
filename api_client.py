import requests, os
from database import get_connection


def external_request(id):
    try:
        req = requests.get(f"https://jsonplaceholder.typicode.com/users/{id}", timeout=5)
    except requests.exceptions.RequestException as e:
        return {"success": False,
                "error": str(e),
                "status": None}
    status = req.status_code
    if status != 200:
        return {"success": False,
                "error": "API request failed",
                "status": status}
    json_data = req.json()
    requests_dict = {
        "name": json_data["name"],
        "email": json_data["email"],
        "company": {
            "name": json_data["company"]["name"],
        }
    }
    return {"success": True,
            "data": requests_dict,
            "status": status}


def search_user(id):
    headers = {
        "Accept": "application/json"
    }
    try:
        req = requests.get(
            "https://jsonplaceholder.typicode.com/users",
            params={"id": id},
            headers=headers,
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        return {"success": False,
                "error": str(e),
                "status": None}
    user_data = req.json()
    if not user_data:
        return {"success": False,
                "error": "User not found",
                "status": 404}
    user = user_data[0]
    return {
        "success": True,
        "data": user,
        "status": 200
    }


def create_post(title, body, user_id):
    headers = {
        "Accept": "application/json",
        "api_key": os.getenv("OPENFDA_API_KEY")
    }
    data = {
        "title": title,
        "body": body,
        "userId": user_id,
        "api_key": os.getenv("OPENFDA_API_KEY")
    }
    try:
        pos = requests.post(
            "https://jsonplaceholder.typicode.com/posts",
            json=data,
            timeout=5,
            headers=headers
        )
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status": None
        }
    status = pos.status_code
    if status != 201:
        return {
            "success": False,
            "error": "Failed to create post",
            "status": status
        }
    return {
        "success": True,
        "data": pos.json(),
        "status": status
    }


def search_drug(product_name):
    try:
        search_response = requests.get(
            "https://api.fda.gov/drug/event.json",
            timeout=5,
            params={
                "api_key": os.getenv("OPENFDA_API_KEY"),
                "search": product_name
            }
        )

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status": None
        }
    status = search_response.status_code
    if status != 200:
        return {
            "success": False,
            "error": "Failed to search for product",
            "status": status
        }
    search_data = search_response.json()
    if not search_data["results"]:
        return {
            "success": False,
            "error": "No results found",
            "status": status
        }
    data = search_data["results"][0]
    severity = data.get("serious")
    if not data["patient"]["drug"]:
        return {
            "success": False,
            "error": "No suspect cause found",
            "status": status
        }
    cause_data = data["patient"]["drug"][0]
    suspect_cause = cause_data.get("medicinalproduct")
    if not data["patient"]["reaction"]:
        return {
            "success": False,
            "error": "No medical reaction found",
            "status": status
        }
    reaction_data = data["patient"]["reaction"][0]
    reaction = reaction_data.get("reactionmeddrapt")
    save_data = save_drug_search(product_name, suspect_cause, reaction, severity)
    if not save_data["success"]:
        return {
            "success": False,
            "error": save_data["error"],
            "status": 502
        }
    return {
        "success": True,
        "data": {
            "id": save_data["id"],
            "product_name": product_name,
            "suspect_cause": suspect_cause,
            "effect": reaction,
            "severity": "Serious" if severity == "1" else "Non-serious" if severity == "2" else "Unknown"
        },
        "status": status
    }

def save_drug_search(product_name, suspect_cause, reaction, severity):
    id = None
    try:
        with (get_connection() as connection):
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT into api_practice_schema.drug_searches
                    (
                        product_name, 
                        suspect_cause, 
                        effect, 
                        severity
                    ) 
                VALUES (%s, %s, %s, %s)
                returning id;
                """,
                (product_name, suspect_cause, reaction, severity)
            )
            saved_id = cursor.fetchone()
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": 502
        }
    return {
        "success": True,
        "id": saved_id[0],
    }


search = search_drug("aspirin")