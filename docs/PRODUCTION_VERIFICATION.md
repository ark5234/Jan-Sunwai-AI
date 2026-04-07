# Production Verification Runbook

This runbook closes production verification tasks for SPA routing, NDMC network config, stress smoke, and clean-machine simulation.

## Commands

## Linux/macOS

- Verify production stack: bash scripts/verify_prod_stack.sh
- Simulate clean deploy: bash scripts/simulate_clean_deploy.sh

## Windows

- Verify production stack: scripts\verify_prod_stack.bat
- Simulate clean deploy: scripts\simulate_clean_deploy.bat

## Verification Scope

1. docker-compose.prod.yml boots successfully.
2. Backend live endpoint responds.
3. Frontend deep-link route returns SPA HTML shell.
4. Backend container can reach OLLAMA_BASE_URL.
5. Short headless locust run completes and writes report.
6. Cold-start timing is logged for deployment simulation.

## Output Artifacts

- reports/load/<timestamp>/locust-report.html
- reports/load/<timestamp>/locust_stats.csv
- reports/load/<timestamp>/locust_failures.csv

## Troubleshooting

- If Ollama check fails, verify OLLAMA_BASE_URL and host routing.
- If SPA check fails, verify frontend nginx.conf try_files and /api proxy.
- If health checks fail, inspect docker compose logs for backend and mongodb.
