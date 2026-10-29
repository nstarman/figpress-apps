// Node-only test tooling (not shipped to browsers): resolve figpress-apps' bare specifiers
// (figpress-apps/…, app/…) the way a built page's import map does. Used by `figpress-apps test`.
import { register } from "node:module";

register(new URL("./hooks.mjs", import.meta.url), { data: JSON.parse(process.env.FIGPRESS_APPS_ROOTS ?? "{}") });
