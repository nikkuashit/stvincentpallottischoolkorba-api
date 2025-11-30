# How to Update Navigation Menu

## Problem
All 34 pages exist in the frontend (`pageContent.tsx`), but they don't appear in the navigation menu because the menu is dynamically loaded from the Django backend database.

## Solution
Update the school's navigation configuration in the backend database.

---

## Method 1: Using Django Admin Panel (Recommended)

1. **Start the backend server** (if not running):
   ```bash
   cd /Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api
   pipenv run python manage.py runserver
   ```

2. **Access Django Admin**:
   - URL: http://localhost:8000/admin/
   - Login with your admin credentials

3. **Navigate to Schools**:
   - Click on "Schools" in the admin panel
   - Find and click on "St. Vincent Pallotti School" (slug: stvincentpallottikorba)

4. **Update Navigation Config**:
   - Find the "Config" field (JSON field)
   - Replace the `navigation` array with the content from `NAVIGATION_CONFIG.json`
   - Save the changes

---

## Method 2: Using Admin Navigation Manager

If you have the custom navigation manager implemented:

1. **Access Navigation Manager**:
   - URL: http://localhost:5173/admin/navigation
   - Login with admin credentials

2. **Import/Update Navigation**:
   - Use the navigation manager interface to add menu items
   - Import from `NAVIGATION_CONFIG.json`
   - Save and publish changes

---

## Method 3: Direct Database Update (Advanced)

If you need to update the database directly:

```bash
cd /Users/ashitrai/Development/study/personal/school-website/stvincentpallottischoolkorba-api

# Activate virtual environment
pipenv shell

# Run Python shell
python manage.py shell
```

Then in the Python shell:

```python
import json
from schools.models import School

# Load the school
school = School.objects.get(slug='stvincentpallottikorba')

# Read the navigation config
with open('NAVIGATION_CONFIG.json', 'r') as f:
    nav_config = json.load(f)

# Update the config
if not school.config:
    school.config = {}
school.config['navigation'] = nav_config['navigation']

# Save
school.save()

print("Navigation updated successfully!")
exit()
```

---

## Navigation Structure

The new navigation includes:

### Main Menu Items:
1. **Home** → `/`
2. **About** → `/about`
   - About Us, Goal, Mission, Aims & Objectives, Principal's Message
3. **Infrastructure** → `/infrastructure`
   - Library, Laboratories, Computer Lab, Staff, Smart Class, Playground
4. **Academics** → `/academics`
   - Affiliation, Subjects, Syllabus, Olympiads, Scholarship, PTM, Curriculum, Results
5. **Admission** → `/admissions`
   - Admission Process, Policy, Fee Structure
6. **Activities** → `/activities`
   - Sports & Games, Cultural, Co-Scholastic, Celebrations
7. **Gallery** → `/gallery`
   - Photo Gallery, Virtual Tour, Annual Function
8. **Downloads** → `/downloads`
   - TC, Book List, Mandatory Disclosure, CBSE Documents
9. **Contact** → `/contact`

---

## Verification

After updating the navigation:

1. **Refresh the frontend**: http://localhost:5173/
2. **Check the menu**: You should see all menu items in the navigation bar
3. **Click on menu items**: They should navigate to the correct pages
4. **Test a few pages**:
   - http://localhost:5173/goal
   - http://localhost:5173/sports-games
   - http://localhost:5173/library

---

## Quick Test (Without Updating Backend)

To verify pages work without updating the backend, access them directly via URL:

- http://localhost:5173/goal → Our Goal
- http://localhost:5173/mission → Our Mission
- http://localhost:5173/sports-games → Sports & Games
- http://localhost:5173/library → Library
- http://localhost:5173/admission-2-2 → Admission Process
- http://localhost:5173/subject-offered → Subjects Offered
- http://localhost:5173/ptm → Parent-Teacher Meetings
- http://localhost:5173/celebration → Celebrations

All 34 pages should load with their content and images!

---

## Troubleshooting

### Pages show "Not Found"
- Verify the backend server is running: http://localhost:8000
- Check that school config has been updated
- Clear browser cache and refresh
- Check browser console for errors

### Menu doesn't update
- Hard refresh the page (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)
- Check that the navigation array is properly formatted JSON
- Verify the school slug matches: `stvincentpallottikorba`

### Images don't load
- Check that images are in: `src/assets/images/`
- Verify image imports in `pageContent.tsx`
- Check browser console for 404 errors

---

## Files Created

1. **NAVIGATION_CONFIG.json** - Complete navigation structure (63 items)
2. **UPDATE_NAVIGATION.md** - This file, with instructions
3. **Frontend: src/data/pageContent.tsx** - All 34 pages defined
4. **Migration Docs**:
   - PAGE_MIGRATION_PLAN.md
   - WEBSITE_CONTENT.md
   - MIGRATION_COMPLETE.md

---

*After updating the navigation, your complete website with all 34 pages will be accessible through the menu!*
