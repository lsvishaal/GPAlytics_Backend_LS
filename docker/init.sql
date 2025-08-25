-- Initialize GPAlytics database
-- This script runs when SQL Server container starts

-- Create the GPAlytics database
IF NOT EXISTS (SELECT name
FROM sys.databases
WHERE name = 'GPAlytics')
BEGIN
    CREATE DATABASE GPAlytics;
    PRINT 'GPAlytics database created successfully';
END
ELSE
BEGIN
    PRINT 'GPAlytics database already exists';
END

-- Switch to GPAlytics database
USE GPAlytics;

-- Create a basic user for testing (optional)
-- Note: Your SQLModel will create the actual tables
IF NOT EXISTS (SELECT name
FROM sys.database_principals
WHERE name = 'testuser')
BEGIN
    CREATE USER testuser WITH PASSWORD = 'TestPassword123!';
    ALTER ROLE db_datareader ADD MEMBER testuser;
    ALTER ROLE db_datawriter ADD MEMBER testuser;
    PRINT 'Test user created successfully';
END

PRINT 'Database initialization completed';
