# ISPL Payroll — your local settings.
# 1. Copy this file to  erp.config.sh
# 2. Fill in your database details and save.
# (erp.config.sh is git-ignored, so your password stays local.)

# Your Postgres / Supabase connection (one line):
export ERP_DB="host=YOUR_HOST port=5432 user=YOUR_USER password=YOUR_PASSWORD dbname=postgres"

# A long random string that signs login cookies (make one up):
export ERP_SECRET="change-this-to-a-long-random-string-xyz123"

# First admin login (you'll set the password on first run):
export ERP_ADMIN_USER="dinesh"

# Where uploaded files are kept (optional):
export ERP_UPLOAD_DIR="$(dirname "$0")/uploads"
