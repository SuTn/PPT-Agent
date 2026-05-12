import type { SlideInfo } from '../api/types';
import './types';

let loadPromise: Promise<void> | null = null;

function loadBundle(): Promise<void> {
  if (window.domToPptx) return Promise.resolve();
  if (loadPromise) return loadPromise;

  loadPromise = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script');
    script.src = '/dom-to-pptx.bundle.js';
    script.onload = () => {
      if (window.domToPptx) {
        resolve();
      } else {
        reject(new Error('dom-to-pptx bundle loaded but window.domToPptx not found'));
      }
    };
    script.onerror = () => reject(new Error('Failed to load dom-to-pptx bundle'));
    document.head.appendChild(script);
  });

  return loadPromise;
}

async function waitForIframeReady(iframe: HTMLIFrameElement): Promise<void> {
  const doc = iframe.contentDocument!;
  if (doc.readyState !== 'complete' && doc.readyState !== 'interactive') {
    await new Promise<void>(resolve => {
      doc.addEventListener('DOMContentLoaded', () => resolve());
    });
  }
  if (doc.fonts) {
    await doc.fonts.ready;
  }
  await new Promise(resolve => requestAnimationFrame(resolve));
  await new Promise(resolve => setTimeout(resolve, 100));
}

function extractSpeakerNotes(html: string): string {
  const match = html.match(/<!--\s*speaker_notes:\s*([\s\S]*?)\s*-->/);
  return match ? match[1].trim() : '';
}

export async function exportEditablePptx(
  sessionId: string,
  slides: SlideInfo[],
  fileName: string,
  onProgress?: (msg: string) => void
): Promise<void> {
  await loadBundle();

  const bodies: HTMLElement[] = [];
  const notes: string[] = [];
  const iframes: HTMLIFrameElement[] = [];

  try {
    for (let i = 0; i < slides.length; i++) {
      const slide = slides[i];
      if (!slide.filename) continue;

      onProgress?.(`正在导出 ${i + 1}/${slides.length}...`);

      const resp = await fetch(`/api/v1/sessions/${sessionId}/slides/${slide.filename}`);
      const html = await resp.text();
      notes.push(extractSpeakerNotes(html));

      const iframe = document.createElement('iframe');
      iframe.style.cssText = 'position:fixed;left:-9999px;top:-9999px;width:1280px;height:720px;border:none;opacity:0;pointer-events:none;';
      document.body.appendChild(iframe);

      iframe.contentDocument!.open();
      iframe.contentDocument!.write(html);
      iframe.contentDocument!.close();

      await waitForIframeReady(iframe);

      bodies.push(iframe.contentDocument!.body);
      iframes.push(iframe);
    }

    onProgress?.('正在生成 PPTX 文件...');

    const blob = await window.domToPptx.exportToPptx(bodies, {
      renderMode: 'dom',
      fileName: `${fileName}.pptx`,
      autoEmbedFonts: true,
      slideNotes: notes,
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${fileName}.pptx`;
    a.click();
    URL.revokeObjectURL(url);
  } finally {
    for (const iframe of iframes) {
      iframe.remove();
    }
  }
}
