"""Stress testing helpers for Blacklist API.

Each function below targets a specific endpoint and performs
100 requests using fake data appropriate for that endpoint.

These are not unit tests (no assertions) but utilities you can
run manually or wrap in formal tests/benchmarks.
"""
import os
import sys
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



if __name__ == "__main__":
	# Generate a valid JWT inside the proper app context
	token = _generate_test_token()

	# Example manual run; adjust jwt_token to a valid one if JWT is enforced.
	print("Health check statuses:", stress_health_check(num_requests=1000))
	print("POST /blacklist statuses:", stress_add_blacklist(jwt_token=token, num_requests=1000))
	print("GET /blacklist/<email> statuses:", stress_get_blacklist(jwt_token=token, num_requests=1000))
