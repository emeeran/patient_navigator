# Spec: FEAT-008 — Follow-Up Tracking
# File: specs/features/FEAT-008-follow-up-tracking.feature
# Relates: API-060..064, DATA-008

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ===================================================================
# HAPPY PATH
# ===================================================================

class TestHappyPath:
    """FEAT-008 happy-path scenarios (h1–h8)."""

    @pytest.mark.spec("FEAT-008-h1")
    async def test_FEAT_008_h1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Navigator creates a follow-up for a case.

        Given an authenticated navigator and case "c-001" exists
        When they submit POST /cases/c-001/followups with type, title, description, due_date
        Then the response status is 201
        And a follow-up is created with status "pending"
        And patient_id is denormalized from the case
        And created_by is set to the navigator's user ID
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/followups",
            json={
                "type": "appointment",
                "title": "Consultation with oncologist",
                "description": "First appointment at Apollo Cancer Centre",
                "due_date": "2026-06-15",
            },
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 201

    @pytest.mark.spec("FEAT-008-h2")
    async def test_FEAT_008_h2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        List follow-ups for a case.

        Given case "c-001" has 4 follow-ups
        When they submit GET /cases/c-001/followups
        Then the response contains 4 follow-ups ordered by due_date ascending
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.get(
            f"/cases/{case_id}/followups",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-h3")
    async def test_FEAT_008_h3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Get follow-up detail.

        Given a follow-up exists with id "fu-001"
        When they submit GET /followups/fu-001
        Then the response contains all fields
        """
        followup_id = "fu-001"  # TODO: use seeded follow-up id

        response = await async_client.get(
            f"/followups/{followup_id}",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-h4")
    async def test_FEAT_008_h4(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Mark follow-up as completed.

        Given a follow-up exists with status "pending"
        When they submit PATCH /followups/fu-001 with status "completed"
        Then status is updated to "completed"
        And completed_at is set to current timestamp
        """
        followup_id = "fu-001"  # TODO: use seeded follow-up id

        response = await async_client.patch(
            f"/followups/{followup_id}",
            json={"status": "completed"},
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-h5")
    async def test_FEAT_008_h5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Update follow-up title and due date.

        Given a follow-up exists with id "fu-001"
        When they submit PATCH /followups/fu-001 with new title and due_date
        Then title and due_date are updated
        """
        followup_id = "fu-001"  # TODO: use seeded follow-up id

        response = await async_client.patch(
            f"/followups/{followup_id}",
            json={
                "title": "Follow-up consultation (rescheduled)",
                "due_date": "2026-06-20",
            },
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-h6")
    async def test_FEAT_008_h6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Cancel a follow-up.

        Given a follow-up exists with status "pending"
        When they submit PATCH /followups/fu-001 with status "cancelled"
        Then status is updated to "cancelled"
        """
        followup_id = "fu-001"  # TODO: use seeded follow-up id

        response = await async_client.patch(
            f"/followups/{followup_id}",
            json={"status": "cancelled"},
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-h7")
    async def test_FEAT_008_h7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        View upcoming follow-ups across all cases.

        Given 8 pending follow-ups exist across 3 cases with various due dates
        When they submit GET /followups/upcoming
        Then follow-ups are sorted by due_date ascending (soonest first)
        And only pending follow-ups are included
        """
        response = await async_client.get(
            "/followups/upcoming",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-h8")
    async def test_FEAT_008_h8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Automatic overdue detection.

        Given a pending follow-up with due_date "2026-06-01"
        And the current date is "2026-06-04"
        When the follow-up is queried
        Then the status is automatically "overdue" (computed from due_date < today)
        And the database status remains "pending" (overdue is computed)
        """
        # TODO: Implement test with time-sensitive overdue detection
        assert True


# ===================================================================
# EDGE CASES
# ===================================================================

class TestEdgeCases:
    """FEAT-008 edge-case scenarios (ec1–ec8)."""

    @pytest.mark.spec("FEAT-008-ec1")
    async def test_FEAT_008_ec1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up with due_date today.

        Given an authenticated navigator
        When they submit POST with due_date equal to today
        Then the response status is 201
        And the follow-up has status "pending" (not overdue yet)
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/followups",
            json={
                "type": "appointment",
                "title": "Today's follow-up",
                "due_date": "2026-06-04",  # TODO: use dynamic today's date
            },
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 201

    @pytest.mark.spec("FEAT-008-ec2")
    async def test_FEAT_008_ec2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up with due_date in the past.

        Given an authenticated navigator
        When they submit POST with due_date "2026-05-01"
        Then the response status is 201
        And the follow-up is immediately flagged as overdue when queried
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/followups",
            json={
                "type": "deadline",
                "title": "Past due",
                "due_date": "2026-05-01",
            },
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions including overdue flag on query
        assert response.status_code == 201

    @pytest.mark.spec("FEAT-008-ec3")
    async def test_FEAT_008_ec3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Multiple follow-up types.

        Given an authenticated navigator
        When they create follow-ups with types: appointment, deadline, funding_status, treatment_progress
        Then all are created successfully
        """
        case_id = "c-001"  # TODO: use seeded case id
        types = ["appointment", "deadline", "funding_status", "treatment_progress"]

        for fu_type in types:
            response = await async_client.post(
                f"/cases/{case_id}/followups",
                json={"type": fu_type, "title": f"Test {fu_type}", "due_date": "2026-07-01"},
                headers=auth_headers_navigator,
            )
            # TODO: Implement assertions per type
            assert response.status_code == 201

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
        response = await async_client.get(
            "/followups/upcoming?type=appointment",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-ec5")
    async def test_FEAT_008_ec5(
        self,
        async_client: AsyncClient,
        auth_headers_patient: dict,
    ):
        """
        Patient views own follow-ups only.

        Given a patient user owns patient record "p-001"
        And follow-ups exist for cases of both p-001 and p-002
        When the patient submits GET /followups/upcoming
        Then only follow-ups for their own cases (p-001) are returned
        """
        # TODO: Implement test with patient ownership filtering
        assert True

    @pytest.mark.spec("FEAT-008-ec6")
    async def test_FEAT_008_ec6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Completed follow-up with completed_at timestamp.

        Given a follow-up completed on "2026-06-10"
        When the follow-up is queried
        Then completed_at is set
        And status is "completed"
        """
        # TODO: Implement test verifying completed_at timestamp
        assert True

    @pytest.mark.spec("FEAT-008-ec7")
    async def test_FEAT_008_ec7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Follow-up list pagination.

        Given 50 follow-ups exist for case "c-001"
        When they submit GET /cases/c-001/followups?page=2&per_page=20
        Then the response contains 20 follow-ups
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.get(
            f"/cases/{case_id}/followups?page=2&per_page=20",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-008-ec8")
    async def test_FEAT_008_ec8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upcoming view limited to next 30 days by default.

        Given follow-ups with due dates ranging from today to 60 days out
        When they submit GET /followups/upcoming
        Then only follow-ups within the next 30 days are returned
        And total_count of all pending follow-ups is included in metadata
        """
        response = await async_client.get(
            "/followups/upcoming",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions including 30-day window
        assert response.status_code == 200


# ===================================================================
# ERROR CASES
# ===================================================================

class TestErrorCases:
    """FEAT-008 error-case scenarios (e1–e8)."""

    @pytest.mark.spec("FEAT-008-e1")
    async def test_FEAT_008_e1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up with missing required fields.

        Given an authenticated navigator
        When they submit POST with only title (missing type and due_date)
        Then the response status is 422
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/followups",
            json={"title": "Test"},
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422

    @pytest.mark.spec("FEAT-008-e2")
    async def test_FEAT_008_e2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Invalid follow-up type.

        Given an authenticated navigator
        When they submit POST with type "surgery"
        Then the response status is 422
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/followups",
            json={"type": "surgery", "title": "Test", "due_date": "2026-07-01"},
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422

    @pytest.mark.spec("FEAT-008-e3")
    async def test_FEAT_008_e3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Create follow-up for non-existent case.

        Given an authenticated navigator
        When they submit POST to a non-existent case
        Then the response status is 404
        """
        response = await async_client.post(
            "/cases/00000000-0000-0000-0000-000000000000/followups",
            json={"type": "appointment", "title": "Test", "due_date": "2026-07-01"},
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 404

    @pytest.mark.spec("FEAT-008-e4")
    async def test_FEAT_008_e4(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Invalid date format for due_date.

        Given an authenticated navigator
        When they submit POST with due_date "not-a-date"
        Then the response status is 422
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/followups",
            json={"type": "appointment", "title": "Test", "due_date": "not-a-date"},
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422

    @pytest.mark.spec("FEAT-008-e5")
    async def test_FEAT_008_e5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Update completed follow-up.

        Given a follow-up with status "completed"
        When they submit PATCH with updated title
        Then the response status is 400
        And the error indicates completed follow-ups cannot be modified
        """
        followup_id = "fu-done"  # TODO: use seeded completed follow-up id

        response = await async_client.patch(
            f"/followups/{followup_id}",
            json={"title": "Updated"},
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 400

    @pytest.mark.spec("FEAT-008-e6")
    async def test_FEAT_008_e6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Cancel an already cancelled follow-up.

        Given a follow-up with status "cancelled"
        When they submit PATCH with status "cancelled"
        Then the response status is 200 (idempotent)
        """
        followup_id = "fu-cancel"  # TODO: use seeded cancelled follow-up id

        response = await async_client.patch(
            f"/followups/{followup_id}",
            json={"status": "cancelled"},
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 200

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
        response = await async_client.get(
            "/followups/00000000-0000-0000-0000-000000000000",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 404

    @pytest.mark.spec("FEAT-008-e8")
    async def test_FEAT_008_e8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Invalid status transition (completed -> pending).

        Given a follow-up with status "completed"
        When they submit PATCH with status "pending"
        Then the response status is 422
        And the error indicates invalid status transition
        """
        followup_id = "fu-done"  # TODO: use seeded completed follow-up id

        response = await async_client.patch(
            f"/followups/{followup_id}",
            json={"status": "pending"},
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422


# ===================================================================
# SECURITY
# ===================================================================

class TestSecurity:
    """FEAT-008 security scenarios (s1–s6)."""

    @pytest.mark.spec("FEAT-008-s1")
    async def test_FEAT_008_s1(
        self,
        async_client: AsyncClient,
        auth_headers_volunteer: dict,
    ):
        """
        Volunteer cannot create follow-ups.

        Given an authenticated volunteer
        When they submit POST /cases/c-001/followups
        Then the response status is 403
        """
        response = await async_client.post(
            "/cases/c-001/followups",
            json={"type": "appointment", "title": "Test", "due_date": "2026-07-01"},
            headers=auth_headers_volunteer,
        )
        # TODO: Implement assertions
        assert response.status_code == 403

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
        response = await async_client.get("/followups/upcoming")
        # TODO: Implement assertions
        assert response.status_code == 401

    @pytest.mark.spec("FEAT-008-s3")
    async def test_FEAT_008_s3(
        self,
        async_client: AsyncClient,
        auth_headers_clinician: dict,
    ):
        """
        Clinician can read but not modify follow-ups.

        Given an authenticated clinician
        When they submit GET /cases/c-001/followups -> 200
        When they submit PATCH /followups/fu-001 -> 403
        """
        case_id = "c-001"  # TODO: use seeded case id
        followup_id = "fu-001"  # TODO: use seeded follow-up id

        get_resp = await async_client.get(
            f"/cases/{case_id}/followups",
            headers=auth_headers_clinician,
        )
        patch_resp = await async_client.patch(
            f"/followups/{followup_id}",
            json={"status": "completed"},
            headers=auth_headers_clinician,
        )
        # TODO: Implement assertions
        assert get_resp.status_code == 200
        assert patch_resp.status_code == 403

    @pytest.mark.spec("FEAT-008-s4")
    async def test_FEAT_008_s4(
        self,
        async_client: AsyncClient,
        auth_headers_patient: dict,
    ):
        """
        Patient can only see own follow-ups.

        Given a patient user and follow-ups for a different patient's case
        When the patient submits GET /followups/fu-other
        Then the response status is 403
        """
        # TODO: Implement test with own vs other patient follow-ups
        assert True

    @pytest.mark.spec("FEAT-008-s5")
    async def test_FEAT_008_s5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        SQL injection in title field.

        Given an authenticated navigator
        When they submit POST with SQL injection in title
        Then the response status is 201
        And the title is stored as literal text
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/followups",
            json={
                "type": "appointment",
                "title": "'; DROP TABLE followups; --",
                "due_date": "2026-07-01",
            },
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions including table integrity
        assert response.status_code == 201

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
    """FEAT-008 performance scenarios (p1–p3)."""

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
        When they submit POST /cases/c-001/followups
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
    """FEAT-008 observability scenarios (o1–o2)."""

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
        And the metric is computed from real-time due_date evaluation
        """
        # TODO: Implement dashboard metrics test
        assert True
