Vendored widget code, served from our own origin so the page calls no third party except the CAPTCHA vendors
themselves (Google reCAPTCHA, Cloudflare Turnstile). Fetched with `npm pack` on 2026-11-03; versions in the names.

| File | Package | Licence |
|---|---|---|
| altcha-3.5.0.min.js | altcha 3.5.0 (`dist/main/altcha.min.js`, workers and styles bundled) | MIT, altcha-LICENSE.txt |
| botd-2.0.0.esm.js | @fingerprintjs/botd 2.0.0 (`dist/botd.esm.js`), loaded with `monitoring: false` | MIT, botd-LICENSE.txt |
| cap-widget-0.1.58.min.js | @cap.js/widget 0.1.58 (`cap.min.js`, classic script, defines `<cap-widget>`) | Apache-2.0, cap-LICENSE.txt |
| cap-wasm-0.0.8.wasm, cap-hashwx-0.0.8.wasm | @cap.js/wasm 0.0.8 (`browser/cap_wasm_bg.wasm`, `browser/hashwx.wasm`), the version the widget pins; set through `CAP_CUSTOM_WASM_URL` / `CAP_CUSTOM_HASHWX_URL` | Apache-2.0, cap-LICENSE.txt (same author and licence) |
