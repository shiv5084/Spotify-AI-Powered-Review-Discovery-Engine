import React from 'react';
import { Barrier } from '../../lib/types';
import MetricCard from './MetricCard';
import styles from '../../styles/dashboard.module.css';

interface FrustrationsSectionProps {
  frustrations: Barrier[];
}

export default function FrustrationsSection({ frustrations }: FrustrationsSectionProps) {
  const hasData = frustrations && frustrations.length > 0;

  return (
    <section id="frustrations" className={styles.gridSection}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            <span className={styles.sectionTitleIcon}>😤</span>
            2. Top 3 Recommendation Frustrations
          </h2>
          <p className={styles.sectionSubtitle}>
            Specific complaints about recommendation accuracy, repetitive songs, or algorithmic loops.
          </p>
        </div>
      </div>

      {hasData ? (
        <div className={styles.cardGrid}>
          {frustrations.slice(0, 3).map((item, index) => (
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
          <div className={styles.emptyStateIcon}>🎧</div>
          <p>No recommendation frustrations identified in this batch.</p>
        </div>
      )}
    </section>
  );
}
