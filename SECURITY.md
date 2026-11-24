# Security policy

## Reporting a vulnerability
Do not open a public issue containing exploit details, credentials, customer data or evidence samples. Use GitHub's private vulnerability reporting feature for this repository when available. If private reporting is unavailable, contact the repository maintainer through GitHub and request a private disclosure channel.

## Scope
Report vulnerabilities affecting authentication, tenant isolation, evidence integrity, custody records, data exposure, connector credentials, model-provider egress, upload handling, dependency or container security.

## Response expectations
The maintainers should acknowledge a report, reproduce it safely, assess affected versions, coordinate a fix and publish an advisory when appropriate. Do not test against systems or tenants you do not own or have explicit permission to assess.

## Secrets
Never commit API keys, private keys, database passwords, production evidence, personal data or customer configuration. Rotate any secret that is accidentally committed; deleting the commit alone does not revoke it.
