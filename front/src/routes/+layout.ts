import type { LayoutLoad } from "./$types";

export const load: LayoutLoad = async ({ url }) => {
	// Route protection is handled by hooks.server.ts
	// This load function provides the pathname to the layout
	return {
		pathname: url.pathname,
	};
};
