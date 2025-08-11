-- Migration script to add metadata_json column to raw_data table
-- Execute this script if the column doesn't exist yet

ALTER TABLE raw_data 
ADD COLUMN IF NOT EXISTS metadata_json TEXT NULL;

-- Verify the column was added
DESCRIBE raw_data;