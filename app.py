import requests
from flask import Flask, jsonify, request, redirect, session
from database import get_connection
import os
from dotenv import load_dotenv
from functools import wraps
from psycopg.errors import UniqueViolation
from api_client import external_request, search_user, create_post, search_drug
from urllib.parse import urlencode
import secrets

load_dotenv()

app = Flask(__name__)
flask_secret_key = os.getenv("FLASK_SECRET_KEY")
if not flask_secret_key:
    flask_secret_key = os.getenv("FLASK_SECRET_KEY")
app.secret_key = flask_secret_key

def authenticate_api():
    request_key=request.headers.get("X-API-Key")
    if not request_key or request_key != os.getenv("API_KEY"):
        return False
    return True

def authenticate_api_request():
    request_external_key=request.headers.get("X-API-Key")
    if not request_external_key or request_external_key != os.getenv("EXTERNAL_API_KEY"):
        return False
    return True

# @app.before_request
# def check_authentication():
#     if request.path != "/health" and not authenticate():
#             return jsonify({"error": "Authentication failed"}), 401

def require_api_key(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if not authenticate_api():
            return jsonify({"error": "Authentication failed"}), 401
        return route_function(*args, **kwargs)
    return wrapper
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

def validate_field(field,value):
    if field not in ["company", "position", "salary"]:
        return f"Invalid field: {field}"
    if field == "company":
        if not isinstance(value, str):
            return "Field 'company' must be a string"
        if value.strip() == "":
            return "Field 'company' cannot be blank"
    elif field == "position":
        if not isinstance(value, str):
            return "Field 'position' must be a string"
        if value.strip() == "":
            return "Field 'position' cannot be blank"
    elif field == "salary":
        if not isinstance(value, int):
            return "Field 'salary' must be an integer"
        if value < 50000 or value > 100000:
            return "Field 'salary' must be between 50000 and 100000"
    return None

def validate_field_post(field,value):
    if field not in ["title", "body", "user_id"]:
        return f"Invalid field: {field}"
    if field == "title":
        if not isinstance(value, str):
            return "Field 'title' must be a string"
        if value.strip() == "":
            return "Field 'title' cannot be blank"
    elif field == "body":
        if not isinstance(value, str):
            return "Field 'body' must be a string"
        if value.strip() == "":
            return "Field 'body' cannot be blank"
    elif field == "user_id":
        if not isinstance(value, int):
            return "Field 'user_id' must be an integer"
    return None

def authenticate_webhook():
    request_webhook_key=request.headers.get("X-Webhook-secret")
    if not request_webhook_key or request_webhook_key != os.getenv("WEBHOOK_SECRET"):
        return False
    return True

@app.route('/webhook', methods=['POST'])
def webhook():
    is_authenticated = authenticate_webhook()
    if not is_authenticated:
        return jsonify({"error": "Wrong Webhook secret"}), 401
    json_data = request.get_json()
    if not json_data or "event_id" not in json_data or "event" not in json_data or "company" not in json_data or "position" not in json_data or "salary" not in json_data:
        return jsonify({"error": "Missing required fields"}), 400
    if json_data["event"] not in ["application.created", "application.updated", "application.deleted"]:
        return jsonify({"error": "Invalid event"}), 400
    if json_data["event"] == "application.created":
        try:
            for key in ["company", "position", "salary"]:
                error = validate_field(key, json_data[key])
                if error:
                    return jsonify({"error": error}), 400
            with get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(
                    """
                    INSERT into api_practice_schema.applications
                    (company,
                     position,
                     salary)
                    VALUES (%s, %s, %s)
                    """,
                    (json_data["company"], json_data["position"], json_data["salary"])
                )
                cursor.execute(
                    """
                    INSERT into api_practice_schema.webhook_events
                    (event_id)
                    VALUES (%s)
                    """,
                    (json_data["event_id"],)
                )
        except UniqueViolation:
            return jsonify({"error": "Webhook event already processed"}), 409
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"message": "Application created"}), 200
    if json_data["event"] == "application.updated":
        return jsonify({"message": "Application updated"}), 200
    if json_data["event"] == "application.deleted":
        return jsonify({"message": "Application deleted"}), 200

@app.route('/applications', methods=['POST'])
@require_api_key
def create_application():
    json_data = request.get_json()
    if not json_data or "company" not in json_data or "position" not in json_data or "salary" not in json_data:
        return jsonify({"error": "Missing required fields"}), 400
    for key,value in json_data.items():
        error=validate_field(key,value)
        if error:
            return jsonify({"error": error}), 400
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT into api_practice_schema.applications
                (
                    company,
                    position,
                    salary
                )
                VALUES (%s,%s,%s)
                RETURNING id
                """,
                (json_data["company"], json_data["position"], json_data["salary"])
            )
            result = cursor.fetchone()
            new_id = result[0]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({
        "id": abc
    })

@app.route('/applications', methods=['GET'])
@require_api_key
def applications():
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT * 
                FROM api_practice_schema.applications
                """,
            )
            rows = cursor.fetchall()
            applications_dict = [
                {
                    "id": row[0],
                    "company": row[1],
                    "position": row[2],
                    "salary": row[3],
                    "status": row[4]
                }
                for row in rows
            ]
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"applications": applications_dict})

@app.route('/applications/<id>', methods=['GET'])
def get_application(id):
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT * FROM api_practice_schema.applications WHERE id=%s
                """,
                (id,)
            )
            row = cursor.fetchone()
            if row is None:
                return jsonify({"error": "Application not found"}), 404
            applications_dict = {
                "id": row[0],
                "company": row[1],
                "position": row[2],
                "salary": row[3]
            }
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify(applications_dict)

@app.route('/applications/<id>', methods=['DELETE'])
def delete_application(id):
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                DELETE FROM api_practice_schema.applications WHERE id=%s
                """,
                (id,)
            )
            if cursor.rowcount != 1:
                return jsonify({"error": "Application not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Application deleted"})

@app.route('/applications/<id>', methods=['PUT'])
def update_application(id):
    json_data = request.get_json()
    if not json_data or "company" not in json_data or "position" not in json_data or "salary" not in json_data:
        return jsonify({"error": "Missing required fields"}), 400
    for key, value in json_data.items():
        error = validate_field(key, value)
        if error:
            return jsonify({"error": error}), 400
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE api_practice_schema.applications 
                set company=%s,
                position=%s,
                salary=%s
                WHERE id=%s
                """,
                (json_data["company"], json_data["position"], json_data["salary"], id)
            )
            if cursor.rowcount != 1:
                return jsonify({"error": "Application not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Application updated"})

@app.route('/applications/<id>', methods=['PATCH'])
def patch_application(id):
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Missing required fields to update"}), 400
    for key, value in json_data.items():
        error = validate_field(key, value)
        if error:
            return jsonify({"error": error}), 400
    values = []
    updates = []
    for field, value in json_data.items():
        updates.append(f"{field}=%s")
        values.append(value)
    clause = ",".join(updates)
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"""
                UPDATE api_practice_schema.applications 
                set {clause}
                WHERE id=%s
                """,
                values + [id]
            )
            if cursor.rowcount != 1:
                return jsonify({"error": "Application not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Application patched"})

@app.route('/applications/<id>/status', methods=['PATCH'])
def patch_status(id):
    is_authenticated = authenticate_webhook()
    if not is_authenticated:
        return jsonify({"error": "Wrong Webhook secret"}), 401
    json_data = request.get_json()
    print(json_data.get("status"))
    if not json_data or json_data.get("status") != "qualified":
        return jsonify({"error": "Application not qualified"}), 400
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE api_practice_schema.applications
                set status=%s
                WHERE id=%s
                """,
                (json_data["status"], id)
            )
            if cursor.rowcount == 0:
                return jsonify({"error": "Application not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"message": "Application status updated"}), 200

@app.route('/external-user/<int:id>', methods=['GET'])
def get_users(id):
    data = external_request(id)
    return jsonify(data), data["status"]

@app.route('/external-user', methods=['GET'])
def search_external_users():
    user_id = request.args.get("id")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return jsonify({"error": "User ID required"}), 400
    user_data = search_user(user_id)
    return jsonify(user_data), user_data["status"]

@app.route('/external-post', methods=['POST'])
def post_external_user():
    is_authenticated = authenticate_api_request()
    if not is_authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    json_data = request.get_json()
    if not json_data or "title" not in json_data or "body" not in json_data or "user_id" not in json_data:
        return jsonify({"error": "Missing required fields"}), 400
    for key in ["title", "body", "user_id"]:
        error = validate_field_post(key, json_data[key])
        if error:
            return jsonify({"error": error}), 400
    post = create_post(json_data["title"], json_data["body"], json_data["user_id"])
    if not post["success"]:
        return jsonify(post), 502
    return jsonify(post), post["status"]


@app.route('/oauth/login')
def github_login():
    state = secrets.token_urlsafe(16)
    session["state"] = state
    params = {
        "client_id": os.getenv("GITHUB_CLIENT_ID"),
        "redirect_uri": "http://127.0.0.1:5000/oauth/callback",
        "scope": "read:user",
        "state": state,
    }
    auth_url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    return redirect(auth_url)

@app.route('/oauth/callback')
def github_callback():
    state = request.args.get("state")
    expected_state = session.get("state")
    if state != expected_state:
        return jsonify({"error": "Invalid state"}), 400
    session.pop("state", None)
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization code missing"}), 400
    try:
        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data = {
                "client_id": os.getenv("GITHUB_CLIENT_ID"),
                "client_secret": os.getenv("GITHUB_CLIENT_SECRET"),
                "code": code,
                "redirect_uri": "http://127.0.0.1:5000/oauth/callback"
            },
            headers={"Accept": "application/json"},
            timeout=5
        )
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 502
    token_data = token_response.json()
    if "access_token" not in token_data:
        return jsonify({"error": "Token exchange failed"}), 400
    access_token = token_data["access_token"]
    github_response = requests.get(
        "https://api.github.com/user",
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        },
        timeout=5
    )
    status = github_response.status_code
    if status != 200:
        return jsonify({
            "error": "Github API request failed",
            "status": status
        }), 502
    github_user = github_response.json()
    return jsonify({
        "success": True,
        "user": github_user
    }), status


@app.route('/external-drug', methods=['GET'])
def get_fda_drugs():
    drug_name = request.args.get("product")
    if not drug_name:
        return jsonify({"error": "Drug product required"}), 400
    search_results = search_drug(drug_name)
    if not search_results["success"]:
        return jsonify(search_results), 502
    return jsonify(search_results), search_results["status"]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
