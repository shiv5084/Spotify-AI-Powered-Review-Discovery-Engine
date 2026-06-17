import React from 'react';
import { Barrier } from '../../lib/types';
import MetricCard from './MetricCard';
import styles from '../../styles/dashboard.module.css';

interface RepeatDriversSectionProps {
  drivers: Barrier[];
}

export default function RepeatDriversSection({ drivers }: RepeatDriversSectionProps) {
  const hasData = drivers && drivers.length > 0;

  return (
    <section id="drivers" className={styles.gridSection}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            <span className={styles.sectionTitleIcon}>🔄</span>
            4. Top 3 Repeat-Listening Drivers
          </h2>
          <p className={styles.sectionSubtitle}>
            Features, content, or experiences that drive habitual, repeat-listening behaviors.
          </p>
        </div>
      </div>

      {hasData ? (
        <div className={styles.cardGrid}>
          {drivers.slice(0, 3).map((item, index) => (
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
          <div className={styles.emptyStateIcon}>🔁</div>
          <p>No repeat-listening drivers identified in this batch.</p>
        </div>
      )}
    </section>
  );
}
