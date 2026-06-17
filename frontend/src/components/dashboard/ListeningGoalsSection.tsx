import React from 'react';
import { ListeningGoal } from '../../lib/types';
import MetricCard from './MetricCard';
import styles from '../../styles/dashboard.module.css';

interface ListeningGoalsSectionProps {
  goals: ListeningGoal[];
}

export default function ListeningGoalsSection({ goals }: ListeningGoalsSectionProps) {
  const hasData = goals && goals.length > 0;

  return (
    <section id="goals" className={styles.gridSection}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            <span className={styles.sectionTitleIcon}>🎯</span>
            3. Top 3 Listening Goals & Intentions
          </h2>
          <p className={styles.sectionSubtitle}>
            Core contexts and use-cases users are trying to satisfy with Spotify discovery.
          </p>
        </div>
      </div>

      {hasData ? (
        <div className={styles.cardGrid}>
          {goals.slice(0, 3).map((item, index) => (
            <MetricCard
              key={index}
              title={item.theme}
              count={item.count}
              frequency={item.frequency}
              averageRating={item.average_rating}
            >
              {item.jtbd && (
                <div className={styles.jtbdBlock}>
                  <strong>JTBD:</strong> &ldquo;{item.jtbd}&rdquo;
                </div>
              )}
            </MetricCard>
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyStateIcon}>🚀</div>
          <p>No listening goals identified in this batch.</p>
        </div>
      )}
    </section>
  );
}
