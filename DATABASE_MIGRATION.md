# Database Migration Guide

## Overview

The Maps Python Script Helper now uses SQLite database for improved performance and scalability. This document explains the migration process from JSON files to SQLite.

## What Changed

### Before (JSON Files)
- `users.json` - Single file with all users
- `user_scripts/*.json` - One JSON file per script
- `library/metadata.json` - Library images metadata

### After (SQLite Database)
- `maps_helper.db` - Single SQLite database file containing:
  - **users** table
  - **user_scripts** table
  - **library_images** table
  - **library_scripts** table
  - **execution_sessions** table

## Benefits

✅ **Performance**: Indexed queries are 10-100x faster  
✅ **Scalability**: Handles thousands of users/scripts easily  
✅ **Relationships**: Proper foreign keys and cascading deletes  
✅ **Features**: Easy to add search, favorites, tags, sharing  
✅ **Integrity**: ACID transactions ensure data consistency  

## Migration Steps

### 1. Install Updated Dependencies

```powershell
# Backend dependencies
cd backend
pip install -r requirements.txt
```

The new `sqlalchemy==2.0.23` dependency will be installed.

### 2. Run Migration Script

```powershell
# From project root
python migrate_to_db.py
```

This will:
- Create the `maps_helper.db` database
- Import all users from `users.json`
- Import all scripts from `user_scripts/*.json`
- Import all images from `library/metadata.json`
- Preserve all IDs and relationships

### 3. Test the Application

```powershell
# Start the backend
cd backend
python app.py
```

Verify that:
- All users are visible
- User scripts load correctly
- Library images display properly
- Creating/editing/deleting works

### 4. Backup Original Files (Optional)

After confirming everything works:

```powershell
# Create backup folder
mkdir backup_json_files

# Move original files
mv users.json backup_json_files/
mv user_scripts backup_json_files/
mv library/metadata.json backup_json_files/
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    settings JSON
);
CREATE INDEX ix_users_name ON users(name);
```

### User Scripts Table
```sql
CREATE TABLE user_scripts (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    code TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    is_favorite BOOLEAN DEFAULT 0,
    is_user_created BOOLEAN DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX ix_user_scripts_user_id ON user_scripts(user_id);
CREATE INDEX ix_user_scripts_created_at ON user_scripts(created_at);
```

### Library Images Table
```sql
CREATE TABLE library_images (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    created_at DATETIME NOT NULL,
    tags JSON
);
CREATE INDEX ix_library_images_name ON library_images(name);
CREATE INDEX ix_library_images_category ON library_images(category);
```

### Execution Sessions Table
```sql
CREATE TABLE execution_sessions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    script_id VARCHAR(36),
    script_name VARCHAR(255),
    started_at DATETIME NOT NULL,
    completed_at DATETIME,
    status VARCHAR(50),
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (script_id) REFERENCES user_scripts(id) ON DELETE SET NULL
);
```

## API Changes

All API endpoints remain the same, but now use the database:

- `GET /api/users` - Now queries database with indexes
- `POST /api/users` - Adds to database with validation
- `GET /api/user-scripts?user_id=xxx` - Fast indexed query
- `POST /api/user-scripts` - Database transaction
- `PUT /api/user-scripts/{id}` - Updates in database
- `DELETE /api/user-scripts/{id}` - Cascading deletes

## Database Management

### View Database Contents

Use any SQLite browser:
- [DB Browser for SQLite](https://sqlitebrowser.org/) (Recommended)
- [SQLite Viewer (VS Code Extension)](https://marketplace.visualstudio.com/items?itemName=qwtel.sqlite-viewer)

Or use command line:
```powershell
sqlite3 maps_helper.db
.tables
SELECT * FROM users;
SELECT * FROM user_scripts LIMIT 5;
```

### Backup Database

```powershell
# Simple file copy
cp maps_helper.db maps_helper.db.backup

# Or use SQLite backup
sqlite3 maps_helper.db ".backup 'backup.db'"
```

### Reset Database

If you need to start fresh:

```powershell
# Delete database
rm maps_helper.db

# Re-run migration
python migrate_to_db.py
```

## Troubleshooting

### Migration fails with "User not found"
- Check that `users.json` exists and is valid
- Run migration again (it's idempotent)

### "Database is locked" error
- Close any SQLite browser tools
- Restart the backend server

### Old data still showing
- Clear browser cache
- Check that backend is using new database file

### Need to rollback
- Stop the backend
- Delete `maps_helper.db`
- Restore from JSON files
- Downgrade backend code if needed

## Future Enhancements

With database in place, we can easily add:
- 📊 User analytics dashboard
- 🔍 Full-text search across scripts
- ⭐ Favorite scripts
- 🏷️ Script tags and categories
- 👥 Script sharing between users
- 📈 Execution history tracking
- 🔄 Script versioning

## Support

If you encounter issues:
1. Check the migration script output for errors
2. Verify database file was created: `ls maps_helper.db`
3. Test with simple query: `sqlite3 maps_helper.db "SELECT COUNT(*) FROM users;"`
4. Check backend logs for database connection errors

## Database Location

- **Development**: `./maps_helper.db` (project root)
- **Docker**: Volume mounted at `/app/maps_helper.db`

The database file is automatically created on first run if it doesn't exist.
