# Nova Mobile

Native iOS and Android client for Nova. The mobile client is isolated under `mobile/` and uses the existing Nova API.

## Development

```bash
cd mobile
npm install
npm run typecheck
npx expo start
```

Test login, registration, chat, dashboard, conversations, settings save, and logout on an Android or iOS device/simulator before publishing a store build.

## Architecture

The app uses Expo + React Native + TypeScript, native navigation, SecureStore for the mobile session token, and the existing FastAPI backend. NovaCore and persistence remain server-side.
