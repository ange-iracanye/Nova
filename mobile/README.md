# Nova Mobile

Native iOS and Android client for Nova. The mobile client is deliberately isolated under `mobile/`; the existing React/Vite website and FastAPI backend runtime are not modified by this client.

## Architecture

```text
iOS / Android
     |
     v
Expo + React Native + TypeScript
     |
     +--> SecureStore session token
     +--> Native navigation / mobile UI
     |
     v
Existing Nova FastAPI API
     |
     +--> authentication
     +--> chat
     +--> conversations
     +--> dashboard
     +--> settings
     |
     v
Existing NovaCore + persistence + AI providers
```

## Current mobile surface

- Login and registration
- Secure session persistence with `expo-secure-store`
- Native chat using the existing `/chat` contract
- User-scoped dashboard using `/dashboard/{email}`
- Conversation history
- Settings backed by the existing `/settings` contract
- Account and logout
- Bottom-tab navigation optimized for one-handed use
- Dark Nova visual language without copying web-only CSS

## Local validation

From the repository root:

```bash
cd mobile
npm install
npm run typecheck
npx expo start
```

Then open the project with an Android emulator, iOS simulator, or Expo Go as appropriate for your development environment and smoke-test login, chat, dashboard, history, settings save, and logout.

The production API is configured in `app.json`. For local development, change `extra.apiUrl` to a backend URL reachable from the device or emulator.

## Compatibility boundary

The mobile client intentionally does not duplicate NovaCore logic. `src/api.ts` is a small adapter around the existing HTTP API, while authentication stores the server session token in SecureStore. This keeps tutoring behavior and persistence on the server and avoids a mobile-only fork.

The existing web application and backend runtime remain the source of truth. The mobile client is additive and lives under `mobile/`.
