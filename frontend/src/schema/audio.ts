export interface Audio {
    id?: number;
    title?: string;
    info?: string;
    uploaded_date?: string;
    transcript: Record<string, any>;
    term: Record<string, any>;
}