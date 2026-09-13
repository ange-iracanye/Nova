# Nova Mobile

Native iOS and Android client for Nova. The mobile client is deliberately isolated under `mobile/`; the existing React/Vite website and FastAPI backend are not modified by this mobile implementation.

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
- Dashboard metrics and subjects using `/v1/dashboard`
- Conversation history
- Settings backed by the existing `/settings` contract
- Account and logout
- Bottom-tab navigation optimized for one-handed use
- Dark Nova visual language without copying web-only CSS

## Why the API layer is separate

The mobile client does not duplicate NovaCore logic. `src/api.ts` is a small typed adapter around the existing HTTP API. This keeps the business logic on the server and prevents mobile-only forks of tutoring behavior.

## Local development

From the repository root:

```bash
cd mobile
npm install
npx expo start
```

Then open the project with an Android emulator, iOS simulator, or Expo Go as appropriate for your development environment.

The production API defaults to the same Render API used by the current web client. For local development, change `extra.apiUrl` in `app.json` to the reachable backend URL for your device/emulator.

## Important compatibility note

The existing backend currently exposes a process-local auth session store and a process-level NovaCore lock. The mobile app therefore reuses the existing session/token mechanism rather than introducing a second authentication system. The existing web application remains the source of truth for web behavior.

## Safety boundary

No files under `frontend/` or the existing backend runtime were changed to create this client. The mobile app lives behind a separate branch and can be reviewed independently before it is merged.
