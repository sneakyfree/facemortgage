"""
Load testing suite for FaceMortgage API.

Uses Locust for load testing. Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or headless:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
        --headless -u 100 -r 10 --run-time 5m

Configuration:
    -u: Number of users to simulate
    -r: Spawn rate (users per second)
    --run-time: Test duration

Web UI available at http://localhost:8089 when running in headed mode.
"""

from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import json
import logging

logger = logging.getLogger(__name__)


class BorrowerUser(HttpUser):
    """
    Simulates a borrower browsing the professional grid.

    Behavior pattern:
    - Mostly browses the grid
    - Occasionally filters
    - Sometimes views individual professional profiles
    - Rarely initiates calls
    """

    # Wait 1-3 seconds between actions (typical browsing pattern)
    wait_time = between(1, 3)

    # Weight: borrowers are the majority of traffic
    weight = 10

    def on_start(self):
        """Initialize user session."""
        self.session_id = f"load-test-{random.randint(100000, 999999)}"
        self.viewed_professionals = []

    @task(50)
    def browse_grid(self):
        """Browse the professional grid - most common action."""
        with self.client.get(
            "/api/v1/grid",
            params={"page": 1, "page_size": 20},
            name="/api/v1/grid",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                data = response.json()
                # Store some professional IDs for later use
                professionals = data.get("professionals", [])
                if professionals:
                    self.viewed_professionals = [p["id"] for p in professionals[:5]]
                response.success()
            else:
                response.failure(f"Grid returned {response.status_code}")

    @task(20)
    def browse_grid_with_filters(self):
        """Browse with filters - moderately common."""
        filters = self._random_filters()
        with self.client.get(
            "/api/v1/grid",
            params={"page": 1, "page_size": 20, **filters},
            name="/api/v1/grid (filtered)",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Filtered grid returned {response.status_code}")

    @task(10)
    def get_lookup_data(self):
        """Fetch filter options - done when opening filter panel."""
        with self.client.get(
            "/api/v1/grid/lookup-data",
            name="/api/v1/grid/lookup-data",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Lookup data returned {response.status_code}")

    @task(15)
    def view_professional(self):
        """View a professional profile - less common."""
        if not self.viewed_professionals:
            return

        professional_id = random.choice(self.viewed_professionals)
        with self.client.get(
            f"/api/v1/professionals/{professional_id}",
            name="/api/v1/professionals/{id}",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Professional view returned {response.status_code}")

    @task(3)
    def track_impression(self):
        """Track grid impression - happens on page load."""
        if not self.viewed_professionals:
            return

        with self.client.post(
            "/api/v1/grid/impression",
            json={
                "professional_ids": self.viewed_professionals[:3],
                "session_id": self.session_id,
            },
            name="/api/v1/grid/impression",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Impression tracking returned {response.status_code}")

    @task(2)
    def track_click(self):
        """Track profile click - happens when user clicks on card."""
        if not self.viewed_professionals:
            return

        with self.client.post(
            "/api/v1/grid/click",
            json={
                "professional_id": random.choice(self.viewed_professionals),
                "click_type": random.choice(["profile_view", "call_initiate"]),
                "grid_position": random.randint(1, 20),
                "session_id": self.session_id,
            },
            name="/api/v1/grid/click",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Click tracking returned {response.status_code}")

    def _random_filters(self):
        """Generate random filter combinations."""
        filters = {}

        # Randomly add state filter
        if random.random() < 0.5:
            filters["state_code"] = random.choice(["CA", "TX", "FL", "NY", "WA"])

        # Randomly add user type filter
        if random.random() < 0.3:
            filters["user_type"] = random.choice(["loan_officer", "realtor"])

        # Randomly add language filter
        if random.random() < 0.2:
            filters["language_code"] = random.choice(["en", "es", "zh"])

        return filters


class ProfessionalUser(HttpUser):
    """
    Simulates a professional checking their dashboard.

    Behavior pattern:
    - Checks dashboard periodically
    - Updates availability status
    - Views leads occasionally
    """

    # Wait 5-10 seconds between actions (professionals check less frequently)
    wait_time = between(5, 10)

    # Weight: fewer professionals than borrowers
    weight = 2

    def on_start(self):
        """Attempt to authenticate (will likely fail without real credentials)."""
        self.authenticated = False
        # In a real load test, you'd use test credentials here
        # For now, we'll just hit public endpoints or expect 401s

    @task(5)
    def check_dashboard(self):
        """Check dashboard stats."""
        with self.client.get(
            "/api/v1/professionals/me/dashboard",
            name="/api/v1/professionals/me/dashboard",
            catch_response=True,
        ) as response:
            # Expect 401 without auth, 200 with auth
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Dashboard returned {response.status_code}")

    @task(2)
    def update_status(self):
        """Update availability status."""
        with self.client.post(
            "/api/v1/professionals/me/status",
            json={"status": random.choice(["online_available", "online_busy", "away"])},
            name="/api/v1/professionals/me/status",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Status update returned {response.status_code}")

    @task(1)
    def check_subscription(self):
        """Check subscription status."""
        with self.client.get(
            "/api/v1/billing/subscription",
            name="/api/v1/billing/subscription",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 401]:
                response.success()
            else:
                response.failure(f"Subscription check returned {response.status_code}")


class DataProviderUser(HttpUser):
    """
    Simulates users requesting professional stats (baseball cards).

    Behavior pattern:
    - Requests stats for specific NMLS IDs
    - Caching should reduce backend load
    """

    wait_time = between(2, 5)
    weight = 3

    def on_start(self):
        """Setup test NMLS IDs."""
        # Sample NMLS IDs for testing
        self.nmls_ids = [
            "123456",
            "234567",
            "345678",
            "456789",
            "567890",
        ]

    @task
    def get_professional_stats(self):
        """Request professional stats from data provider."""
        nmls_id = random.choice(self.nmls_ids)
        with self.client.get(
            f"/api/v1/data/stats/{nmls_id}",
            name="/api/v1/data/stats/{nmls_id}",
            catch_response=True,
        ) as response:
            # 200 for success, 404 for not found, 503 for provider unavailable
            if response.status_code in [200, 404, 503]:
                response.success()
            else:
                response.failure(f"Stats returned {response.status_code}")


class HealthCheckUser(HttpUser):
    """
    Simulates load balancer health checks.

    Behavior pattern:
    - Very frequent, lightweight checks
    - Must be fast and reliable
    """

    wait_time = between(1, 2)
    weight = 1

    @task(10)
    def liveness_check(self):
        """Liveness probe - should always succeed."""
        with self.client.get(
            "/health/live",
            name="/health/live",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Liveness check returned {response.status_code}")

    @task(5)
    def readiness_check(self):
        """Readiness probe - checks dependencies."""
        with self.client.get(
            "/health/ready",
            name="/health/ready",
            catch_response=True,
        ) as response:
            if response.status_code in [200, 503]:
                response.success()
            else:
                response.failure(f"Readiness check returned {response.status_code}")


# Event hooks for custom reporting


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log when test starts."""
    logger.info("Load test starting...")
    if isinstance(environment.runner, MasterRunner):
        logger.info("Running in distributed mode as master")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log summary when test stops."""
    logger.info("Load test completed")

    if environment.stats.total.num_failures > 0:
        logger.warning(
            f"Total failures: {environment.stats.total.num_failures}"
        )


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track slow requests."""
    if response_time > 1000:  # > 1 second
        logger.warning(f"Slow request: {name} took {response_time}ms")
