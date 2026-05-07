-- Multimodal Drone Detection Database Schema
-- The database 'drone_detection' is automatically created by POSTGRES_DB env variable

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create incidents table
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id VARCHAR(80) NOT NULL UNIQUE,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_timestamp DOUBLE PRECISION NOT NULL,
    has_drone BOOLEAN NOT NULL,
    decision VARCHAR(10) NOT NULL,
    confidence_band VARCHAR(10) NOT NULL,
    alert_level VARCHAR(10) NOT NULL,
    is_confirmed BOOLEAN NOT NULL,
    fused_confidence DOUBLE PRECISION NOT NULL CHECK (fused_confidence >= 0 AND fused_confidence <= 1),
    stream_name VARCHAR(100) NOT NULL,
    primary_frame_url TEXT,
    primary_thumbnail_url TEXT,
    per_modality_scores JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    gating_reason TEXT NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL CHECK (latency_ms >= 0),
    evidence JSONB NOT NULL,
    media JSONB NOT NULL,
    objects JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common incident queries
CREATE INDEX idx_incidents_incident_id ON incidents(incident_id);
CREATE INDEX idx_incidents_detected_at ON incidents(detected_at DESC);
CREATE INDEX idx_incidents_decision ON incidents(decision);
CREATE INDEX idx_incidents_stream_name ON incidents(stream_name);

-- Create aggregated incident table for event-level views
CREATE TABLE IF NOT EXISTS incident_aggregates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    aggregate_id VARCHAR(80) NOT NULL UNIQUE,
    stream_name VARCHAR(100) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    decision VARCHAR(10) NOT NULL,
    has_drone BOOLEAN NOT NULL,
    confidence_band VARCHAR(10) NOT NULL,
    alert_level VARCHAR(10) NOT NULL,
    is_confirmed BOOLEAN NOT NULL,
    fused_confidence DOUBLE PRECISION NOT NULL CHECK (fused_confidence >= 0 AND fused_confidence <= 1),
    avg_fused_confidence DOUBLE PRECISION NOT NULL CHECK (avg_fused_confidence >= 0 AND avg_fused_confidence <= 1),
    frame_count INTEGER NOT NULL CHECK (frame_count >= 0),
    drone_frame_count INTEGER NOT NULL CHECK (drone_frame_count >= 0),
    representative_incident_id VARCHAR(80) NOT NULL,
    raw_incident_ids JSONB NOT NULL,
    primary_frame_url TEXT,
    primary_thumbnail_url TEXT,
    per_modality_scores JSONB NOT NULL,
    thresholds JSONB NOT NULL,
    gating_reason TEXT NOT NULL,
    latency_ms DOUBLE PRECISION NOT NULL CHECK (latency_ms >= 0),
    evidence JSONB NOT NULL,
    media JSONB NOT NULL,
    objects JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_incident_aggregates_aggregate_id ON incident_aggregates(aggregate_id);
CREATE INDEX idx_incident_aggregates_last_seen_at ON incident_aggregates(last_seen_at DESC);
CREATE INDEX idx_incident_aggregates_decision ON incident_aggregates(decision);
CREATE INDEX idx_incident_aggregates_stream_name ON incident_aggregates(stream_name);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update updated_at
CREATE TRIGGER update_incidents_updated_at BEFORE UPDATE ON incidents
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_incident_aggregates_updated_at BEFORE UPDATE ON incident_aggregates
    FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();
