"""
FaceMortgage Load Testing Suite.

Main Locust file combining all test scenarios.
"""

import os
from locust import HttpUser, task, between, events
from faker import Faker

fake = Faker()


class BorrowerUser(HttpUser):
    """
    Simulates a borrower browsing the grid and initiating calls.
    
    Most common user type - high volume, read-heavy.
    """
    weight = 5  # 5x more borrowers than professionals
    wait_time = between(1, 3)
    
    @task(5)
    def browse_grid(self):
        """Browse the professional grid - most common action."""
        self.client.get("/api/v1/grid")
    
    @task(3)
    def filter_grid_by_state(self):
        """Filter grid by state."""
        states = ["CA", "TX", "NY", "FL", "WA", "AZ"]
        state = fake.random_element(states)
        self.client.get(f"/api/v1/grid?state={state}")
    
    @task(2)
    def filter_grid_advanced(self):
        """Advanced grid filtering."""
        params = {
            "state": fake.random_element(["CA", "TX", "NY"]),
            "specialty": fake.random_element(["first_time", "refinance", "jumbo"]),
            "available_only": "true",
        }
        self.client.get("/api/v1/grid", params=params)
    
    @task(2)
    def view_professional_profile(self):
        """View a professional's detailed profile."""
        # In real test, would fetch actual IDs from grid first
        self.client.get("/api/v1/professionals/featured")
    
    @task(1)
    def get_matched(self):
        """Submit borrower intake for matching."""
        data = {
            "state": fake.random_element(["CA", "TX", "NY", "FL"]),
            "loan_purpose": fake.random_element(["purchase", "refinance"]),
            "property_type": "single_family",
            "timeline": fake.random_element(["immediate", "30_days", "exploring"]),
        }
        self.client.post("/api/v1/matching/match", json=data)
    
    @task(1)
    def lookup_state_data(self):
        """Fetch dropdown data."""
        self.client.get("/api/v1/lookups/states")
        self.client.get("/api/v1/lookups/specialties")


class ProfessionalUser(HttpUser):
    """
    Simulates a logged-in professional using their dashboard.
    
    Less common but more write-heavy operations.
    """
    weight = 1
    wait_time = between(2, 5)
    
    def on_start(self):
        """Login at start of session."""
        email = os.environ.get("TEST_PRO_EMAIL", "pro@example.com")
        password = os.environ.get("TEST_PRO_PASSWORD", "testpassword123")
        
        response = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers["Authorization"] = f"Bearer {self.token}"
    
    @task(3)
    def check_dashboard(self):
        """Professional checks their dashboard stats."""
        self.client.get("/api/v1/professionals/me/stats")
    
    @task(2)
    def view_leads(self):
        """View my leads."""
        self.client.get("/api/v1/leads")
    
    @task(2)
    def view_calls(self):
        """View call history."""
        self.client.get("/api/v1/calls")
    
    @task(1)
    def check_billing(self):
        """Check billing status."""
        self.client.get("/api/v1/billing/subscription")
    
    @task(1)
    def check_analytics(self):
        """Check analytics."""
        self.client.get("/api/v1/analytics/summary")


class AdminUser(HttpUser):
    """
    Simulates an admin user.
    
    Rare but potentially heavy operations.
    """
    weight = 0.1
    wait_time = between(5, 10)
    
    def on_start(self):
        """Login as admin."""
        email = os.environ.get("TEST_ADMIN_EMAIL", "admin@example.com")
        password = os.environ.get("TEST_ADMIN_PASSWORD", "adminpassword123")
        
        response = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.client.headers["Authorization"] = f"Bearer {self.token}"
    
    @task(3)
    def view_moderation_queue(self):
        """Check moderation queue."""
        self.client.get("/api/v1/moderation/queue")
    
    @task(2)
    def view_users(self):
        """View user list."""
        self.client.get("/api/v1/admin/users")
    
    @task(1)
    def view_audit(self):
        """Check audit logs."""
        self.client.get("/api/v1/audit")


# Event hooks for reporting

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log slow requests for debugging."""
    if response_time > 500:
        print(f"SLOW: {request_type} {name} took {response_time}ms")


@events.quitting.add_listener
def on_quit(environment, **kwargs):
    """Print summary on quit."""
    if environment.stats.total.fail_ratio > 0.01:
        print(f"WARNING: Failure rate {environment.stats.total.fail_ratio:.2%} exceeds 1% threshold")
