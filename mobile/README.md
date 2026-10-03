# Nova Mobile

Native iOS and Android client for Nova. The mobile client is built with Expo + React Native and uses the existing Nova FastAPI backend.

## Development

Requirements:
- Node.js 20.19+ for Expo SDK 55
- An Android device/emulator or iOS simulator/device
- An Expo account for EAS cloud builds

From the mobile directory:

    npm install
    npm run typecheck
    npx expo start

Test login, registration, chat, dashboard, conversations, settings save, and logout on a real Android device and an iPhone before publishing.

## Production builds

EAS Build is already configured:

    npm run build:android
    npm run build:ios

The production Android profile creates an Android App Bundle suitable for Google Play. The production iOS profile creates an iOS build suitable for App Store Connect.

For store submission:

    npm run submit:android
    npm run submit:ios

The first EAS setup will ask you to authenticate with Expo and configure the native signing credentials. Do not commit signing keys or service-account JSON files to this repository.

## App identity

- App name: Nova AI
- Android package: ai.nova.tutor
- iOS bundle identifier: ai.nova.tutor
- URL scheme: nova
- Production API: https://nova-api-i07q.onrender.com

## Store checklist

Before publishing, complete:
1. App icon and splash assets in the Expo app configuration.
2. Privacy policy URL and support/contact URL.
3. App Store Connect product page, age rating, screenshots, keywords, and review notes.
4. Google Play Console store listing, Data safety form, content rating, target audience, privacy policy, and review access.
5. Test login, registration, chat, conversation history, dashboard, settings persistence, logout, offline/error states, and account deletion flows on physical devices.
6. Verify that the production backend is healthy before starting a store build.

## Important

The mobile app is intentionally separate from the existing Vite website. Changes here do not require replacing the working web UI. The mobile client uses SecureStore for its session token and talks directly to the production API.
