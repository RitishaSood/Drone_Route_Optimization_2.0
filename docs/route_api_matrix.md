# Route / API Matrix

| Frontend Feature | Frontend Route | Backend Endpoint | Expected Result | Notes |
| --- | --- | --- | --- | --- |
| Home redirect | `/` | none | loads or redirects | `/` redirects to `/simulation` |
| Simulation Setup | `/simulation` | `POST /api/runs` | creates run | Uses the current scenario form |
| Recent Runs | `/simulation` or `/results` | `GET /api/runs?clientId=` | returns runs | Client-local demo list |
| Run Status | `/results` | `GET /api/runs/:runId/status` | returns status | Used for polling |
| Algorithm Comparison | `/results` | `GET /api/runs/:runId/algorithm-metrics` | returns metrics | Shown after path-planner outputs exist |
| Plot Gallery | `/results` | `GET /api/runs/:runId/plots/:filename` | returns image or 404 | Filename allowlist enforced |
| Downloads | `/results` | `GET /api/runs/:runId/files/:filename` | returns file or 404 | Filename allowlist enforced |
| Drone Database | `/drones` | local static data | no backend required | Static table |
| Methodology | `/methodology` | none | static page | Documentation only |
