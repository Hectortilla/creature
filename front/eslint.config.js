import prettier from "eslint-config-prettier";
import { includeIgnoreFile } from "@eslint/compat";
import js from "@eslint/js";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import { fileURLToPath } from "node:url";
import ts from "typescript-eslint";
import svelteConfig from "./svelte.config.js";

const gitignorePath = fileURLToPath(new URL("./.gitignore", import.meta.url));

export default ts.config(
	includeIgnoreFile(gitignorePath),
	{
		// Generated code is owned by the generators (`npm run generate`), never
		// hand-edited — mirror the .prettierignore exclusions so lint skips it too.
		ignores: [
			"src/lib/api/*.gen.ts",
			"src/lib/api/client/**",
			"src/lib/api/core/**",
			"src/lib/utils/generated/**",
		],
	},
	js.configs.recommended,
	...ts.configs.recommended,
	...svelte.configs.recommended,
	prettier,
	...svelte.configs.prettier,
	{
		languageOptions: {
			globals: { ...globals.browser, ...globals.node },
		},
		rules: {
			// typescript-eslint strongly recommend that you do not use the no-undef lint rule on TypeScript projects.
			// see: https://typescript-eslint.io/troubleshooting/faqs/eslint/#i-get-errors-from-the-no-undef-rule-about-global-variables-not-being-defined-even-though-there-are-no-typescript-errors
			"no-undef": "off",
			// Allow intentionally-unused names when prefixed with _ (e.g. interface-
			// mandated params), the standard convention.
			"@typescript-eslint/no-unused-vars": [
				"error",
				{
					argsIgnorePattern: "^_",
					varsIgnorePattern: "^_",
					caughtErrorsIgnorePattern: "^_",
				},
			],
			// Pre-existing-debt ratchet (see docs/harness.md): these high-volume findings
			// in app/legacy code need per-case judgment (trusted-HTML decisions, unique
			// keys, real types, route resolution). Keep them visible as warnings so
			// `npm run lint` gates on *errors* — i.e. blocks new error-level violations —
			// while this backlog is worked down. Do not add new occurrences.
			"svelte/no-at-html-tags": "warn",
			"svelte/require-each-key": "warn",
			"@typescript-eslint/no-explicit-any": "warn",
			"svelte/no-navigation-without-resolve": "warn",
			"svelte/prefer-writable-derived": "warn",
			"svelte/prefer-svelte-reactivity": "warn",
		},
	},
	{
		files: ["**/*.svelte", "**/*.svelte.ts", "**/*.svelte.js"],
		languageOptions: {
			parserOptions: {
				projectService: true,
				extraFileExtensions: [".svelte"],
				parser: ts.parser,
				svelteConfig,
			},
		},
	},
);
