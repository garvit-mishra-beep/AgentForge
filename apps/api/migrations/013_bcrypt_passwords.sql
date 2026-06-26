-- Update demo user password hash to bcrypt for standard compatibility
UPDATE users
SET password_hash = '$2b$12$7/YKFTAFfbj60xYLwS.3.utdZ40MVbRjpcnBJm/ePxdvyOeUOv6la'
WHERE id = '00000000-0000-0000-0000-000000000001';
