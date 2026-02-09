/**
 * Helpers para formato de archivo y aceptación según URL (from/to).
 * Usado por useFileSelection y Convert.
 */
const IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg'];

export function extensionMatchesUrlFrom(ext: string, urlFrom: string): boolean {
    if (urlFrom === 'png') return IMAGE_EXTENSIONS.includes(ext);
    return ext === urlFrom;
}

export function getAcceptForUrlFrom(urlFrom: string): string {
    if (!urlFrom) return '';
    if (urlFrom === 'png' || urlFrom === 'jpg' || urlFrom === 'jpeg') return '.png,.jpg,.jpeg';
    if (urlFrom === 'htm') return '.htm,.html';
    if (urlFrom === 'html') return '.html,.htm';
    return `.${urlFrom}`;
}
