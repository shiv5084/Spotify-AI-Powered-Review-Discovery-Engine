import React from 'react';
import { Barrier } from '../../lib/types';
import MetricCard from './MetricCard';
import styles from '../../styles/dashboard.module.css';

interface BarriersSectionProps {
  barriers: Barrier[];
}

export default function BarriersSection({ barriers }: BarriersSectionProps) {
  const hasData = barriers && barriers.length > 0;

  return (
    <section id="barriers" className={styles.gridSection}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            <span className={styles.sectionTitleIcon}>🛑</span>
            1. Top 3 Discovery Barriers
          </h2>
          <p className={styles.sectionSubtitle}>
            Issues preventing users from discovering new content or using discovery features.
          </p>
        </div>
      </div>

      {hasData ? (
        <div className={styles.cardGrid}>
          {barriers.slice(0, 3).map((item, index) => (
            <MetricCard
              key={index}
              title={item.theme}
              count={item.count}
              frequency={item.frequency}
              averageRating={item.average_rating}
            />
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyStateIcon}>🔍</div>
          <p>No discovery barriers identified in this batch.</p>
        </div>
      )}
    </section>
  );
}
