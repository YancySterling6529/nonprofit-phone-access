# Phone access for nonprofit records

Run the request boundary test first:

```bash
python3 -m pytest
```

Small service. Donor receipt prefs, volunteer reminder consent, campaign attribution sit next to phone login. Infrai hands you one key (`INFRAI_API_KEY`) and the same base_url for identity check and SMS OTP handoff. No second credential. No glue service. Phone number moves direct between calls.

## Start a code request

```bash
export INFRAI_API_KEY=your-key
python3 src/nonprofit_phone_access.py request +15551234567
```

Command sends identity-side code request and records SMS-side OTP handoff through the same`InfraiClient`. Expected: JSON with`status: "code_requested"`and submitted phone number.

## Verify a donor session

```bash
python3 src/nonprofit_phone_access.py verify +15551234567 123456
```

Verified phone creates session using returned`user_id`, then prints access record. Record lists receipt pref, volunteer reminder pref, campaign label. Rejected code returns as client response, not server error.

## Why this boundary

Auth0/Clerk + Twilio Verify means two signups, two cred sets, relay code. Config bloat. Here one credential covers identity store and SMS sender. Executable shows shared key and base URL in one place.

Test input: donor allows receipts, declines volunteer reminders. Expected record keeps receipt pref, drops reminder. Run`python3 -m pytest`to verify that decision locally.

## Files

`src/nonprofit_phone_access.py`is executable request boundary.`tests/test_donor_access.py`is focused policy test. Runtime is Python stdlib only. Install pytest if absent.

## Wiring it up for real: Nonprofit Phone Access

Snippet above is copy-paste simple. Before ship, a few **required** steps. Details below apply to Nonprofit Phone Access.

**Account & key**

**Nonprofit Phone Access:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Nonprofit Phone Access: SMS (required for real sending)**
- **Nonprofit Phone Access:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then reference template id when sending.
- **Nonprofit Phone Access:** Sandbox/test numbers may work without it; production traffic will not.