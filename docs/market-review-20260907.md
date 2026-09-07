# Market and dependency review — 2026-09-07

Target: early-career North American Backend, Cloud Infrastructure and ML Infrastructure roles. This is a targeted official-company sample, not a market-wide census.

- [Amazon ML Infra Services SDE I, Cupertino](https://www.amazon.jobs/en/jobs/10464055/software-development-engineer-i-ml-infra-services-annapurna-labs): automation, compatibility, root cause and metrics; full official JD and Apply link read on 2026-09-07. Original publication date was not exposed.
- [Lightfield Infrastructure Early Career, Cambridge](https://jobs.ashbyhq.com/lightfield/9a7ef2f9-577a-4242-b884-719e3cdf4420): concurrency, backpressure, permissions and debugging in the official ATS search body. Publication date is unverified.
- [Benchling Backend Infrastructure](https://jobs.ashbyhq.com/benchling/e729560e-a2dd-4949-8dc5-031312a9b2e2), [Astronomer Data Plane](https://jobs.ashbyhq.com/astronomer/282736cd-6967-469b-b13d-63b54424ed1c/), and [Notion Infrastructure](https://jobs.ashbyhq.com/notion/42f18ccd-c4c8-4a85-8c1f-de12c575fe87/): indexed official descriptions emphasize cloud/service tooling, compute lifecycle or async reliability. These pages were JS-only; current status/location and posting dates were not independently verified. Search crawl dates within 3–4 months are not posting dates. Public ATS metadata requests returned 403.

The requested recent 3–6 month window was prioritized but cannot be certified for this sample. Repeated themes support lifecycle and failure-handling work. AWS/Kubernetes are specific cloud-role preferences; a permission graph is a company-specific focus. Neither technology popularity nor these JDs prove this project is deployed or that a particular applicant is eligible.

[Collector core 0.160.0](https://github.com/open-telemetry/opentelemetry-collector/releases/tag/v0.160.0) was released 2026-09-02; the repository is active. [Batching migration notes](https://github.com/open-telemetry/opentelemetry-collector/blob/main/docs/rfcs/batching-migration.md) motivate explicit queue batching settings and two clean-version campaigns. No release-note speedup is claimed.

[Cosign 2.6.5](https://github.com/sigstore/cosign/releases/tag/v2.6.5) and [3.1.3](https://github.com/sigstore/cosign/releases/tag/v3.1.3) were released 2026-08-06. Select the maintained 2.6 patch for the existing detached-signature contract; defer [v3 default changes](https://github.com/sigstore/cosign/releases/tag/v3.0.0) until new-bundle/keyless behavior has its own requirements and tests.

[Python 3.14.7](https://www.python.org/downloads/release/python-3147/) was released 2026-08-05. CI qualifies Python 3.12 and 3.14.7 without changing the author's local 3.14.4 interpreter. Official action commits and tool checksums are pinned. A configured CI matrix is not a successful run; use the repository's Actions results for execution evidence.
