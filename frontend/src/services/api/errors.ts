/**
 * Error tipo API: permite mostrar el mensaje de detalle que devuelve el backend.
 */
export class ApiError extends Error {
    constructor(
        message: string,
        public readonly statusCode: number,
        public readonly detail: string
    ) {
        super(message);
        this.name = 'ApiError';
        Object.setPrototypeOf(this, ApiError.prototype);
    }
}

/**
 * Parsea la respuesta de error del backend (JSON con detail o texto plano) y lanza ApiError.
 */
export async function apiErrorFromResponse(response: Response, fallbackMessage = 'Request failed'): Promise<never> {
    const text = await response.text();
    let detail = fallbackMessage;
    try {
        const data = text ? JSON.parse(text) : {};
        if (data.detail != null) {
            detail = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail)
                ? data.detail.map((x: { msg?: string }) => x.msg || JSON.stringify(x)).join(', ')
                : JSON.stringify(data.detail);
        }
    } catch {
        if (text) detail = text;
    }
    throw new ApiError(detail, response.status, detail);
}
