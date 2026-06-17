export interface Barrier {
  theme: string;
  frequency: number;
  count: number;
  average_rating: number;
}

export interface ListeningGoal {
  theme: string;
  frequency: number;
  count: number;
  average_rating: number;
  jtbd?: string;
}

export interface DiscoveryChallenge {
  pain_point: string;
  count: number;
  frequency_within_segment: number;
}

export interface UnderservedSegment {
  segment: string;
  frequency: number;
  count: number;
  average_rating: number;
  severity_score?: number;
  severity_rank?: number;
  discovery_challenges?: DiscoveryChallenge[];
}

export interface UnmetNeed {
  need?: string;
  theme?: string;
  frequency: number;
  count: number;
  average_rating: number;
  opportunity_score: number;
}

export interface Opportunity {
  problem: string;
  evidence: string;
  suggested_ai_solution: string;
  expected_impact: string;
}

export interface SentimentDistribution {
  positive: number;
  neutral: number;
  negative: number;
  total: number;
}

export interface DashboardMetrics {
  top_barriers: Barrier[];
  top_frustrations: Barrier[];
  listening_goals: ListeningGoal[];
  repeat_drivers: Barrier[];
  underserved_segments: UnderservedSegment[];
  unmet_needs: UnmetNeed[];
  opportunities: Opportunity[];
}

export interface DashboardData {
  week_ending: string;
  pulse_note_text: string;
  sentiment_distribution?: SentimentDistribution;
  metrics: DashboardMetrics;
}
