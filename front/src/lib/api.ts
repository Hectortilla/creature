import { PUBLIC_API_URL } from '$env/static/public';
import { client } from './api/client.gen';

// Configure the API client with the base URL from environment
export function configureApiClient(baseUrl: string = PUBLIC_API_URL) {
	client.setConfig({
		baseUrl,
	});
}

// Initialize with default config
configureApiClient();

// Re-export everything from the generated SDK
export * from './api/sdk.gen';
export * from './api/types.gen';
