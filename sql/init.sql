-- Multimodal Drone Detection Database Schema
-- The database 'drone_detection' is automatically created by POSTGRES_DB env variable

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create detection table
CREATE TABLE IF NOT EXISTS detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence NUMERIC(4, 3) CHECK (confidence >= 0 AND confidence <= 1),
    direction VARCHAR(3),
    distance_ft INTEGER,
    visual_confidence NUMERIC(4, 3) CHECK (visual_confidence >= 0 AND visual_confidence <= 1),
    thermal_confidence NUMERIC(4, 3) CHECK (thermal_confidence >= 0 AND thermal_confidence <= 1),
    fused_score NUMERIC(4, 3) CHECK (fused_score >= 0 AND fused_score <= 1),
    frame_snapshot_url TEXT,
    stream_name VARCHAR(50) DEFAULT 'drone',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on timestamp for faster queries
CREATE INDEX idx_detections_timestamp ON detections(timestamp DESC);
CREATE INDEX idx_detections_confidence ON detections(confidence DESC);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update updated_at
CREATE TRIGGER update_detections_updated_at BEFORE UPDATE ON detections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
-- INSERT INTO detections (timestamp, drone_detected, confidence, direction, distance_ft, visual_confidence, thermal_confidence, fused_score, frame_snapshot_url)
-- VALUES
--     ('2026-04-15T14:32:07Z', true, 0.94, 'NE', 18, 0.92, 0.89, 0.94, 'https://s3.amazonaws.com/bucket/detection_001.jpg'),
--     ('2026-04-15T14:33:15Z', false, 0.23, NULL, NULL, 0.21, 0.25, 0.23, NULL);
