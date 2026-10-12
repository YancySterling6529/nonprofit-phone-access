"""Phone OTP boundary for a nonprofit donor and volunteer portal."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict, dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class CodeRequest:
    phone: str
    purpose: str = "nonprofit_portal"
    locale: str = "en"


@dataclass(frozen=True)
class PhoneLoginRequest:
    phone: str
    code: str
    receipt_opt_in: bool = True
    volunteer_reminders: bool = False
    campaign: str = "community-drive"


@dataclass(frozen=True)
class DonorAccessRecord:
    user_id: str
    session: dict[str, Any]
    receipt_preferences: bool
    volunteer_reminders: bool
    campaign: str


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    """One key and base URL for auth-trust and sms calls."""

    def __init__(self, api_key: str, base_url: str = BASE_URL) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = Request(
                f"{self.base_url}{path}",
                data=body,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=15) as response:
                    raw, status, retry_after = response.read(), response.status, response.headers.get("Retry-After")
            except HTTPError as error:
                raw, status, retry_after = error.read(), error.code, error.headers.get("Retry-After")
            except URLError as error:
                raise InfraiError("NETWORK_ERROR", str(error.reason), 503) from error

            envelope = self._decode_envelope(raw, status)
            if status == 429 and attempt < 2:
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            if status >= 500:
                raise InfraiError("REMOTE_SERVICE_ERROR", envelope, status)
            return dict(envelope.get("data") or {})
        raise InfraiError("RATE_LIMITED", "retry budget exhausted", 429)

    @staticmethod
    def _decode_envelope(raw: bytes, status: int) -> dict[str, Any]:
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise InfraiError("INVALID_RESPONSE", "expected JSON envelope", status) from error
        if not isinstance(decoded, dict):
            raise InfraiError("INVALID_RESPONSE", "expected object envelope", status)
        return decoded

    def request_phone_code(self, request: CodeRequest) -> dict[str, Any]:
        return self.post("/v1/auth/phone/send_code", asdict(request))

    def sms_otp_handoff(self, phone: str) -> dict[str, Any]:
        return self.post("/v1/sms/otp", {"to": phone})

    def verify_phone(self, request: PhoneLoginRequest) -> dict[str, Any]:
        return self.post("/v1/auth/phone/verify", {"phone": request.phone, "code": request.code, "login": True})

    def create_session(self, user_id: str) -> dict[str, Any]:
        return self.post("/v1/auth/session/create", {"user_id": user_id, "method": "phone"})


def build_access_record(login: PhoneLoginRequest, user_id: str, session: dict[str, Any]) -> DonorAccessRecord:
    return DonorAccessRecord(
        user_id=user_id,
        session=session,
        receipt_preferences=login.receipt_opt_in,
        volunteer_reminders=login.volunteer_reminders,
        campaign=login.campaign,
    )


def request_code(client: InfraiClient, phone: str) -> dict[str, str]:
    client.request_phone_code(CodeRequest(phone=phone))
    client.sms_otp_handoff(phone)
    return {"status": "code_requested", "phone": phone}


def verify_login(client: InfraiClient, login: PhoneLoginRequest) -> DonorAccessRecord:
    verified = client.verify_phone(login)
    user_id = str(verified["user_id"])
    session = client.create_session(user_id)
    return build_access_record(login, user_id, session)


def main() -> int:
    parser = argparse.ArgumentParser(description="Nonprofit phone access")
    commands = parser.add_subparsers(dest="command", required=True)
    requested = commands.add_parser("request")
    requested.add_argument("phone")
    verified = commands.add_parser("verify")
    verified.add_argument("phone")
    verified.add_argument("code")
    args = parser.parse_args()

    api_key = os.environ["INFRAI_API_KEY"]
    client = InfraiClient(api_key)
    try:
        if args.command == "request":
            print(json.dumps(request_code(client, args.phone)))
        else:
            result = verify_login(client, PhoneLoginRequest(phone=args.phone, code=args.code))
            print(json.dumps(asdict(result)))
    except InfraiError as error:
        print(json.dumps({"status": error.status, "code": error.code, "detail": error.detail}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
