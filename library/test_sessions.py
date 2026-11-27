from django.contrib.auth import get_user_model
from django.test import TestCase


class IndependentAdminResearcherSessionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="session-test-admin",
            password="Strong-Test-Password-2026!",
            is_staff=True,
            is_superuser=True,
        )

    def researcher_login(self):
        return self.client.post(
            "/accounts/login/",
            {
                "username": "session-test-admin",
                "password": "Strong-Test-Password-2026!",
            },
            follow=False,
        )

    def admin_login(self):
        return self.client.post(
            "/admin/login/",
            {
                "username": "session-test-admin",
                "password": "Strong-Test-Password-2026!",
                "next": "/admin/",
            },
            follow=False,
        )

    def test_researcher_login_does_not_create_admin_session(self):
        response = self.researcher_login()
        self.assertIn("mizan_researcher_sessionid", response.cookies)
        self.assertNotIn("mizan_admin_sessionid", response.cookies)
        self.assertNotIn("sessionid", response.cookies)

    def test_admin_login_does_not_create_researcher_session(self):
        response = self.admin_login()
        self.assertIn("mizan_admin_sessionid", response.cookies)
        self.assertNotIn("mizan_researcher_sessionid", response.cookies)
        self.assertNotIn("sessionid", response.cookies)

    def test_both_sessions_can_coexist_in_one_browser(self):
        researcher_response = self.researcher_login()
        researcher_cookie = researcher_response.cookies[
            "mizan_researcher_sessionid"
        ].value

        admin_response = self.admin_login()
        admin_cookie = admin_response.cookies["mizan_admin_sessionid"].value

        self.assertNotEqual(researcher_cookie, admin_cookie)
        self.assertEqual(
            self.client.cookies["mizan_researcher_sessionid"].value,
            researcher_cookie,
        )
        self.assertEqual(
            self.client.cookies["mizan_admin_sessionid"].value,
            admin_cookie,
        )

        researcher_page = self.client.get("/")
        admin_page = self.client.get("/admin/")

        self.assertEqual(researcher_page.status_code, 200)
        self.assertEqual(admin_page.status_code, 200)

    def test_researcher_logout_preserves_admin_session(self):
        self.researcher_login()
        self.admin_login()

        response = self.client.post("/accounts/logout/")

        self.assertIn("mizan_researcher_sessionid", response.cookies)
        self.assertEqual(
            response.cookies["mizan_researcher_sessionid"]["max-age"], 0
        )
        self.assertIn("mizan_admin_sessionid", self.client.cookies)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_admin_logout_preserves_researcher_session(self):
        self.researcher_login()
        self.admin_login()

        response = self.client.post("/admin/logout/")

        self.assertIn("mizan_admin_sessionid", response.cookies)
        self.assertEqual(response.cookies["mizan_admin_sessionid"]["max-age"], 0)
        self.assertIn("mizan_researcher_sessionid", self.client.cookies)
        self.assertEqual(self.client.get("/").status_code, 200)
