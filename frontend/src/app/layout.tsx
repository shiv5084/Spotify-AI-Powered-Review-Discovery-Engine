import type { Metadata } from 'next';
import './globals.css';
import Navbar from '../components/layout/Navbar';
import Sidebar from '../components/layout/Sidebar';
import { fetchDashboard } from '../lib/fetchDashboard';

export const metadata: Metadata = {
  title: 'Spotify PRDE — Review Discovery Engine Dashboard',
  description: 'AI-Powered review theme extraction, analysis, and discovery engine dashboard.',
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  let weekEnding = 'N/A';
  
  try {
    const data = await fetchDashboard();
    weekEnding = data.week_ending;
  } catch (error: any) {
    if (error.message && error.message.includes('Dynamic server usage')) {
      throw error;
    }
    console.error('Error fetching data in root layout:', error);
  }

  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body>
        <Navbar weekEnding={weekEnding} />
        <div style={{ display: 'flex' }}>
          <Sidebar />
          <main style={{
            marginLeft: 'var(--sidebar-width)',
            marginTop: 'var(--navbar-height)',
            width: 'calc(100% - var(--sidebar-width))',
            padding: '2rem 2.5rem',
            minHeight: 'calc(100vh - var(--navbar-height))',
            boxSizing: 'border-box'
          }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
