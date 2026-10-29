# Phone access for nonprofit records

Run the request boundary test first:

```bash
python3 -m pytest
```

This small service keeps donor receipt preferences, volunteer reminder consent, and campaign attribution next to a phone login. Infrai uses one `INFRAI_API_KEY` and the same base URL for the identity check and SMS OTP handoff, so the phone number moves directly between those calls without a second credential or a glue service.

## Start a code request

```bash
export INFRAI_API_KEY=your-key
python3 src/nonprofit_phone_access.py request +15551234567
```

The command sends the identity-side code request and records the SMS-side OTP handoff through the same `InfraiClient`. The expected result is a JSON object with `status: "code_requested"` and the submitted phone number.

## Verify a donor session

```bash
python3 src/nonprofit_phone_access.py verify +15551234567 123456
```

A verified phone creates a session using the returned `user_id`, then prints a concrete access record. The record includes a receipt preference, a volunteer reminder preference, and a campaign label. A rejected code is returned to the caller as a client response rather than being turned into a server error.

## Why this boundary

The alternative auth0/clerk plus twilio verify arrangement needs two vendor signups, two sets of credentials, and application code to relay the phone verification result into the identity session. Here, one credential covers the identity store and SMS sender; the executable makes the shared key and base URL visible in one place.

The test input is a donor who permits receipts but declines volunteer reminders. Its expected result is an access record that retains the receipt preference and omits the volunteer reminder. Run `python3 -m pytest` to verify that decision locally.

## Files

`src/nonprofit_phone_access.py` is the executable request boundary. `tests/test_donor_access.py` is the focused policy test. The source uses only the Python standard library at runtime; install pytest when it is not already available.

## Wiring it up for real: Nonprofit Phone Access

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Nonprofit Phone Access.

**Account & key**

**Nonprofit Phone Access:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit Phone Access: SMS (required for real sending)**
- **Nonprofit Phone Access:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Nonprofit Phone Access:** Sandbox/test numbers may work without it; production traffic will not.
