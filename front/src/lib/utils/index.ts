import { browser } from "$app/environment";

export function shouldPersist(): boolean {
	// TODO: Implement ETag
	return browser && import.meta.env.PROD;
}
