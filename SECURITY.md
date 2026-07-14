# Security

## Local configuration

Provide `GOOGLE_MAPS_API_KEY` and `IFTTT_WEBHOOK_KEY` through the process environment. The IFTTT integration is disabled when its key is absent. Do not put credentials in source files, test fixtures, or generated files.

Copy `.env.example` to `.env` for a local record of the required values, then export them into the process environment before running the application. The application does not automatically load `.env`.

Copy `zappa_settings.example.json` to `zappa_settings.json` for deployment settings and replace its placeholders locally. The local file is ignored by Git.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to the repository owner rather than opening a public issue.
