export function formatHandle(name: string | number): string {
    if (typeof name === 'number') {
        return name.toString();
    }
    return name
        .normalize('NFD')                 // separa los acentos
        .replace(/[\u0300-\u036f]/g, '')  // elimina acentos
        .toLowerCase()                    // convierte a minúsculas
        .replace(/\s+/g, '-')             // reemplaza espacios por guiones
        .replace(/[^a-z0-9-]/g, '');     // elimina caracteres especiales
}