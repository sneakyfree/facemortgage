/**
 * Load Testing Script for FaceMortgage
 * 
 * Usage: k6 run scripts/load-test.js
 * 
 * Targets:
 * - /api/v1/grid: Professional grid load
 * - /api/v1/matching/find: Match algorithm
 * - /api/v1/auth/login: Authentication
 * 
 * Pass criteria:
 * - 1000 concurrent virtual users
 * - p95 response time < 500ms
 * - Error rate < 1%
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const gridLatency = new Trend('grid_latency');
const matchLatency = new Trend('match_latency');
const authLatency = new Trend('auth_latency');

// Test configuration
export const options = {
    scenarios: {
        // Ramp up to 1000 users
        load_test: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '30s', target: 100 },   // Warm up
                { duration: '1m', target: 500 },    // Ramp to 500
                { duration: '2m', target: 1000 },   // Peak load
                { duration: '1m', target: 1000 },   // Sustain
                { duration: '30s', target: 0 },     // Ramp down
            ],
            gracefulRampDown: '30s',
        },
    },
    thresholds: {
        'http_req_duration': ['p(95)<500'],          // 95% of requests under 500ms
        'errors': ['rate<0.01'],                     // Error rate under 1%
        'grid_latency': ['p(95)<300'],               // Grid loads fast
        'match_latency': ['p(95)<800'],              // Matching can be slower
        'auth_latency': ['p(95)<200'],               // Auth must be fast
    },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:5846';

// Test data
const STATES = ['CA', 'TX', 'FL', 'NY', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI'];
const LOAN_PURPOSES = ['purchase', 'refinance', 'cash_out', 'heloc'];
const TIMELINES = ['immediate', '30_days', 'exploring'];

function randomChoice(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

export default function () {
    const iteration = __ITER;

    // Distribute load across endpoints
    const endpoint = iteration % 3;

    switch (endpoint) {
        case 0:
            testGridEndpoint();
            break;
        case 1:
            testMatchingEndpoint();
            break;
        case 2:
            testAuthEndpoint();
            break;
    }

    // Random sleep between 0.5-2 seconds
    sleep(0.5 + Math.random() * 1.5);
}

function testGridEndpoint() {
    const startTime = new Date();

    const response = http.get(`${BASE_URL}/api/v1/grid`, {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'grid' },
    });

    gridLatency.add(new Date() - startTime);

    const success = check(response, {
        'grid: status 200': (r) => r.status === 200,
        'grid: has professionals': (r) => {
            try {
                const body = JSON.parse(r.body);
                return Array.isArray(body.professionals);
            } catch {
                return false;
            }
        },
    });

    errorRate.add(!success);
}

function testMatchingEndpoint() {
    const startTime = new Date();

    const payload = JSON.stringify({
        state: randomChoice(STATES),
        loan_purpose: randomChoice(LOAN_PURPOSES),
        property_type: 'single_family',
        timeline: randomChoice(TIMELINES),
        special_needs: [],
    });

    const response = http.post(`${BASE_URL}/api/v1/matching/find`, payload, {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'matching' },
    });

    matchLatency.add(new Date() - startTime);

    const success = check(response, {
        'matching: status 200': (r) => r.status === 200,
        'matching: has matches': (r) => {
            try {
                const body = JSON.parse(r.body);
                return Array.isArray(body.matches);
            } catch {
                return false;
            }
        },
    });

    errorRate.add(!success);
}

function testAuthEndpoint() {
    const startTime = new Date();

    // Test the login endpoint with demo credentials
    const payload = JSON.stringify({
        email: 'john@loanpro.com',
        password: 'demo123',
    });

    const response = http.post(`${BASE_URL}/api/v1/auth/login`, payload, {
        headers: { 'Content-Type': 'application/json' },
        tags: { name: 'auth' },
    });

    authLatency.add(new Date() - startTime);

    // Note: We expect some auth failures under load (rate limiting)
    const success = check(response, {
        'auth: status 200 or 429': (r) => r.status === 200 || r.status === 429,
    });

    // Only count as error if unexpected status
    errorRate.add(response.status !== 200 && response.status !== 429);
}

export function handleSummary(data) {
    return {
        'stdout': textSummary(data, { indent: '  ' }),
        'results/load-test-results.json': JSON.stringify(data),
    };
}

function textSummary(data, options) {
    const indent = options.indent || '';
    let output = '\n';
    output += '==========================================\n';
    output += '  FaceMortgage Load Test Results\n';
    output += '==========================================\n\n';

    output += `${indent}VUs Max: ${data.metrics.vus_max.values.max}\n`;
    output += `${indent}Iterations: ${data.metrics.iterations.values.count}\n`;
    output += `${indent}Duration: ${Math.round(data.state.testRunDurationMs / 1000)}s\n\n`;

    output += `${indent}HTTP Requests:\n`;
    output += `${indent}  Total: ${data.metrics.http_reqs.values.count}\n`;
    output += `${indent}  Rate: ${data.metrics.http_reqs.values.rate.toFixed(2)}/s\n\n`;

    output += `${indent}Response Times (p95):\n`;
    output += `${indent}  Grid: ${data.metrics.grid_latency?.values['p(95)']?.toFixed(0) || 'N/A'}ms\n`;
    output += `${indent}  Matching: ${data.metrics.match_latency?.values['p(95)']?.toFixed(0) || 'N/A'}ms\n`;
    output += `${indent}  Auth: ${data.metrics.auth_latency?.values['p(95)']?.toFixed(0) || 'N/A'}ms\n\n`;

    output += `${indent}Error Rate: ${(data.metrics.errors.values.rate * 100).toFixed(2)}%\n\n`;

    // Pass/Fail
    const passed = Object.values(data.thresholds || {}).every(t => t.ok);
    output += `${indent}STATUS: ${passed ? '✅ PASSED' : '❌ FAILED'}\n`;

    return output;
}
