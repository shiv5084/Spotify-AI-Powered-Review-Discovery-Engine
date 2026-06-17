import React from 'react';
import { fetchDashboard } from '../../lib/fetchDashboard';
import PulseNoteViewer from '../../components/pulse/PulseNoteViewer';
import styles from '../../styles/dashboard.module.css';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default async function PulseNotePage() {
  let data;
  let errorMsg = null;

  try {
    data = await fetchDashboard();
  } catch (error: any) {
    console.error('Error fetching data for pulse note:', error);
    errorMsg = error.message || 'Unknown error occurred.';
  }

  if (errorMsg || !data) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.emptyState}>
          <div className={styles.emptyStateIcon}>⚠️</div>
          <p>Error loading pulse note: {errorMsg || 'Data file not found.'}</p>
        </div>
      </div>
    );
  }

  return (
    <PulseNoteViewer 
      pulseNoteText={data.pulse_note_text} 
      weekEnding={data.week_ending} 
    />
  );
}
