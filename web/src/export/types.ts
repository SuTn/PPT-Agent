export interface DomToPptxOptions {
  renderMode: 'dom' | 'image';
  fileName?: string;
  autoEmbedFonts?: boolean;
  slideNotes?: string[];
  skipDownload?: boolean;
  imageScale?: number;
  imageType?: 'png' | 'jpeg';
  signal?: AbortSignal;
  shouldCancel?: () => boolean;
}

export interface DomToPptxApi {
  exportToPptx(
    target: HTMLElement | HTMLElement[] | AsyncIterable<HTMLElement>,
    options: DomToPptxOptions
  ): Promise<Blob>;
  setIconRules?: (rules: unknown) => void;
  getIconRules?: () => unknown;
}

declare global {
  interface Window {
    domToPptx: DomToPptxApi;
  }
}
