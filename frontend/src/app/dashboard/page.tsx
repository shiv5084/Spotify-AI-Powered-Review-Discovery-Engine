import React from 'react';
import { fetchDashboard } from '../../lib/fetchDashboard';
import SentimentSummary from '../../components/dashboard/SentimentSummary';
import BarriersSection from '../../components/dashboard/BarriersSection';
import FrustrationsSection from '../../components/dashboard/FrustrationsSection';
import ListeningGoalsSection from '../../components/dashboard/ListeningGoalsSection';
import RepeatDriversSection from '../../components/dashboard/RepeatDriversSection';
import SegmentsSection from '../../components/dashboard/SegmentsSection';
import UnmetNeedsSection from '../../components/dashboard/UnmetNeedsSection';
import OpportunitiesSection from '../../components/dashboard/OpportunitiesSection';
import styles from '../../styles/dashboard.module.css';

// Force dynamic rendering to always load the latest dashboard_data.json on page request
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default async function DashboardPage() {
  let data;
  let errorMsg = null;

  try {
    data = await fetchDashboard();
  } catch (error: any) {
    console.error('Error fetching dashboard data:', error);
    errorMsg = error.message || 'Unknown error occurred while loading dashboard data.';
  }

  if (errorMsg || !data) {
    return (
      <div className={styles.dashboardContainer}>
        <div className={styles.headerSection}>
          <h1 className={styles.pageTitle}>Executive Review Discovery Dashboard</h1>
          <p className={styles.pageSubtitle}>Unable to load dashboard data.</p>
        </div>
        <div className={styles.emptyState}>
          <div className={styles.emptyStateIcon}>⚠️</div>
          <p>Error loading dashboard metrics: {errorMsg || 'Data file not found.'}</p>
          <p style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
            Please ensure you have executed the Python pipeline to generate the data: <code>python main.py</code>
          </p>
        </div>
      </div>
    );
  }

  const { metrics } = data;

  return (
    <div className={styles.dashboardContainer}>
      <div className={styles.headerSection}>
        <h1 className={styles.pageTitle}>Executive Review Discovery Dashboard</h1>
        <p className={styles.pageSubtitle}>
          Weekly aggregated insights and AI-discovered opportunities from Spotify user feedback.
        </p>
      </div>

      <SentimentSummary distribution={data.sentiment_distribution} />

      <BarriersSection barriers={metrics.top_barriers || []} />
      <FrustrationsSection frustrations={metrics.top_frustrations || []} />
      <ListeningGoalsSection goals={metrics.listening_goals || []} />
      <RepeatDriversSection drivers={metrics.repeat_drivers || []} />
      <SegmentsSection segments={metrics.underserved_segments || []} />
      <UnmetNeedsSection needs={metrics.unmet_needs || []} />
      <OpportunitiesSection opportunities={metrics.opportunities || []} />
    </div>
  );
}
