# Nova logo

Place the final Nova logo here as:

- `nova-logo.svg` for the primary vector logo.

The application references it through `src/config/brand.js`:

```js
logo: "/brand/nova-logo.svg"
```

Do not hard-code logo paths in individual components. Import `NOVA_BRAND` from the brand configuration so changing the logo updates every connected surface consistently.
