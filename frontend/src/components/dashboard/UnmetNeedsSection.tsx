import React from 'react';
import { UnmetNeed } from '../../lib/types';
import MetricCard from './MetricCard';
import styles from '../../styles/dashboard.module.css';

interface UnmetNeedsSectionProps {
  needs: UnmetNeed[];
}

export default function UnmetNeedsSection({ needs }: UnmetNeedsSectionProps) {
  const hasData = needs && needs.length > 0;

  return (
    <section id="unmet-needs" className={styles.gridSection}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            <span className={styles.sectionTitleIcon}>💡</span>
            6. Top 3 Unmet Needs
          </h2>
          <p className={styles.sectionSubtitle}>
            High-opportunity areas where customer needs are not currently satisfied by existing features.
          </p>
        </div>
      </div>

      {hasData ? (
        <div className={styles.cardGrid}>
          {needs.slice(0, 3).map((item, index) => {
            // Assume 1.0 is the maximum opportunity score (since mock data shows 0.25, 0.15, etc.)
            // If some scores are greater than 1, clamp/handle gracefully
            const displayPercentage = Math.min(100, Math.max(0, item.opportunity_score * 100));

            return (
              <MetricCard
                key={index}
                title={item.theme || item.need || ''}
                count={item.count}
                frequency={item.frequency}
                averageRating={item.average_rating}
              >
                <div className={styles.oppScoreBlock}>
                  <div className={styles.oppScoreLabelRow}>
                    <span>Opportunity Score</span>
                    <span style={{ color: 'var(--primary)' }}>{item.opportunity_score.toFixed(2)}</span>
                  </div>
                  <div className={styles.oppScoreBarContainer}>
                    <div 
                      className={styles.oppScoreBarFill} 
                      style={{ width: `${displayPercentage}%` }}
                    />
                  </div>
                </div>
              </MetricCard>
            );
          })}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyStateIcon}>💡</div>
          <p>No unmet needs identified in this batch.</p>
        </div>
      )}
    </section>
  );
}
