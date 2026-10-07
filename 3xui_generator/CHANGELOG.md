# Changelog

## 4.2.1

- Restored the full management API surface from v4.1.
- Fixed existing-client VLESS link generation so it never creates a duplicate inbound/client.
- Added existing-client link and subscription endpoint.
- Fixed Reality X25519 generation to use the current 3x-ui GET endpoint.
- Added inbound update, client update, cleanup and management helpers.
- Added QR generation for existing clients.
- Kept API credentials server-side.

## 4.2.0

- Updated for current Home Assistant App repository/build model.
- Removed legacy build.yaml.
- Dockerfile is now the single source of truth for the base image and labels.
- Added Home Assistant minimum version 2026.4.0.
- Added English configuration translations.
- Fixed optional configuration fields so they are not unnecessarily required.
- Kept the 3x-ui API token server-side.
- Prepared the repository for direct installation from GitHub.

## 4.1.0

- Public-release cleanup.
- Removed developer-specific placeholder data.
- Renamed the project to 3x-ui Manager.
