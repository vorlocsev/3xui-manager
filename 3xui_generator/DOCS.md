# 3x-ui Manager 4.2

Home Assistant App for managing a remote 3x-ui panel.

## Install

1. Open **Settings → Apps** in Home Assistant.
2. Open the App Store menu.
3. Add the repository:
   `https://github.com/vorlocsev/3xui-manager`
4. Install **3x-ui Manager**.
5. Configure the remote 3x-ui URL and API token.
6. Start the app and open its Ingress panel.

The app does not expose a host port. Its web UI is available through Home Assistant Ingress.

## Configuration

Required:
- **3x-ui URL** — the base URL of the remote panel.
- **API token** — 3x-ui Bearer token.

Optional:
- **VLESS server address** — address used in generated VLESS links.
- **Subscription base URL** — optional external subscription URL base.
- **Verify TLS** — enabled by default.

## 3x-ui API

The app uses the authenticated `/panel/api/*` API. 3x-ui supports Bearer authentication for these endpoints. VLESS Reality creation uses the inbound and client APIs and the server X25519 key generator. citeturn0search1

## Security

The API token stays inside the App container and is never sent to the browser frontend.

Do not commit your real API token, server address, UUIDs, Reality keys or VLESS links to GitHub.
