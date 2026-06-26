# Seed Scripts

This directory contains scripts for seeding default data into the database.

## seed_defaults.py

Seeds default records for the application:

1. **Roles**
   - Creates the `OWNER` role (code: "OWNER")

2. **Privileges**
   - Creates standard CRUD privileges for all modules:
     - BOOK, AUTHOR, GENRE, BOOK_GENRE, BOOK_AUTHOR, BOOK_RATING
     - BUSINESS, BUSINESS_BOOK, BUSINESS_USER, BUSINESS_RATING
     - INVENTORY_ITEM, ORDER, ORDER_ITEM, RATING
     - USER, ROLE, PRIVILEGE, ROLE_PRIVILEGE
     - VARIANT_TYPE, VARIANT_OPTION, ITEM_ATTRIBUTE, ENTITY_IMAGE
   - Note: AUTHOR module does not have DELETE privilege (authors cannot be deleted per MDC-AUTHOR-2)

3. **Role-Privilege Mappings**
   - Maps all created privileges to the OWNER role

4. **Platform Privileges**
   - MANAGE_PLATFORM_USERS
   - MANAGE_PLATFORM_PRIVILEGES
   - MANAGE_PLATFORM_PRIVILEGE_SETS
   - VIEW_PLATFORM_ANALYTICS
   - MANAGE_BUSINESSES
   - MANAGE_SYSTEM_SETTINGS

5. **Platform Privilege Sets**
   - Super Admin (all platform privileges)
   - Admin (MANAGE_PLATFORM_USERS, VIEW_PLATFORM_ANALYTICS, MANAGE_BUSINESSES)
   - Moderator (VIEW_PLATFORM_ANALYTICS, MANAGE_BUSINESSES)

6. **Platform Privilege Set-Privilege Mappings**
   - Maps platform privileges to their respective privilege sets

## Usage

```bash
# From the project root directory
python scripts/seed_defaults.py
```

## seed_super_admin.py

Seeds a platform super admin user for bootstrapping the platform.

Following MDC-PU bootstrap_super_admin:
- Creates USER with status "NEW" (forces password change on first login)
- Creates PLATFORM_USER linked to Super Admin privilege set
- Uses environment variables for admin credentials

### Usage

```bash
# From the project root directory
SUPER_ADMIN_EMAIL=admin@example.com SUPER_ADMIN_PASSWORD=changeme python scripts/seed_super_admin.py
```

### Optional Environment Variables

- `SUPER_ADMIN_EMAIL` (required): Email address for the super admin user
- `SUPER_ADMIN_PASSWORD` (required): Initial password (user will be forced to change on first login)
- `SUPER_ADMIN_FIRST_NAME` (optional, default: "Super"): First name for the super admin
- `SUPER_ADMIN_LAST_NAME` (optional, default: "Admin"): Last name for the super admin

### Prerequisites

- Must run `seed_defaults.py` first to create the Super Admin privilege set
- MongoDB must be running and accessible

### Notes

- The script is idempotent - if a user with the email already exists, it will check if they have a platform_user record
- If user exists but no platform_user, it will create the platform_user record
- User status is set to "NEW" to force password change on first login (per MDC-PU bootstrap_super_admin)

## upload_seeds.py

Uploads seed data from CSV files directly to the database. Supports uploading books, authors, and genres.

### Usage

```bash
# Upload a specific type
python scripts/upload_seeds.py --type authors --file scripts/seeds/authors.csv
python scripts/upload_seeds.py --type genres --file scripts/seeds/genres.csv
python scripts/upload_seeds.py --type books --file scripts/seeds/books.csv

# Upload all seed files
python scripts/upload_seeds.py --all
```

### CSV File Format

**authors.csv:**
- Columns: `first_name`, `last_name`, `middle_name` (optional), `about`, `image` (optional), `status` (optional, default: ACTIVE)

**genres.csv:**
- Columns: `name`, `description` (optional), `status` (optional, default: ACTIVE)

**books.csv:**
- Columns: `title`, `genres` (comma-separated), `image`, `synopsis`, `status` (optional, default: ACTIVE)

### Seed Files Location

Seed CSV files are located in `scripts/seeds/`:
- `scripts/seeds/authors.csv` - Sample author data (10 authors)
- `scripts/seeds/genres.csv` - Sample genre data (15 genres)
- `scripts/seeds/books.csv` - Sample book data (15 books)

### Prerequisites

- Python 3.8+
- MongoDB must be running and accessible
- Database connection configured (via environment variables or config)

### Notes

- The script uploads records directly to the database (no API required)
- No authentication token needed - connects directly to MongoDB
- Failed uploads are reported with row numbers and error messages
- The script is idempotent - running it multiple times will create duplicate records (use with caution)
- Books should be uploaded after genres and authors (books may reference genres)
- Data is validated using Pydantic models before insertion

## General Notes

- The scripts are idempotent - they check for existing records before creating new ones
- If a record already exists, they will skip creation and log a message
- The scripts will create missing mappings even if some records already exist
- Make sure MongoDB is running and accessible before running the scripts
- Run `seed_defaults.py` before `seed_super_admin.py`
