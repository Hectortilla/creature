export function formatHandle(name: string | number | null | undefined): string {
	if (name == null) return "";

	const str = String(name);

	let normalized = str;
	if (normalized.normalize) {
		normalized = normalized.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
	}

	return normalized
		.toLowerCase()
		.replace(/\s+/g, "-")
		.replace(/[^a-z0-9-]/g, "");
}
