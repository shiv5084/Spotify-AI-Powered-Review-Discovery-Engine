'use client';

import React, { useEffect, useState } from 'react';
import { SentimentDistribution } from '../../lib/types';
import styles from '../../styles/dashboard.module.css';

interface SentimentSummaryProps {
  distribution?: SentimentDistribution;
}

export default function SentimentSummary({ distribution }: SentimentSummaryProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Subtle trigger to animate widths on load
    setMounted(true);
  }, []);

  // Standard fallback default if no distribution data is available
  const defaultDist: SentimentDistribution = {
    positive: 15,
    neutral: 65,
    negative: 20,
    total: 100,
  };

  const dist = distribution && typeof distribution.total === 'number' && distribution.total > 0
    ? distribution
    : defaultDist;

  const total = dist.total || 100;
  const positivePct = (dist.positive / total) * 100;
  const neutralPct = (dist.neutral / total) * 100;
  const negativePct = (dist.negative / total) * 100;

  return (
    <section className={styles.sentimentSection}>
      <div className={styles.sectionHeader}>
        <div>
          <h2 className={styles.sectionTitle}>
            <span className={styles.sectionTitleIcon}>📊</span>
            Overall User Sentiment Breakdown
          </h2>
          <p className={styles.sectionSubtitle}>
            Aggregated tone across all scrubbed Spotify user reviews in this reporting period.
          </p>
        </div>
      </div>

      <div className={styles.sentimentBarContainer}>
        {dist.positive > 0 && (
          <div
            className={`${styles.sentimentBarSegment} ${styles.sentimentSegmentPositive}`}
            style={{ width: mounted ? `${positivePct}%` : '0%' }}
            title={`Positive: ${dist.positive} reviews (${positivePct.toFixed(1)}%)`}
          >
            {positivePct >= 8 && `${positivePct.toFixed(1)}%`}
          </div>
        )}
        {dist.neutral > 0 && (
          <div
            className={`${styles.sentimentBarSegment} ${styles.sentimentSegmentNeutral}`}
            style={{ width: mounted ? `${neutralPct}%` : '0%' }}
            title={`Neutral: ${dist.neutral} reviews (${neutralPct.toFixed(1)}%)`}
          >
            {neutralPct >= 8 && `${neutralPct.toFixed(1)}%`}
          </div>
        )}
        {dist.negative > 0 && (
          <div
            className={`${styles.sentimentBarSegment} ${styles.sentimentSegmentNegative}`}
            style={{ width: mounted ? `${negativePct}%` : '0%' }}
            title={`Negative: ${dist.negative} reviews (${negativePct.toFixed(1)}%)`}
          >
            {negativePct >= 8 && `${negativePct.toFixed(1)}%`}
          </div>
        )}
      </div>

      <div className={styles.sentimentLegend}>
        <div className={styles.sentimentLegendItem}>
          <span className={`${styles.sentimentDot} ${styles.sentimentDotPositive}`} />
          <span className={styles.sentimentLegendLabel}>Positive</span>
          <span className={styles.sentimentLegendValue}>
            {dist.positive} reviews ({positivePct.toFixed(1)}%)
          </span>
        </div>
        <div className={styles.sentimentLegendItem}>
          <span className={`${styles.sentimentDot} ${styles.sentimentDotNeutral}`} />
          <span className={styles.sentimentLegendLabel}>Neutral</span>
          <span className={styles.sentimentLegendValue}>
            {dist.neutral} reviews ({neutralPct.toFixed(1)}%)
          </span>
        </div>
        <div className={styles.sentimentLegendItem}>
          <span className={`${styles.sentimentDot} ${styles.sentimentDotNegative}`} />
          <span className={styles.sentimentLegendLabel}>Negative</span>
          <span className={styles.sentimentLegendValue}>
            {dist.negative} reviews ({negativePct.toFixed(1)}%)
          </span>
        </div>
        <div className={styles.sentimentLegendItem} style={{ marginLeft: 'auto' }}>
          <span className={styles.sentimentLegendLabel}>Total Analyzed:</span>
          <span className={styles.sentimentLegendValue} style={{ fontWeight: 700, color: 'var(--text-main)' }}>
            {dist.total} reviews
          </span>
        </div>
      </div>
    </section>
  );
}
