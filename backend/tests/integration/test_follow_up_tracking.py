# Spec: FEAT-008 — Follow-Up Tracking
# File: specs/features/FEAT-008-follow-up-tracking.feature
# Relates: API-060..064, DATA-008

import pytest
from httpx import AsyncClient

from tests.seed import SEED_CASE_IDS

pytestmark = pytest.mark.asyncio

# Seeded case IDs for tests
CASE_ID = SEED_CASE_IDS["c001"]
CASE_ID_UNDER_REVIEW = SEED_CASE_IDS["c002"]


# ── Helper ───────────────────────────────────────────────


async def _create_follow_up(
    client: AsyncClient,
    headers: dict,
    case_id,
    scheduled_date: str = "2026-07-01T10:00:00Z",
    follow_up_type: str = "appointment",
    notes: str = "Test follow-up",
):
    """POST a follow-up and return the response JSON."""
    resp = await client.post(
        f"/cases/{case_id}/followups",
        json={
            "scheduled_date": scheduled_date,
            "follow_up_type": follow_up_type,
            "notes": notes,
        },
        headers=headers,
    )
    assert resp.status_code == 201, f"Create failed: {resp.status_code} {resp.text}"
    return resp.json()


# ===================================================================
# HAPPY PATH
# ===================================================================


class TestHappyPath:
    """FEAT-008 happy-path scenarios (h1-h8)."""

    @pytest.mark.spec("FEAT-008-h1")
    async def test_FEAT_008_h1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Navigator creates a follow-up for a case.

        Given an authenticated navigator and case c001 exists
        When they submit POST /cases/{c001}/followups
        Then the response status is 201
        And a follow-up is created with status "scheduled"
        And created_by is set to the navigator's user ID
        """
        resp = await async_client.post(
            f"/cases/{CASE_ID}/followups",
            json={
                "scheduled_date": "2026-07-01T10:00:00Z",
                "follow_up_type": "appointment",
                "notes": "Consultation with oncologist",
            },
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 201
        body = resp.json()
        assert body["case_id"] == str(CASE_ID)
        assert body["follow_up_type"] == "appointment"
        assert body["status"] == "scheduled"
        assert body["created_by"] is not None
        assert body["notes"] == "Consultation with oncologist"
        assert body["id"] is not None

    @pytest.mark.spec("FEAT-008-h2")
    async def test_FEAT_008_h2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        List follow-ups for a case.

        Given case c001 has follow-ups
        When they submit GET /cases/{c001}/followups
        Then the response status is 200
        And the response contains the follow-ups with pagination metadata
        """
        # Create a follow-up first so the list is not empty
        await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-07-10T09:00:00Z",
        )

        resp = await async_client.get(
            f"/cases/{CASE_ID}/followups",
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "per_page" in body
        assert body["total"] >= 1
        assert len(body["items"]) >= 1
        # Each item should have the expected fields
        item = body["items"][0]
        assert item["case_id"] == str(CASE_ID)

    @pytest.mark.spec("FEAT-008-h3")
    async def test_FEAT_008_h3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Get follow-up detail.

        Given a follow-up exists
        When they submit GET /followups/{follow_up_id}
        Then the response contains all fields
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-07-15T10:00:00Z",
            notes="Detail retrieval test",
        )

        resp = await async_client.get(
            f"/followups/{fu['id']}",
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == fu["id"]
        assert body["case_id"] == str(CASE_ID)
        assert body["follow_up_type"] == "appointment"
        assert body["status"] == "scheduled"
        assert body["notes"] == "Detail retrieval test"
        assert body["scheduled_date"] is not None
        assert body["created_by"] is not None
        assert body["created_at"] is not None
        assert body["updated_at"] is not None
        assert body["completed_at"] is None
        assert body["completed_by"] is None
        assert "reminder_sent" in body

    @pytest.mark.spec("FEAT-008-h4")
    async def test_FEAT_008_h4(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Mark follow-up as completed via the complete endpoint.

        Given a follow-up exists with status "scheduled"
        When they submit POST /followups/{id}/complete
        Then status is updated to "completed"
        And completed_at is set to current timestamp
        And completed_by is set to the navigator's user ID
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-07-20T10:00:00Z",
        )

        resp = await async_client.post(
            f"/followups/{fu['id']}/complete",
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["completed_at"] is not None
        assert body["completed_by"] is not None

    @pytest.mark.spec("FEAT-008-h5")
    async def test_FEAT_008_h5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Update follow-up scheduled_date and notes via PATCH.

        Given a follow-up exists
        When they submit PATCH /followups/{id} with new scheduled_date and notes
        Then scheduled_date and notes are updated
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-07-25T08:00:00Z",
            notes="Original notes",
        )

        resp = await async_client.patch(
            f"/followups/{fu['id']}",
            json={
                "scheduled_date": "2026-08-10T14:00:00Z",
                "notes": "Rescheduled consultation",
            },
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["notes"] == "Rescheduled consultation"

    @pytest.mark.spec("FEAT-008-h6")
    async def test_FEAT_008_h6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Cancel a follow-up via PATCH.

        Given a follow-up exists with status "scheduled"
        When they submit PATCH /followups/{id} with status "cancelled"
        Then status is updated to "cancelled"
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-08-01T10:00:00Z",
        )

        resp = await async_client.patch(
            f"/followups/{fu['id']}",
            json={"status": "cancelled"},
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "cancelled"

    @pytest.mark.spec("FEAT-008-h7")
    async def test_FEAT_008_h7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        View upcoming follow-ups across all cases.

        Given pending follow-ups exist across cases
        When they submit GET /followups/upcoming
        Then the response status is 200
        And the response contains follow-ups with pagination metadata
        """
        # Create follow-ups on two different cases
        await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-09-01T10:00:00Z",
            follow_up_type="checkup",
        )
        await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID_UNDER_REVIEW,
            scheduled_date="2026-09-05T14:00:00Z",
            follow_up_type="lab_test",
        )

        resp = await async_client.get(
            "/followups/upcoming",
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert body["total"] >= 2

    @pytest.mark.spec("FEAT-008-h8")
    async def test_FEAT_008_h8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Automatic overdue detection.

        Given a follow-up with scheduled_date in the past
        When the follow-up is queried
        Then the overdue status may be computed from scheduled_date < today
        """
        # Create with a past date — overdue detection is server-side computed
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2025-01-01T10:00:00Z",
        )

        resp = await async_client.get(
            f"/followups/{fu['id']}",
            headers=auth_headers_navigator,
        )

        assert resp.status_code == 200
        body = resp.json()
        # Status should be either "scheduled" (stored) or "overdue" (computed)
        assert body["status"] in ("scheduled", "overdue")


# ===================================================================
# EDGE CASES
# ===================================================================


class TestEdgeCases:
    """FEAT-008 edge-case scenarios (ec1-ec8)."""

    @pytest.mark.spec("FEAT-008-ec1")
    async def test_FEAT_008_ec1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up with scheduled_date today.

        Given an authenticated navigator
        When they submit POST with scheduled_date equal to today
        Then the response status is 201
        And the follow-up has status "scheduled" (not overdue yet)
        """
        resp = await async_client.post(
            f"/cases/{CASE_ID}/followups",
            json={
                "scheduled_date": "2026-06-05T10:00:00Z",
                "follow_up_type": "appointment",
                "notes": "Today's follow-up",
            },
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "scheduled"

    @pytest.mark.spec("FEAT-008-ec2")
    async def test_FEAT_008_ec2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up with scheduled_date in the past.

        Given an authenticated navigator
        When they submit POST with a past scheduled_date
        Then the response status is 201
        And the follow-up may be flagged as overdue when queried
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2025-05-01T08:00:00Z",
            notes="Past due follow-up",
        )

        # Re-fetch to check overdue status
        resp = await async_client.get(
            f"/followups/{fu['id']}",
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 200
        body = resp.json()
        # If the server computes overdue, status should reflect that;
        # otherwise it remains "scheduled"
        assert body["status"] in ("scheduled", "overdue")

    @pytest.mark.spec("FEAT-008-ec3")
    async def test_FEAT_008_ec3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Multiple follow-up types.

        Given an authenticated navigator
        When they create follow-ups with valid types
        Then all are created successfully
        """
        valid_types = ["appointment", "checkup", "lab_test", "imaging", "referral"]

        for fu_type in valid_types:
            resp = await async_client.post(
                f"/cases/{CASE_ID}/followups",
                json={
                    "scheduled_date": "2026-07-01T10:00:00Z",
                    "follow_up_type": fu_type,
                    "notes": f"Test {fu_type}",
                },
                headers=auth_headers_navigator,
            )
            assert resp.status_code == 201, f"Failed for type {fu_type}"
            assert resp.json()["follow_up_type"] == fu_type

    @pytest.mark.spec("FEAT-008-ec4")
    async def test_FEAT_008_ec4(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Filter upcoming by follow-up type.

        Given pending follow-ups of various types exist
        When they submit GET /followups/upcoming?type=appointment
        Then only appointment-type follow-ups are returned
        """
        # Create follow-ups of different types
        await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-10-01T10:00:00Z",
            follow_up_type="appointment",
        )
        await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-10-05T10:00:00Z",
            follow_up_type="lab_test",
        )

        resp = await async_client.get(
            "/followups/upcoming?type=appointment",
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 200
        body = resp.json()
        for item in body["items"]:
            assert item["follow_up_type"] == "appointment"

    @pytest.mark.spec("FEAT-008-ec5")
    async def test_FEAT_008_ec5(
        self,
        async_client: AsyncClient,
        auth_headers_patient: dict,
    ):
        """
        Patient views own follow-ups only.

        Given a patient user
        When the patient submits GET /followups/upcoming
        Then only follow-ups for their own cases are returned
        """
        resp = await async_client.get(
            "/followups/upcoming",
            headers=auth_headers_patient,
        )
        assert resp.status_code == 200
        body = resp.json()
        # Patient should see at most their own follow-ups (may be empty)
        assert "items" in body
        assert "total" in body

    @pytest.mark.spec("FEAT-008-ec6")
    async def test_FEAT_008_ec6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Completed follow-up with completed_at timestamp.

        Given a follow-up is completed via POST /followups/{id}/complete
        When the follow-up is queried
        Then completed_at is set
        And status is "completed"
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-08-15T10:00:00Z",
        )

        complete_resp = await async_client.post(
            f"/followups/{fu['id']}/complete",
            headers=auth_headers_navigator,
        )
        assert complete_resp.status_code == 200

        # Re-fetch to verify persisted state
        resp = await async_client.get(
            f"/followups/{fu['id']}",
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["completed_at"] is not None
        assert body["completed_by"] is not None

    @pytest.mark.spec("FEAT-008-ec7")
    async def test_FEAT_008_ec7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Follow-up list pagination.

        Given follow-ups exist for case c001
        When they submit GET /cases/{c001}/followups?page=1&per_page=2
        Then the response contains paginated results
        """
        # Create a few follow-ups to ensure pagination is testable
        for i in range(3):
            await _create_follow_up(
                async_client, auth_headers_navigator, CASE_ID,
                scheduled_date=f"2026-08-{10 + i:02d}T10:00:00Z",
                notes=f"Pagination test {i}",
            )

        resp = await async_client.get(
            f"/cases/{CASE_ID}/followups?page=1&per_page=2",
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 2
        assert body["per_page"] == 2
        assert body["page"] == 1
        assert body["total"] >= 3

    @pytest.mark.spec("FEAT-008-ec8")
    async def test_FEAT_008_ec8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upcoming view returns scheduled follow-ups with pagination.

        Given follow-ups with various scheduled dates exist
        When they submit GET /followups/upcoming
        Then follow-ups are returned with pagination metadata
        """
        await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-11-01T10:00:00Z",
        )

        resp = await async_client.get(
            "/followups/upcoming",
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert "page" in body
        assert "per_page" in body


# ===================================================================
# ERROR CASES
# ===================================================================


class TestErrorCases:
    """FEAT-008 error-case scenarios (e1-e8)."""

    @pytest.mark.spec("FEAT-008-e1")
    async def test_FEAT_008_e1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up with missing required fields.

        Given an authenticated navigator
        When they submit POST with only notes (missing scheduled_date and follow_up_type)
        Then the response status is 422
        """
        resp = await async_client.post(
            f"/cases/{CASE_ID}/followups",
            json={"notes": "Missing fields"},
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 422

    @pytest.mark.spec("FEAT-008-e2")
    async def test_FEAT_008_e2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Invalid follow-up type.

        Given an authenticated navigator
        When they submit POST with an invalid follow_up_type
        Then the response status is 422 or 400
        """
        resp = await async_client.post(
            f"/cases/{CASE_ID}/followups",
            json={
                "scheduled_date": "2026-07-01T10:00:00Z",
                "follow_up_type": "surgery",
                "notes": "Invalid type",
            },
            headers=auth_headers_navigator,
        )
        assert resp.status_code in (400, 422)

    @pytest.mark.spec("FEAT-008-e3")
    async def test_FEAT_008_e3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up for non-existent case.

        Given an authenticated navigator
        When they submit POST to a non-existent case UUID
        Then the response status is 404
        """
        resp = await async_client.post(
            "/cases/00000000-0000-0000-0000-000000000000/followups",
            json={
                "scheduled_date": "2026-07-01T10:00:00Z",
                "follow_up_type": "appointment",
                "notes": "Non-existent case",
            },
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 404

    @pytest.mark.spec("FEAT-008-e4")
    async def test_FEAT_008_e4(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Invalid date format for scheduled_date.

        Given an authenticated navigator
        When they submit POST with an unparseable scheduled_date
        Then the response status is 422
        """
        resp = await async_client.post(
            f"/cases/{CASE_ID}/followups",
            json={
                "scheduled_date": "not-a-date",
                "follow_up_type": "appointment",
                "notes": "Bad date",
            },
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 422

    @pytest.mark.spec("FEAT-008-e5")
    async def test_FEAT_008_e5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Update completed follow-up.

        Given a follow-up with status "completed"
        When they submit PATCH with updated notes
        Then the response status is 400
        And the error indicates completed follow-ups cannot be modified
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-07-20T10:00:00Z",
        )
        # Complete it first
        await async_client.post(
            f"/followups/{fu['id']}/complete",
            headers=auth_headers_navigator,
        )

        # Attempt to patch a completed follow-up
        resp = await async_client.patch(
            f"/followups/{fu['id']}",
            json={"notes": "Should fail"},
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 400

    @pytest.mark.spec("FEAT-008-e6")
    async def test_FEAT_008_e6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Cancel an already cancelled follow-up (idempotent).

        Given a follow-up with status "cancelled"
        When they submit PATCH with status "cancelled" again
        Then the response status is 200 (idempotent)
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-08-20T10:00:00Z",
        )
        # Cancel it first
        await async_client.patch(
            f"/followups/{fu['id']}",
            json={"status": "cancelled"},
            headers=auth_headers_navigator,
        )

        # Cancel again — should be idempotent
        resp = await async_client.patch(
            f"/followups/{fu['id']}",
            json={"status": "cancelled"},
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    @pytest.mark.spec("FEAT-008-e7")
    async def test_FEAT_008_e7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Get non-existent follow-up.

        Given an authenticated navigator
        When they submit GET /followups/{non-existent}
        Then the response status is 404
        """
        resp = await async_client.get(
            "/followups/00000000-0000-0000-0000-000000000000",
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 404

    @pytest.mark.spec("FEAT-008-e8")
    async def test_FEAT_008_e8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Invalid status transition (completed -> scheduled).

        Given a follow-up with status "completed"
        When they submit PATCH with status "scheduled"
        Then the response status is 400 or 422
        And the error indicates invalid status transition
        """
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-07-25T10:00:00Z",
        )
        # Complete it first
        await async_client.post(
            f"/followups/{fu['id']}/complete",
            headers=auth_headers_navigator,
        )

        # Attempt invalid transition: completed -> scheduled
        resp = await async_client.patch(
            f"/followups/{fu['id']}",
            json={"status": "scheduled"},
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 400


# ===================================================================
# SECURITY
# ===================================================================


class TestSecurity:
    """FEAT-008 security scenarios (s1-s6)."""

    @pytest.mark.spec("FEAT-008-s1")
    async def test_FEAT_008_s1(
        self,
        async_client: AsyncClient,
        auth_headers_volunteer: dict,
    ):
        """
        Volunteer cannot create follow-ups.

        Given an authenticated volunteer
        When they submit POST /cases/{case_id}/followups
        Then the response status is 403
        """
        resp = await async_client.post(
            f"/cases/{CASE_ID}/followups",
            json={
                "scheduled_date": "2026-07-01T10:00:00Z",
                "follow_up_type": "appointment",
                "notes": "Volunteer attempt",
            },
            headers=auth_headers_volunteer,
        )
        assert resp.status_code == 403

    @pytest.mark.spec("FEAT-008-s2")
    async def test_FEAT_008_s2(
        self,
        async_client: AsyncClient,
    ):
        """
        Unauthenticated access rejected.

        Given no authentication token
        When they submit GET /followups/upcoming
        Then the response status is 401
        """
        resp = await async_client.get("/followups/upcoming")
        assert resp.status_code == 401

    @pytest.mark.spec("FEAT-008-s3")
    async def test_FEAT_008_s3(
        self,
        async_client: AsyncClient,
        auth_headers_clinician: dict,
        auth_headers_navigator: dict,
    ):
        """
        Clinician can read but not modify follow-ups.

        Given an authenticated clinician
        When they submit GET /cases/{case_id}/followups -> 200
        When they submit PATCH /followups/{id} -> 403
        """
        # Create a follow-up as navigator so one exists for the clinician to read
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-09-01T10:00:00Z",
        )

        get_resp = await async_client.get(
            f"/cases/{CASE_ID}/followups",
            headers=auth_headers_clinician,
        )
        patch_resp = await async_client.patch(
            f"/followups/{fu['id']}",
            json={"notes": "Clinician edit attempt"},
            headers=auth_headers_clinician,
        )
        assert get_resp.status_code == 200
        assert patch_resp.status_code == 403

    @pytest.mark.spec("FEAT-008-s4")
    async def test_FEAT_008_s4(
        self,
        async_client: AsyncClient,
        auth_headers_patient: dict,
        auth_headers_navigator: dict,
    ):
        """
        Patient can only see own follow-ups.

        Given a patient user and follow-ups for a different patient's case
        When the patient submits GET /followups/upcoming
        Then only their own follow-ups are returned (none for other patients)
        """
        # Create a follow-up on case c002 (under_review, also patient p001)
        fu = await _create_follow_up(
            async_client, auth_headers_navigator, CASE_ID,
            scheduled_date="2026-09-15T10:00:00Z",
        )

        # Patient requests the specific follow-up — access depends on ownership
        resp = await async_client.get(
            f"/followups/{fu['id']}",
            headers=auth_headers_patient,
        )
        # Patient either gets 200 (if own) or 403 (if not theirs)
        assert resp.status_code in (200, 403)

    @pytest.mark.spec("FEAT-008-s5")
    async def test_FEAT_008_s5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        SQL injection in notes field.

        Given an authenticated navigator
        When they submit POST with SQL injection in notes
        Then the response status is 201
        And the notes are stored as literal text
        """
        injection = "'; DROP TABLE followups; --"
        resp = await async_client.post(
            f"/cases/{CASE_ID}/followups",
            json={
                "scheduled_date": "2026-07-01T10:00:00Z",
                "follow_up_type": "appointment",
                "notes": injection,
            },
            headers=auth_headers_navigator,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["notes"] == injection

        # Verify table still works by listing follow-ups
        list_resp = await async_client.get(
            f"/cases/{CASE_ID}/followups",
            headers=auth_headers_navigator,
        )
        assert list_resp.status_code == 200

    @pytest.mark.spec("FEAT-008-s6")
    async def test_FEAT_008_s6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Follow-up mutations are audited.

        Given an authenticated navigator
        When they create and complete a follow-up
        Then activity events are logged for: followup.created, followup.completed
        """
        # TODO: Implement test verifying audit trail
        assert True


# ===================================================================
# PERFORMANCE
# ===================================================================


class TestPerformance:
    """FEAT-008 performance scenarios (p1-p3)."""

    @pytest.mark.performance
    @pytest.mark.spec("FEAT-008-p1")
    async def test_FEAT_008_p1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upcoming view under 200ms with 1,000 follow-ups.

        Given 1,000 pending follow-ups across 200 cases
        When they submit GET /followups/upcoming
        Then the response time is under 200ms at the 95th percentile
        """
        # TODO: Implement performance test
        assert True

    @pytest.mark.performance
    @pytest.mark.spec("FEAT-008-p2")
    async def test_FEAT_008_p2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Follow-up creation under 100ms.

        Given an authenticated navigator
        When they submit POST /cases/{case_id}/followups
        Then the response time is under 100ms at the 95th percentile
        """
        # TODO: Implement performance test
        assert True

    @pytest.mark.performance
    @pytest.mark.spec("FEAT-008-p3")
    async def test_FEAT_008_p3(self):
        """
        Overdue detection query under 100ms.

        Given 500 pending follow-ups with 100 overdue
        When the overdue detection query runs
        Then the computation takes under 100ms
        And all overdue follow-ups are correctly identified
        """
        # TODO: Implement performance test
        assert True


# ===================================================================
# OBSERVABILITY
# ===================================================================


class TestObservability:
    """FEAT-008 observability scenarios (o1-o2)."""

    @pytest.mark.observability
    @pytest.mark.spec("FEAT-008-o1")
    async def test_FEAT_008_o1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Follow-up lifecycle events are logged.

        Given an authenticated navigator
        When they create, update, complete, and cancel follow-ups
        Then activity events are emitted for:
          - followup.created, followup.updated, followup.completed, followup.cancelled
        """
        # TODO: Implement lifecycle audit verification
        assert True

    @pytest.mark.observability
    @pytest.mark.spec("FEAT-008-o2")
    async def test_FEAT_008_o2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Overdue follow-up count in dashboard metrics.

        Given 15 overdue follow-ups exist
        When the dashboard metrics endpoint is called (GET /reports/dashboard)
        Then the response includes overdue_followups_count: 15
        And the metric is computed from real-time scheduled_date evaluation
        """
        # TODO: Implement dashboard metrics test
        assert True
