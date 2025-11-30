import os
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import string
from typing import List

import requests
from flask_jwt_extended import create_access_token
from main import app  # or however your Flask app is created


def _random_email() -> str:
	"""Generate a random email address."""

	username = "user" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
	domain = random.choice(["example.com", "test.com", "mail.com", "fake.org"])
	return f"{username}@{domain}"


def _random_uuid() -> str:
	"""Generate a random UUIDv4-like string using the uuid module."""

	import uuid

	return str(uuid.uuid4())


BASE_URL = "http://lb-devops-blacklist-app-1235064677.us-east-1.elb.amazonaws.com"


def stress_health_check(num_requests: int = 100) -> List[int]:
	"""Call `/blacklist/ping` `num_requests` times via real HTTP.

	Returns a list of HTTP status codes for basic inspection.
	"""

	statuses: List[int] = []
	for _ in range(num_requests):
		resp = requests.get(f"{BASE_URL}/blacklist/ping")
		statuses.append(resp.status_code)
	return statuses


def stress_add_blacklist(num_requests: int = 100, jwt_token: str = "test-token") -> List[int]:
	"""Call `POST /blacklist` `num_requests` times with fake payloads.

	The JWT token is injected as-is in the Authorization header; adjust it
	to a valid token in your environment if needed.
	"""

	statuses: List[int] = []

	headers = {
		"Authorization": f"Bearer {jwt_token}",
		"Content-Type": "application/json",
	}

	for _ in range(num_requests):
		payload = {
			"email": _random_email(),
			"app_uuid": _random_uuid(),
			"blocked_reason": random.choice(
				[
					"Spam activity",
					"User requested block",
					"Bounce detected",
					"Security incident",
				]
			),
		}
		resp = requests.post(f"{BASE_URL}/blacklist", json=payload, headers=headers)
		statuses.append(resp.status_code)
	return statuses


def stress_get_blacklist(num_requests: int = 100, jwt_token: str = "test-token") -> List[int]:
	"""Call `GET /blacklist/<email>` `num_requests` times with fake emails.

	Uses random email addresses; most will likely not exist, which is fine
	for stressing the endpoint itself.
	"""

	statuses: List[int] = []

	headers = {
		"Authorization": f"Bearer {jwt_token}",
	}

	for _ in range(num_requests):
		email = _random_email()
		resp = requests.get(f"{BASE_URL}/blacklist/{email}", headers=headers)
		statuses.append(resp.status_code)
	return statuses

def _generate_test_token() -> str:

	with app.app_context():
		return create_access_token(identity="test_user")



def run_sustained_stress(
    duration_minutes: int = 30,
    requests_per_minute: int = 10,
    jwt_token: str | None = None,
) -> None:
    """Run 10 requests every minute for the given duration.

    Uses the existing stress_* helpers to actually hit the endpoints.
    """

    if jwt_token is None:
        jwt_token = _generate_test_token()

    for minute in range(duration_minutes):
        print(f"\n=== Minute {minute + 1}/{duration_minutes} ===")

        jwt_token = _generate_test_token()

        # 10 health checks
        health_statuses = stress_health_check(num_requests=requests_per_minute)
        print("Health check statuses:", health_statuses)

        # 10 POSTs
        post_statuses = stress_add_blacklist(
            num_requests=requests_per_minute, jwt_token=jwt_token
        )
        print("POST /blacklist statuses:", post_statuses)

        # 10 GETs
        get_statuses = stress_get_blacklist(
            num_requests=requests_per_minute, jwt_token=jwt_token
        )
        print("GET /blacklist/<email> statuses:", get_statuses)

        # Sleep until next minute, except after the last iteration
        if minute < duration_minutes - 1:
            print("Sleeping 60 seconds before next batch...")
            time.sleep(60)


if __name__ == "__main__":
	# Generate a valid JWT inside the proper app context
	token = _generate_test_token()

	run_sustained_stress(duration_minutes=5, requests_per_minute=1000, jwt_token=token)
	# Example manual run; adjust jwt_token to a valid one if JWT is enforced.
	# print("Health check statuses:", stress_health_check())
	# print("POST /blacklist statuses:", stress_add_blacklist(jwt_token=token))
	# print("GET /blacklist/<email> statuses:", stress_get_blacklist(jwt_token=token))
