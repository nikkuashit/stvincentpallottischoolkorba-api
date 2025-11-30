# Parent Onboarding & Multi-Child Management System

## Executive Summary

This document defines the comprehensive parent self-registration, student onboarding, and multi-child management system. Parents can register themselves, add one or more children, submit admission applications, and manage their family's educational journey.

---

## Core Concepts

### 1. Parent as Primary User
- Parents register first (create account)
- Parents can add multiple children
- Each child can be added as:
  - **Admission Application** (prospective student)
  - **Existing Student** (already enrolled, parent claiming)

### 2. One-to-Many Relationship
```
Parent (1) ────── (Many) Children
  └─ John Smith
      ├─ Sarah Smith (Class 5)
      ├─ Michael Smith (Class 3)
      └─ Emma Smith (Application pending)
```

### 3. Multi-Parent Support
```
Student (1) ────── (Many) Parents
  └─ Sarah Smith
      ├─ John Smith (Father, Primary)
      └─ Mary Smith (Mother)
```

---

## Parent Registration Flow

### Step 1: Public Registration Page

**URL**: `/auth/register` or `/admissions/parent-registration`

**Form Fields**:
```typescript
interface ParentRegistrationForm {
  // Personal Information
  firstName: string
  lastName: string
  email: string  // Used for login
  phone: string  // Used for OTP verification

  // Login Credentials
  username: string  // Optional, can use email
  password: string
  confirmPassword: string

  // Optional (can be filled later)
  dateOfBirth?: string
  gender?: 'male' | 'female' | 'other'
  occupation?: string
  address?: string

  // Verification
  phoneOtp: string  // Sent after entering phone
  emailVerificationToken: string  // Sent to email

  // Terms
  termsAccepted: boolean
  privacyPolicyAccepted: boolean
}
```

### Step 2: Phone & Email Verification

**Phone Verification**:
```python
POST /api/auth/send-phone-otp/
{
  "phone": "+91-9876543210"
}

Response:
{
  "message": "OTP sent to +91-9876543210",
  "expires_in": 300  # 5 minutes
}

# Parent enters OTP
POST /api/auth/verify-phone-otp/
{
  "phone": "+91-9876543210",
  "otp": "123456"
}

Response:
{
  "verified": true,
  "phone_verified_token": "temp-token-xyz"
}
```

**Email Verification**:
```python
# Automatic email sent upon registration
# Contains link: /verify-email?token=abc123

GET /api/auth/verify-email/?token=abc123

Response:
{
  "verified": true,
  "message": "Email verified successfully"
}
```

### Step 3: Account Creation

```python
POST /api/auth/parent-registration/

Request:
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john.smith@example.com",
  "username": "johnsmith",
  "password": "SecurePass123!",
  "phone": "+91-9876543210",
  "phone_verified_token": "temp-token-xyz",
  "terms_accepted": true
}

Response:
{
  "id": "parent-uuid",
  "message": "Parent account created successfully",
  "email_verification_required": true,
  "next_step": "add_children",
  "tokens": {
    "access": "jwt-access-token",
    "refresh": "jwt-refresh-token"
  }
}
```

---

## Adding Children (Multiple Scenarios)

### Scenario 1: New Admission Application

**Use Case**: Parent wants to enroll new child in school

```python
POST /api/admissions/applications/

Request:
{
  "admission_type": "new_admission",
  "school_id": "school-uuid",

  // Student Information
  "student": {
    "first_name": "Sarah",
    "last_name": "Smith",
    "date_of_birth": "2015-03-15",
    "gender": "female",
    "blood_group": "O+",

    "previous_school": "ABC Primary School",
    "applying_for_class": "class-6",
    "applying_for_academic_year": "2025-26"
  },

  // Parent Information (auto-filled from logged-in parent)
  "parent_id": "parent-uuid",
  "relation": "father",

  // Documents
  "documents": [
    {
      "type": "birth_certificate",
      "file_url": "https://...",
      "file_name": "sarah_birth_cert.pdf"
    },
    {
      "type": "address_proof",
      "file_url": "https://..."
    },
    {
      "type": "previous_school_report",
      "file_url": "https://..."
    }
  ],

  // Additional Information
  "special_needs": false,
  "medical_conditions": "",
  "emergency_contact": {
    "name": "Mary Smith",
    "relation": "mother",
    "phone": "+91-9876543211"
  }
}

Response:
{
  "application_id": "app-uuid",
  "application_number": "APP-2025-1234",
  "status": "submitted",
  "message": "Admission application submitted successfully",
  "next_steps": [
    "Application under review",
    "You will be notified via email/SMS",
    "Expected response within 7 days"
  ],
  "fee_details": {
    "application_fee": 500,
    "payment_status": "pending",
    "payment_link": "/payments/app-uuid"
  }
}
```

### Scenario 2: Link Existing Student (Claim Child)

**Use Case**: Parent's child is already enrolled, parent wants to link them

```python
POST /api/parents/link-student/

Request:
{
  "student_admission_number": "SCH-2024-5678",
  "student_dob": "2015-03-15",  // For verification
  "relation": "father",

  // Verification method
  "verification_method": "school_admin_approval",  // or "otp"
}

Response (School Admin Approval Method):
{
  "link_request_id": "req-uuid",
  "status": "pending_approval",
  "message": "Request sent to school admin for verification",
  "student": {
    "name": "Sarah Smith",
    "class": "6-A",
    "school": "ABC School"
  }
}

Response (OTP Method):
{
  "link_request_id": "req-uuid",
  "status": "otp_sent",
  "message": "OTP sent to registered phone number ending in **3210",
  "otp_expires_in": 300
}

# After OTP verification
POST /api/parents/link-student/verify-otp/
{
  "link_request_id": "req-uuid",
  "otp": "654321"
}

Response:
{
  "status": "linked",
  "message": "Student linked successfully",
  "student": {
    "id": "student-uuid",
    "name": "Sarah Smith",
    "admission_number": "SCH-2024-5678",
    "class": "6-A"
  }
}
```

### Scenario 3: Add Sibling (Subsequent Child)

**Use Case**: Parent already has one child enrolled, adding another

```python
POST /api/admissions/applications/sibling/

Request:
{
  "school_id": "school-uuid",
  "existing_sibling_id": "student-uuid-of-first-child",

  "student": {
    "first_name": "Michael",
    "last_name": "Smith",
    "date_of_birth": "2017-08-22",
    "gender": "male",
    "applying_for_class": "class-4"
  },

  "sibling_discount_applicable": true,

  // Less documentation required (some can be reused)
  "reuse_parent_documents": true,
  "documents": [
    {
      "type": "birth_certificate",
      "file_url": "https://..."
    }
  ]
}

Response:
{
  "application_id": "app-uuid-2",
  "application_number": "APP-2025-1235",
  "sibling_preference": true,
  "discount_applied": 20,  // 20% sibling discount
  "status": "submitted",
  "priority": "high"  // Siblings get priority
}
```

---

## Parent-Child Data Model

### Enhanced Models

#### Parent Model (Updated)

```python
class Parent(models.Model):
    """Parent/Guardian user profile"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')

    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)

    # Contact Information
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, unique=True)
    alternate_phone = models.CharField(max_length=20, blank=True)

    # Verification Status
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)

    # Professional Information
    occupation = models.CharField(max_length=100, blank=True)
    employer_name = models.CharField(max_length=200, blank=True)
    annual_income_range = models.CharField(max_length=50, blank=True)

    # Address
    address_line1 = models.TextField(blank=True)
    address_line2 = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, default='India')

    # Profile
    photo = models.ImageField(upload_to='parents/photos/', null=True, blank=True)

    # Relationship to students (ManyToMany through StudentParent)
    students = models.ManyToManyField('Student', through='StudentParent', related_name='parents')

    # Status
    is_primary_contact = models.BooleanField(default=True)  # For school communications
    is_active = models.BooleanField(default=True)

    # Metadata
    registration_source = models.CharField(
        max_length=50,
        choices=[
            ('self_registration', 'Self Registration'),
            ('admin_created', 'Created by Admin'),
            ('admission_process', 'Through Admission'),
        ],
        default='self_registration'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['organization', 'school']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_children_count(self):
        return self.students.count()

    def get_active_children(self):
        return self.students.filter(status='active')
```

#### StudentParent Model (Enhanced)

```python
class StudentParent(models.Model):
    """Many-to-Many relationship between Students and Parents"""

    RELATION_CHOICES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Legal Guardian'),
        ('grandfather', 'Grandfather'),
        ('grandmother', 'Grandmother'),
        ('uncle', 'Uncle'),
        ('aunt', 'Aunt'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)

    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE)

    relation = models.CharField(max_length=20, choices=RELATION_CHOICES)

    # Primary parent gets all notifications
    is_primary = models.BooleanField(default=False)

    # Can this parent make decisions (admission, transfer)?
    has_decision_authority = models.BooleanField(default=True)

    # Permissions
    can_view_grades = models.BooleanField(default=True)
    can_view_attendance = models.BooleanField(default=True)
    can_download_reports = models.BooleanField(default=True)
    can_communicate_with_teachers = models.BooleanField(default=True)

    # Status
    is_active = models.BooleanField(default=True)

    # Verification (for self-linked students)
    link_verified_by = models.ForeignKey(
        'UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_parent_links'
    )
    link_verified_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['student', 'parent']]
        indexes = [
            models.Index(fields=['organization', 'student']),
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['is_primary']),
        ]

    def __str__(self):
        return f"{self.parent.full_name} ({self.relation}) - {self.student.full_name}"
```

#### AdmissionApplication Model (New)

```python
class AdmissionApplication(models.Model):
    """Admission application submitted by parent"""

    APPLICATION_STATUS = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('documents_pending', 'Documents Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('waitlisted', 'Waitlisted'),
        ('enrolled', 'Enrolled'),
        ('withdrawn', 'Withdrawn'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    application_number = models.CharField(max_length=50, unique=True)

    # Organization & School
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE)
    school = models.ForeignKey('School', on_delete=models.CASCADE)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.CASCADE)

    # Student Information (before Student record is created)
    student_first_name = models.CharField(max_length=100)
    student_last_name = models.CharField(max_length=100)
    student_date_of_birth = models.DateField()
    student_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    student_blood_group = models.CharField(max_length=5, blank=True)

    # Photo
    student_photo = models.ImageField(upload_to='applications/photos/', null=True, blank=True)

    # Academic Information
    previous_school = models.CharField(max_length=200, blank=True)
    previous_class = models.CharField(max_length=50, blank=True)
    applying_for_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True)

    # Parent Information
    parent = models.ForeignKey('Parent', on_delete=models.CASCADE, related_name='admission_applications')
    parent_relation = models.CharField(max_length=20, choices=StudentParent.RELATION_CHOICES)

    # Sibling Information
    has_sibling = models.BooleanField(default=False)
    sibling_student = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='sibling_applications')
    sibling_discount_applied = models.BooleanField(default=False)
    sibling_discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Medical Information
    has_special_needs = models.BooleanField(default=False)
    special_needs_description = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)
    allergies = models.TextField(blank=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_relation = models.CharField(max_length=50)
    emergency_contact_phone = models.CharField(max_length=20)

    # Documents (JSONField)
    documents = models.JSONField(default=list)
    # Example: [
    #   {"type": "birth_certificate", "url": "...", "verified": true},
    #   {"type": "address_proof", "url": "...", "verified": false}
    # ]

    # Application Status
    status = models.CharField(max_length=30, choices=APPLICATION_STATUS, default='draft')

    # Application Dates
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    decision_at = models.DateTimeField(null=True, blank=True)

    # Review
    reviewed_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, related_name='reviewed_applications')
    review_notes = models.TextField(blank=True)

    # Decision
    approved_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, related_name='approved_applications')
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    # Enrollment
    student = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True, related_name='admission_application')
    admission_number = models.CharField(max_length=50, blank=True)
    enrolled_at = models.DateTimeField(null=True, blank=True)

    # Financial
    application_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    application_fee_paid = models.BooleanField(default=False)
    payment_transaction_id = models.CharField(max_length=100, blank=True)

    # Priority
    priority_score = models.IntegerField(default=0)  # Based on sibling, distance, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['organization', 'school', 'status']),
            models.Index(fields=['parent', 'status']),
            models.Index(fields=['application_number']),
            models.Index(fields=['academic_year', 'applying_for_class']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.application_number} - {self.student_first_name} {self.student_last_name}"

    def generate_application_number(self):
        """Generate unique application number"""
        year = self.academic_year.start_date.year
        count = AdmissionApplication.objects.filter(
            school=self.school,
            academic_year=self.academic_year
        ).count()
        return f"APP-{year}-{self.school.code}-{count+1:04d}"
```

---

## Parent Dashboard Features

### Dashboard Overview

```
┌─────────────────────────────────────────────┐
│  Welcome back, John Smith!                  │
├─────────────────────────────────────────────┤
│                                             │
│  MY CHILDREN (3)                            │
│  ┌──────────────┐  ┌──────────────┐       │
│  │ Sarah Smith  │  │ Michael Smith│       │
│  │ Class 6-A    │  │ Class 4-B    │       │
│  │ Attendance:  │  │ Attendance:  │       │
│  │ 95%          │  │ 92%          │       │
│  │ [View More]  │  │ [View More]  │       │
│  └──────────────┘  └──────────────┘       │
│                                             │
│  ┌──────────────┐                          │
│  │ Emma Smith   │                          │
│  │ Application  │                          │
│  │ Pending      │                          │
│  │ [Track]      │                          │
│  └──────────────┘                          │
│                                             │
│  [+ Add Another Child]                     │
│                                             │
│  QUICK ACTIONS                              │
│  • View Attendance                          │
│  • View Grades                              │
│  • Download Report Cards                    │
│  • Message Teachers                         │
│  • Pay Fees                                 │
│  • Apply for Leave                          │
│                                             │
│  RECENT NOTIFICATIONS (5)                   │
│  • Sarah - Math assignment due tomorrow     │
│  • Michael - Parent-teacher meeting on...  │
│  • Emma - Application approved!             │
│                                             │
└─────────────────────────────────────────────┘
```

### Features Available to Parents

#### 1. Child Management
```typescript
interface ChildManagementFeatures {
  addChild: {
    newAdmission: boolean      // Submit new application
    linkExisting: boolean       // Claim enrolled student
    addSibling: boolean         // Add sibling of enrolled student
  }

  viewChildren: {
    profiles: boolean           // View child profiles
    attendance: boolean         // View attendance records
    grades: boolean             // View grades/report cards
    assignments: boolean        // View assignments
    schedules: boolean          // View class schedules
  }

  manageChildren: {
    updateProfile: boolean      // Update child info
    uploadDocuments: boolean    // Upload/update documents
    managePermissions: boolean  // Manage photo/activity consent
  }
}
```

#### 2. Communication
- Message teachers
- View school announcements
- Receive notifications (email, SMS, app)
- Schedule parent-teacher meetings
- Report absences/leaves

#### 3. Financial
- View fee structure
- Pay fees online
- Download receipts
- View payment history
- Apply for fee concession

#### 4. Applications & Transfers
- Track admission applications
- Initiate student transfer
- Track transfer status

---

## Complete Registration & Onboarding Flow

### Parent Journey Map

```
┌────────────────────────────────────────────────────────┐
│ PHASE 1: DISCOVERY                                     │
│ Parent visits school website                           │
│ Clicks "Apply for Admission" or "Parent Portal"       │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 2: REGISTRATION                                  │
│ 1. Parent enters basic info (name, email, phone)      │
│ 2. Verifies phone via OTP                             │
│ 3. Creates password                                    │
│ 4. Receives email verification link                   │
│ Status: Account created (email verification pending)  │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 3: PROFILE COMPLETION                           │
│ 1. Add address details                                │
│ 2. Add occupation & employer                          │
│ 3. Upload ID proof (optional)                         │
│ Status: Profile 80% complete                          │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 4: ADD FIRST CHILD                              │
│                                                        │
│ Option A: New Admission                               │
│ • Fill student details                                │
│ • Upload documents (birth cert, address proof)        │
│ • Select class applying for                           │
│ • Pay application fee                                 │
│ • Submit application                                  │
│ Status: Application submitted                         │
│                                                        │
│ Option B: Link Existing Student                       │
│ • Enter admission number + DOB                        │
│ • Request sent to school admin                        │
│ • Awaiting verification                               │
│ Status: Link request pending                          │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 5: ADD MORE CHILDREN (Optional)                 │
│ Parent can add siblings:                              │
│ • Sibling applications get priority                   │
│ • Discount may apply                                  │
│ • Some documents reused                               │
│ Status: Multiple children added                       │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 6: SCHOOL REVIEW                                │
│ School admin reviews application:                     │
│ • Verifies documents                                  │
│ • Checks eligibility                                  │
│ • Approves/rejects                                    │
│ Parent receives notification                          │
│ Status: Decision received                             │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 7: ENROLLMENT (If Approved)                     │
│ 1. Parent receives admission offer                    │
│ 2. Pays admission fee                                 │
│ 3. Completes enrollment formalities                   │
│ 4. Student record created in system                   │
│ 5. Parent-student link activated                      │
│ Status: Enrolled! Parent portal fully active          │
└────────────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────────────┐
│ PHASE 8: ONGOING MANAGEMENT                           │
│ Parent can now:                                       │
│ • View all children's data                            │
│ • Track attendance & grades                           │
│ • Communicate with school                             │
│ • Pay fees                                            │
│ • Add more children anytime                           │
│ Status: Active parent user                            │
└────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### Parent Registration & Management

```python
# Parent self-registration
POST /api/auth/parent-registration/
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john@example.com",
  "phone": "+91-9876543210",
  "password": "SecurePass123!",
  "phone_verified_token": "temp-token"
}

# Send phone OTP
POST /api/auth/send-phone-otp/
{"phone": "+91-9876543210"}

# Verify phone OTP
POST /api/auth/verify-phone-otp/
{"phone": "+91-9876543210", "otp": "123456"}

# Verify email
GET /api/auth/verify-email/?token=abc123

# Get parent profile
GET /api/parents/me/

# Update parent profile
PATCH /api/parents/me/
{
  "occupation": "Software Engineer",
  "address_line1": "123 Main St"
}

# Get parent's children
GET /api/parents/me/children/
Response:
{
  "children": [
    {
      "id": "student-uuid",
      "name": "Sarah Smith",
      "class": "6-A",
      "admission_number": "SCH-2024-1234",
      "status": "active",
      "relation": "daughter"
    }
  ]
}
```

### Admission Applications

```python
# Create new admission application
POST /api/admissions/applications/
{
  "school_id": "uuid",
  "student_first_name": "Emma",
  "student_last_name": "Smith",
  "student_date_of_birth": "2019-05-10",
  "applying_for_class": "class-uuid",
  "documents": [...]
}

# Save as draft (can submit later)
POST /api/admissions/applications/draft/

# Submit application
POST /api/admissions/applications/{id}/submit/

# Get application status
GET /api/admissions/applications/{id}/

# Upload application document
POST /api/admissions/applications/{id}/documents/
FormData: {document_type, file}

# Pay application fee
POST /api/admissions/applications/{id}/pay-fee/
{
  "payment_method": "razorpay",
  "amount": 500
}

# Track application
GET /api/admissions/applications/{id}/track/
Response:
{
  "status": "under_review",
  "timeline": [
    {"stage": "submitted", "date": "2025-01-15"},
    {"stage": "under_review", "date": "2025-01-16"},
    {"stage": "decision", "expected_date": "2025-01-22"}
  ]
}
```

### Link Existing Student

```python
# Request to link student
POST /api/parents/link-student/
{
  "student_admission_number": "SCH-2024-5678",
  "student_dob": "2015-03-15",
  "relation": "father",
  "verification_method": "school_admin_approval"
}

# Verify with OTP (alternate method)
POST /api/parents/link-student/verify-otp/
{
  "link_request_id": "req-uuid",
  "otp": "654321"
}

# Get link requests (for school admin)
GET /api/schools/link-requests/pending/

# Approve link request (school admin)
POST /api/schools/link-requests/{id}/approve/

# Reject link request (school admin)
POST /api/schools/link-requests/{id}/reject/
{"reason": "Invalid details provided"}
```

---

## Verification & Security

### 1. Phone Verification
- OTP sent via SMS
- Valid for 5 minutes
- Max 3 attempts
- Rate limiting: 1 OTP per minute

### 2. Email Verification
- Link sent to email
- Token valid for 24 hours
- Can request new link if expired

### 3. Student Link Verification
- **Option A**: School admin approval (recommended)
  - Request sent to school
  - Admin verifies parent identity
  - Approval required before link activates

- **Option B**: OTP to registered phone (if student has parent phone in records)
  - System checks if parent phone matches student's records
  - Sends OTP to that number
  - Instant verification

### 4. Document Verification
- School admin reviews uploaded documents
- Can request re-upload if unclear
- Documents marked as verified/not verified

---

## Business Rules

### 1. Multiple Parents per Student
```python
# Allow up to 2 parents by default (configurable)
MAX_PARENTS_PER_STUDENT = 2

# Roles
- Primary parent: Gets all notifications
- Secondary parent: Can view, limited permissions
```

### 2. Sibling Benefits
```python
SIBLING_DISCOUNT_PERCENTAGE = 20  # Configurable per school
SIBLING_ADMISSION_PRIORITY = True

def calculate_priority_score(application):
    score = 0
    if application.has_sibling:
        score += 50
    if application.parent.address_distance < 5:  # km
        score += 30
    if application.special_category:
        score += 40
    return score
```

### 3. Application Fee
```python
# Application fee structure
APPLICATION_FEE = {
    'new_admission': 500,
    'sibling_admission': 250,  # 50% discount
    'readmission': 200,
}

# Refund policy
REFUND_IF_REJECTED = True
REFUND_PERCENTAGE = 80  # 80% refund (20% processing fee)
```

### 4. Admission Capacity
```python
def check_admission_availability(class_id):
    """Check if class has capacity"""
    class_obj = Class.objects.get(id=class_id)
    current_count = class_obj.students.filter(status='active').count()

    if current_count >= class_obj.capacity:
        return False, "Class full"

    # Reserve some seats for siblings
    reserved_for_siblings = class_obj.capacity * 0.1  # 10%
    if current_count >= (class_obj.capacity - reserved_for_siblings):
        return True, "Waitlist (sibling priority)"

    return True, "Available"
```

---

## Notifications

### Email Templates

**1. Welcome Email (After Registration)**
```
Subject: Welcome to ABC School Parent Portal!

Hi John,

Thank you for registering with ABC School!

Your parent account has been created successfully.
Email: john@example.com

Next Steps:
1. Verify your email (click link below)
2. Complete your profile
3. Add your children

[Verify Email] [Login to Portal]

Need help? Contact us at support@school.com
```

**2. Application Submitted**
```
Subject: Application Submitted - Emma Smith

Hi John,

Your admission application for Emma Smith has been submitted successfully.

Application Number: APP-2025-1234
Class Applied: Class 1-A
Application Fee: ₹500 (Paid)

Status: Under Review
Expected Decision: Within 7 days

Track Application: [Link]

Thank you!
ABC School Admissions Team
```

**3. Application Approved**
```
Subject: 🎉 Admission Approved - Emma Smith

Hi John,

Congratulations! We are pleased to inform you that Emma Smith's admission application has been approved.

Class: 1-A
Admission Number: SCH-2025-5678

Next Steps:
1. Pay admission fee: ₹10,000 (Due: 7 days)
2. Submit original documents
3. Complete enrollment formalities

[Pay Fee Now] [View Details]

Welcome to ABC School family!
```

**4. Student Linked Successfully**
```
Subject: Student Linked to Your Account

Hi John,

Sarah Smith (Adm. No: SCH-2024-5678) has been successfully linked to your parent account.

You can now:
• View attendance and grades
• Download report cards
• Communicate with teachers
• Pay fees online

[Visit Portal]
```

---

## Mobile App Considerations

### Progressive Web App (PWA) Features

```typescript
interface ParentMobileApp {
  features: {
    pushNotifications: boolean    // Real-time alerts
    offlineMode: boolean           // View cached data
    biometricLogin: boolean        // Fingerprint/Face ID
    qrCodeScanner: boolean         // Scan attendance QR
    documentCamera: boolean        // Upload docs via camera
  }

  notifications: {
    dailyAttendance: boolean       // "Sarah marked present"
    gradeUpdated: boolean          // "Math exam grade posted"
    feeReminder: boolean           // "Fee due in 3 days"
    schoolAnnouncements: boolean   // "School closed tomorrow"
    teacherMessages: boolean       // "New message from teacher"
  }
}
```

---

## Implementation Checklist

### Backend
- [ ] Create Parent model with multi-child support
- [ ] Create StudentParent relationship model
- [ ] Create AdmissionApplication model
- [ ] Implement phone OTP verification
- [ ] Implement email verification
- [ ] Create parent registration API
- [ ] Create add child APIs (admission + link)
- [ ] Create parent dashboard API
- [ ] Implement student link approval workflow
- [ ] Set up notification system (email + SMS)

### Frontend
- [ ] Parent registration page
- [ ] Phone verification UI
- [ ] Email verification landing page
- [ ] Parent dashboard
- [ ] Add child wizard (multi-step form)
- [ ] Document upload interface
- [ ] Application tracking page
- [ ] Link existing student form
- [ ] Child profile cards
- [ ] Notification center

### Admin Panel
- [ ] View admission applications
- [ ] Approve/reject applications
- [ ] Review parent-student link requests
- [ ] Bulk approve siblings
- [ ] Application analytics

---

## Future Enhancements

1. **Family Account**: Multiple parents share single family account
2. **Multi-School**: Parent with children in different schools
3. **Student Self-Registration**: For older students (college)
4. **Payment Plans**: Installment options for fees
5. **Scholarship Applications**: Built-in scholarship workflow
6. **Alumni Network**: Former students maintaining connection

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Status**: Design Complete - Ready for Implementation
