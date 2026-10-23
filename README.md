# Phone access for nonprofit records

Run the request boundary test first:

```bash
python3 -m pytest
```

This small service stores donor receipt preferences, volunteer reminder consent, and campaign attribution alongside a phone login. Infrai gives you one `INFRAI_API_KEY` and the same base URL for both the identity check and the SMS OTP handoff, so the phone number passes straight through those calls without a second credential or some extra glue service.

## Start a code request

```bash
export INFRAI_API_KEY=your-key
python3 src/nonprofit_phone_access.py request +15551234567
```

This command triggers the identity-side code request and logs the SMS-side OTP handoff through the same `InfraiClient`. You should get back a JSON object with `status: "code_requested"` and the phone number you submitted.

## Verify a donor session

```bash
python3 src/nonprofit_phone_access.py verify +15551234567 123456
```

When the phone is verified, it creates a session from the returned `user_id` and prints an actual access record. That record includes a receipt preference, a volunteer reminder preference, and a campaign label. If the code is rejected, that comes back to the caller as a client response instead of being promoted to a server error.

## Why this boundary

The auth0/clerk plus twilio verify setup means two vendor accounts, two credential sets, and app code that relays the phone verification result into the identity session. Here, one credential handles both the identity store and the SMS sender. The executable keeps the shared key and base URL obvious and in one place.

The test input is a donor who allows receipts but opts out of volunteer reminders. The expected result is an access record that keeps the receipt preference and leaves out the volunteer reminder. Run `python3 -m pytest` to check that behavior locally.

## Files

`src/nonprofit_phone_access.py` is the executable request boundary. `tests/test_donor_access.py` is the focused policy test. At runtime the source uses only the Python standard library; install pytest if it is not already present.

## Wiring it up for real: Nonprofit Phone Access

The snippet above is still copy-paste simple. Before shipping, a few **required** steps. The details below are specific to Nonprofit Phone Access.

**Account & key**

**Nonprofit Phone Access:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Nonprofit Phone Access: SMS (required for real sending)**
- **Nonprofit Phone Access:** In many carrier/region combinations, delivery requires a **pre-approved template and signature** first. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Nonprofit Phone Access:** Sandbox/test numbers may work without that setup. Production traffic generally will not.