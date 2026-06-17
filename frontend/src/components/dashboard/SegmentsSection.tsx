import React from 'react';
import { UnderservedSegment } from '../../lib/types';
import MetricCard from './MetricCard';
import styles from '../../styles/dashboard.module.css';

interface SegmentsSectionProps {
  segments: UnderservedSegment[];
}

export default function SegmentsSection({ segments }: SegmentsSectionProps) {
  const hasData = segments && segments.length > 0;

  return (
    <section id="segments" className={styles.gridSection}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            <span className={styles.sectionTitleIcon}>👥</span>
            5. Top 3 Underserved User Segments
          </h2>
          <p className={styles.sectionSubtitle}>
            Groups of users experiencing disproportionate friction — with their primary discovery challenges.
          </p>
        </div>
      </div>

      {hasData ? (
        <div className={styles.cardGrid}>
          {segments.slice(0, 3).map((item, index) => (
            <MetricCard
              key={index}
              title={item.segment}
              count={item.count}
              frequency={item.frequency}
              averageRating={item.average_rating}
            >
              {item.discovery_challenges && item.discovery_challenges.length > 0 && (
                <div className={styles.discoveryChallengesBlock}>
                  <div className={styles.discoveryChallengesLabel}>
                    🔍 Top Discovery Challenges
                  </div>
                  {item.discovery_challenges.slice(0, 3).map((challenge, cIdx) => {
                    const pct = Math.min(100, Math.max(0, challenge.frequency_within_segment * 100));
                    return (
                      <div key={cIdx} className={styles.challengeRow}>
                        <div className={styles.challengeLabelRow}>
                          <span className={styles.challengeRank}>#{cIdx + 1}</span>
                          <span className={styles.challengeName}>{challenge.pain_point}</span>
                          <span className={styles.challengeFreq}>
                            {(challenge.frequency_within_segment * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className={styles.challengeBarContainer}>
                          <div
                            className={styles.challengeBarFill}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </MetricCard>
          ))}
        </div>
      ) : (
        <div className={styles.emptyState}>
          <div className={styles.emptyStateIcon}>👥</div>
          <p>No underserved user segments identified in this batch.</p>
        </div>
      )}
    </section>
  );
}
