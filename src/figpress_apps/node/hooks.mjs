// Module resolve hook for `figpress-apps test`: prefix → folder, loaded as ES modules.
import { pathToFileURL } from "node:url";
import { join } from "node:path";

let roots = {};
export async function initialize(data) { roots = data; }
export async function resolve(specifier, context, next) {
  for (const [prefix, dir] of Object.entries(roots)) {
    if (specifier.startsWith(prefix)) {
      return { url: pathToFileURL(join(dir, specifier.slice(prefix.length))).href, format: "module", shortCircuit: true };
    }
  }
  return next(specifier, context);
}
