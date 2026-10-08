'use client';

import { useEffect, useRef, useState } from 'react';

declare global {
  interface Window {
    // Chart.js, loaded from the same CDN URL the templates used.
    Chart?: new (context: CanvasRenderingContext2D, config: unknown) => { destroy(): void };
  }
}

const CHART_JS_URL = 'https://cdn.jsdelivr.net/npm/chart.js';
let chartJsLoading: Promise<void> | null = null;

/** Adds the Chart.js <script> once, however many charts a page shows. */
function loadChartJs(): Promise<void> {
  if (window.Chart) return Promise.resolve();
  chartJsLoading ??= new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = CHART_JS_URL;
    script.onload = () => resolve();
    script.onerror = () => {
      chartJsLoading = null;
      reject(new Error('Chart.js failed to load'));
    };
    document.body.appendChild(script);
  });
  return chartJsLoading;
}

interface ChartCanvasProps {
  id: string;
  height: number;
  /** The exact configuration object the template passed to `new Chart(...)`. */
  config: Record<string, unknown>;
}

/** A `<canvas>` drawn by Chart.js, as in the templates' {% block scripts %}. */
export function ChartCanvas({ id, height, config }: ChartCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [ready, setReady] = useState(false);
  const serialized = JSON.stringify(config);

  useEffect(() => {
    let cancelled = false;
    loadChartJs().then(() => !cancelled && setReady(true), () => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const context = canvasRef.current?.getContext('2d');
    if (!ready || !context || !window.Chart) return;
    const chart = new window.Chart(context, JSON.parse(serialized));
    return () => chart.destroy();
  }, [ready, serialized]);

  return <canvas id={id} height={height} ref={canvasRef}></canvas>;
}
