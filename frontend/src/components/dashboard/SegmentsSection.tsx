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
          {segments.slice(0, 3).map((item, index) => {
            const rank = item.severity_rank ?? (index + 1);
            const score = item.severity_score ?? 0;
            const badgeClass =
              rank === 1 ? styles.severityBadgeRank1 :
              rank === 2 ? styles.severityBadgeRank2 :
              styles.severityBadgeRank3;
            const barClass =
              rank === 1 ? styles.severityBarRank1 :
              rank === 2 ? styles.severityBarRank2 :
              styles.severityBarRank3;
            // Assuming max severity score is around 5
            const barWidth = Math.min(100, Math.max(0, score * 20));

            return (
              <MetricCard
                key={index}
                title={item.segment}
                count={item.count}
                frequency={item.frequency}
                averageRating={item.average_rating}
              >
                {(item.severity_score !== undefined || item.severity_rank !== undefined) && (
                  <div className={styles.severityBlock}>
                    <div className={styles.severityHeader}>
                      <span className={`${styles.severityBadge} ${badgeClass}`}>
                        Severity Rank #{rank}
                      </span>
                      <span className={styles.severityScoreLabel}>
                        Severity Score: <strong className={styles.severityScoreValue}>{score.toFixed(2)}</strong>
                      </span>
                    </div>
                    <div className={styles.severityBarContainer}>
                      <div
                        className={`${styles.severityBarFill} ${barClass}`}
                        style={{ width: `${barWidth}%` }}
                      />
                    </div>
                  </div>
                )}

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
            );
          })}
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
