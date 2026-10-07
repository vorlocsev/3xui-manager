# 3x-ui Manager

Home Assistant App for managing a remote **3x-ui 3.9.x** panel with a focused **VLESS Reality** workflow.

**Current version: 4.5.2**

## What it does

- Home Assistant Ingress web interface
- Connects to a remote 3x-ui panel through its API
- Creates and manages VLESS Reality inbounds
- Creates and manages clients
- Enable / disable / delete clients and inbounds
- Displays client traffic, quota, online status and last seen
- Generates VLESS links and QR codes
- Shares VLESS links through Telegram
- Supports combined **Inbound + client** creation
- Checks the installed 3x-ui version and available stable updates
- Can trigger the native 3x-ui panel update
- RU / EN interface language selector
- Keeps 3x-ui API credentials on the Home Assistant side

## Installation

Add this repository to the Home Assistant App Store:

`https://github.com/vorlocsev/3xui-manager`

Then install **3x-ui Manager**.

## Compatibility

Designed for current Home Assistant Apps/Supervisor and the 3x-ui 3.9.x API model. The project is currently aligned with **3x-ui 3.9.0** and Home Assistant **2026.10.x**.

## Configuration

Configure the App from Home Assistant:

- **3x-ui URL** — address of the remote 3x-ui panel
- **API token** — Bearer token used by the Manager
- **Verify TLS** — enable for a valid trusted certificate
- **Server address** — public IP or domain used in generated VLESS links

No server credentials or personal connection data are stored in the repository.

## Language

The web interface supports:

- 🇷🇺 Русский
- 🇬🇧 English

The selected language is saved in the browser and restored automatically.

## Security

The API token is handled by the Home Assistant App backend and is not embedded in the web interface or repository.

## Project

GitHub: `https://github.com/vorlocsev/3xui-manager`
