-- Multimodal Drone Detection Database Schema
-- The database 'drone_detection' is automatically created by POSTGRES_DB env variable

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create detection table
CREATE TABLE IF NOT EXISTS detections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    confidence NUMERIC(4, 3) CHECK (confidence >= 0 AND confidence <= 1),
    direction VARCHAR(2),
    distance_ft INTEGER,
    visual_confidence NUMERIC(4, 3) CHECK (visual_confidence >= 0 AND visual_confidence <= 1),
    thermal_confidence NUMERIC(4, 3) CHECK (thermal_confidence >= 0 AND thermal_confidence <= 1),
    fused_score NUMERIC(4, 3) CHECK (fused_score >= 0 AND fused_score <= 1),
    frame_snapshot_url TEXT,
    stream_name VARCHAR(20) DEFAULT 'drone',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on detected_at for faster queries
CREATE INDEX idx_detections_detected_at ON detections(detected_at DESC);
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
