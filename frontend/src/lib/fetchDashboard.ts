import fs from 'fs';
import path from 'path';
import { DashboardData } from './types';

export async function fetchDashboard(): Promise<DashboardData> {
  if (typeof window === 'undefined') {
    // ── Server-side path resolution ───────────────────────────────────────
    // On Vercel: process.cwd() = /var/task
    //   public/ files are bundled at /var/task/public/  ← check here first
    //   ../data/ does NOT exist on Vercel               ← local dev only

    // ① Local dev fallback: ../data/dashboard_data.json (relative to frontend/)
    const dataPath = process.env.DASHBOARD_DATA_PATH || '../data/dashboard_data.json';
    const localPath = path.resolve(process.cwd(), dataPath);
    if (fs.existsSync(localPath)) {
      const raw = fs.readFileSync(localPath, 'utf-8');
      return JSON.parse(raw) as DashboardData;
    }

    // ② Vercel-compatible: public/dashboard_data.json
    const publicPath = path.join(process.cwd(), 'public', 'dashboard_data.json');
    if (fs.existsSync(publicPath)) {
      const raw = fs.readFileSync(publicPath, 'utf-8');
      return JSON.parse(raw) as DashboardData;
    }

    // ③ Neither location has the file
    throw new Error(
      `Dashboard data not found. Checked:\n  (1) ${publicPath}\n  (2) ${localPath}`
    );
  } else {
    // Client-side: call the Next.js API route which has its own fallback chain
    const res = await fetch('/api/dashboard');
    if (!res.ok) {
      throw new Error('Failed to fetch dashboard data from /api/dashboard');
    }
    return res.json() as Promise<DashboardData>;
  }
}
