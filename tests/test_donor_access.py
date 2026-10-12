import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from nonprofit_phone_access import PhoneLoginRequest, build_access_record


def test_receipt_permission_is_retained_when_volunteer_reminders_are_declined() -> None:
    login = PhoneLoginRequest(
        phone="+15551234567",
        code="123456",
        receipt_opt_in=True,
        volunteer_reminders=False,
        campaign="spring-clinic",
    )

    record = build_access_record(login, "donor-42", {"session_id": "session-42"})

    assert record.receipt_preferences is True
    assert record.volunteer_reminders is False
    assert record.campaign == "spring-clinic"
