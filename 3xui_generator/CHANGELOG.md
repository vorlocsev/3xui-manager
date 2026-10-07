# Changelog

All notable changes to 3x-ui Manager are documented here. Newest versions are listed first.

## 4.5.0 - 2026-10-08

- Added the connected 3x-ui panel version to the app header.
- Added a stable-release update check using the native 3x-ui update API.
- Added one-click 3x-ui panel update with confirmation.
- Added post-update status refresh after the 3x-ui panel restarts.
- Kept update execution inside 3x-ui instead of downloading or replacing the panel binary from the Home Assistant app.
- Bumped the Home Assistant App version to 4.5.0.

## 4.4.0 - 2026-10-08

- Simplified the client interface into compact client cards.
- Added online/offline status using the 3x-ui clients online endpoint.
- Added last-seen information for offline clients when available.
- Added automatic client presence refresh every 15 seconds.
- Added one-tap VLESS link copy action.
- Added Telegram share action using Telegram's official share URL.
- Added inline QR code display for each client.
- Kept enable/disable and delete actions directly on the client card.
- Simplified inbound display and moved inbound management below the client list.
- Bumped the Home Assistant App version to 4.4.0.

## 4.3.1 - 2026-10-08

- Added a combined **Inbound + client** creation workflow.
- The combined workflow creates a VLESS Reality inbound and immediately adds a client to it.
- Added traffic quota presets: 10, 30, 50, 100, 200, 500 and 1000 GB.
- Added a custom traffic quota field in GB.
- Added VLESS link and QR code output after combined creation.
- Disabled create buttons while a creation request is running to prevent duplicate submissions.
- Added rollback: if client creation fails after the inbound was created, the newly created inbound is removed when possible.
- Added a duplicate-email check to the combined creation workflow.
- Bumped the Home Assistant App version to 4.3.1.

## 4.3.0 - 2026-10-04

- Added explicit VLESS Reality inbound creation.
- Added client creation for an existing VLESS Reality inbound.
- Added client traffic quota selection.
- Added configurable server address for generated VLESS links.
- Reused existing inbounds instead of automatically creating a new inbound on port 443.
- Added backend endpoints for inbound and client creation.
- Improved compatibility with 3x-ui 3.9.0 API responses.

## 4.2.7 - 2026-10-04

- Fixed client lookup for 3x-ui 3.9.0 hydration responses.
- Fixed client enable/disable updates by sending the complete client payload.
- Improved client update handling for 3x-ui 3.9.0.
- Fixed client management actions that previously failed because the nested `client` object was not extracted.

## 4.2.6 - 2026-10-04

- Improved client action handling.
- Improved traffic display.
- Fixed client delete handling.
- Improved client-side action error reporting.

## 4.2.5 - 2026-10-04

- Fixed Home Assistant Ingress API routing.
- API calls now work correctly when the App is opened through an Ingress URL.

## 4.2.4 - 2026-10-04

- Fixed optional subscription configuration schema.
- Removed an invalid empty default for the optional subscription base URL.

## 4.2.3 - 2026-10-04

- Fixed the Home Assistant App watchdog URL.
- Updated watchdog configuration to use the required `[HOST]:[PORT]` format.

## 4.2.2 - 2026-10-04

- Added valid default App configuration values for Home Assistant.
- Improved compatibility with Supervisor configuration validation.

## 4.2.1 - 2026-10-04

- Restored the full management API surface from v4.1.
- Fixed existing-client VLESS link generation so it never creates a duplicate inbound/client.
- Added existing-client link and subscription endpoint.
- Fixed Reality X25519 generation to use the current 3x-ui GET endpoint.
- Added inbound update, client update, cleanup and management helpers.
- Added QR generation for existing clients.
- Kept API credentials server-side.
- Fixed runtime and configuration issues discovered during Home Assistant 2026.4+ testing.

## 4.2.0 - 2026-10-04

- Updated for current Home Assistant App repository/build model.
- Removed legacy build.yaml.
- Dockerfile is now the single source of truth for the base image and labels.
- Added Home Assistant minimum version 2026.4.0.
- Added English configuration translations.
- Fixed optional configuration fields so they are not unnecessarily required.
- Kept the 3x-ui API token server-side.
- Prepared the repository for direct installation from GitHub.

## 4.1.0 - 2026-10-04

- Public-release cleanup.
- Removed developer-specific placeholder data.
- Renamed the project to 3x-ui Manager.

