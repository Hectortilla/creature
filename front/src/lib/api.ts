import { client } from './api/client.gen';

// Configure the API client with the base URL
export function configureApiClient(baseUrl: string = 'http://localhost:8000') {
	client.setConfig({
		baseUrl,
	});
}

// Initialize with default config
configureApiClient();

// Re-export everything from the generated SDK
export * from './api/sdk.gen';
export * from './api/types.gen';

