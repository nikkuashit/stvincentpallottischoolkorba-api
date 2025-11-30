# Student Transfer Workflow System

## Executive Summary

This document defines the comprehensive student transfer workflow, including intra-organization transfers, inter-organization transfers, and all associated business rules, permissions, and data handling.

---

## Transfer Types

### 1. Intra-Organization Transfer
**Definition**: Student moves between schools within the same organization

**Common Scenarios**:
- Moving from junior school to senior school
- Relocating to different branch in different city
- Academic performance-based transfer
- Parent request due to location change

**Example**: Student moves from "ABC Primary School" to "ABC High School" (both under ABC Education Group)

---

### 2. Inter-Organization Transfer
**Definition**: Student moves from one organization to completely different organization

**Common Scenarios**:
- Family relocation to different city/country
- Switching to school with different curriculum
- Disciplinary transfer (rare)
- Better opportunities/facilities

**Example**: Student moves from "ABC School" to "XYZ School" (different organizations)

---

### 3. Class/Section Transfer (Within Same School)
**Definition**: Student changes class or section within the same school

**Common Scenarios**:
- Section rebalancing
- Academic stream change (Science → Commerce)
- Performance-based promotion
- Parent request

**Example**: Student moves from "Class 10-A" to "Class 10-B" in same school

---

## Transfer Workflow

### Workflow States

```
┌─────────────┐
│   DRAFT     │ ← Transfer request created, not submitted
└─────────────┘
      ↓
┌─────────────┐
│   PENDING   │ ← Submitted, awaiting source school approval
└─────────────┘
      ↓
┌─────────────┐
│  APPROVED   │ ← Source school approved
│  (Source)   │
└─────────────┘
      ↓
┌─────────────┐
│  PENDING    │ ← Awaiting destination school approval
│(Destination)│
└─────────────┘
      ↓
┌─────────────┐
│  ACCEPTED   │ ← Destination school accepted
└─────────────┘
      ↓
┌─────────────┐
│  COMPLETED  │ ← Transfer finalized, student moved
└─────────────┘

    OR

┌─────────────┐
│  REJECTED   │ ← Rejected by either school
└─────────────┘

┌─────────────┐
│  CANCELLED  │ ← Cancelled by requester before completion
└─────────────┘
```

---

## Who Can Initiate Transfer?

### Transfer Initiation Matrix

| Transfer Type | Initiator | Requires Approval From |
|---------------|-----------|------------------------|
| **Intra-Org Transfer** | Parent, School Admin, Org Admin | Source School Admin → Destination School Admin → Org Admin (optional) |
| **Inter-Org Transfer (Outgoing)** | Parent, School Admin | Source School Admin → Org Admin |
| **Inter-Org Transfer (Incoming)** | Destination School Admin | Destination School Admin → Org Admin |
| **Class/Section Transfer** | School Admin, School Staff | School Admin only |

### Detailed Permission Rules

#### 1. **Parent-Initiated Transfer**
```
Permissions Required:
- Parent can initiate ONLY for their own children
- Can create transfer request (DRAFT state)
- Can upload supporting documents
- Can cancel before approval
- Cannot approve at any stage
```

**Steps**:
1. Parent logs into portal
2. Navigates to "Student Transfer Request"
3. Selects student (from their children)
4. Chooses transfer type and destination
5. Fills reason and uploads documents
6. Submits request

---

#### 2. **School Admin-Initiated Transfer**
```
Permissions Required:
- Can initiate for any student in their school
- Can approve/reject incoming requests
- Can approve/reject outgoing requests
- Can cancel transfer if not completed
- Can recommend students for transfer
```

**Use Cases**:
- Student performance requires different school
- School capacity issues
- Disciplinary action
- Parent request handling

---

#### 3. **Org Admin-Initiated Transfer**
```
Permissions Required:
- Can initiate for any student across organization
- Can override school decisions (with audit log)
- Can approve/reject all intra-org transfers
- Can facilitate inter-org transfers
- Can bulk transfer students (e.g., grade promotion)
```

**Use Cases**:
- Organization-wide restructuring
- New school opening (bulk transfer)
- Capacity balancing across schools
- Policy enforcement

---

#### 4. **School Staff (Limited)**
```
Permissions Required:
- Can ONLY initiate class/section transfers within school
- Cannot initiate school-to-school transfers
- Requires School Admin approval
```

**Use Cases**:
- Teacher recommending section change
- Class balancing by coordinator

---

## Transfer Request Model

### Database Schema

```python
class StudentTransfer(models.Model):
    """Student transfer request and workflow management"""

    TRANSFER_TYPES = [
        ('intra_org', 'Within Organization'),
        ('inter_org_outgoing', 'To Different Organization'),
        ('inter_org_incoming', 'From Different Organization'),
        ('class_section', 'Class/Section Change'),
    ]

    TRANSFER_STATUS = [
        ('draft', 'Draft'),
        ('pending_source', 'Pending Source Approval'),
        ('approved_source', 'Approved by Source'),
        ('pending_destination', 'Pending Destination Approval'),
        ('accepted', 'Accepted by Destination'),
        ('completed', 'Transfer Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    REJECTION_REASONS = [
        ('capacity_full', 'School at Full Capacity'),
        ('academic_mismatch', 'Academic Requirements Not Met'),
        ('documentation_incomplete', 'Incomplete Documentation'),
        ('financial_dues', 'Outstanding Fees/Dues'),
        ('other', 'Other Reason'),
    ]

    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Transfer Type
    transfer_type = models.CharField(max_length=30, choices=TRANSFER_TYPES)
    status = models.CharField(max_length=30, choices=TRANSFER_STATUS, default='draft')

    # Student Information
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='transfer_requests')

    # Source Information
    source_organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='outgoing_transfers')
    source_school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='outgoing_transfers')
    source_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, related_name='outgoing_transfers')

    # Destination Information
    destination_organization = models.ForeignKey('Organization', on_delete=models.CASCADE, related_name='incoming_transfers', null=True)
    destination_school = models.ForeignKey('School', on_delete=models.CASCADE, related_name='incoming_transfers', null=True)
    destination_class = models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, related_name='incoming_transfers')

    # Request Details
    reason = models.TextField()
    additional_notes = models.TextField(blank=True)
    effective_date = models.DateField()  # When transfer should take effect

    # Approvals
    initiated_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, related_name='initiated_transfers')
    initiated_at = models.DateTimeField(auto_now_add=True)

    source_approved_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, related_name='source_approved_transfers')
    source_approved_at = models.DateTimeField(null=True, blank=True)
    source_approval_notes = models.TextField(blank=True)

    destination_approved_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, related_name='destination_approved_transfers')
    destination_approved_at = models.DateTimeField(null=True, blank=True)
    destination_approval_notes = models.TextField(blank=True)

    # Rejection Details
    rejected_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, related_name='rejected_transfers')
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.CharField(max_length=50, choices=REJECTION_REASONS, blank=True)
    rejection_notes = models.TextField(blank=True)

    # Completion
    completed_by = models.ForeignKey('UserProfile', on_delete=models.SET_NULL, null=True, related_name='completed_transfers')
    completed_at = models.DateTimeField(null=True, blank=True)

    # Documents
    supporting_documents = models.JSONField(default=list)
    # Example: [
    #   {"type": "transfer_certificate", "url": "...", "uploaded_at": "..."},
    #   {"type": "parent_consent", "url": "...", "uploaded_at": "..."}
    # ]

    # Financial Settlement
    dues_cleared = models.BooleanField(default=False)
    final_settlement_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    settlement_date = models.DateField(null=True, blank=True)

    # Audit Trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['source_school', 'status']),
            models.Index(fields=['destination_school', 'status']),
            models.Index(fields=['status', 'effective_date']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Transfer: {self.student.full_name} ({self.get_transfer_type_display()}) - {self.status}"
```

---

## Step-by-Step Transfer Process

### Scenario 1: Parent-Initiated Intra-Org Transfer

**Example**: Parent wants to transfer child from "ABC Primary" to "ABC High School"

#### Step 1: Parent Creates Request
```python
POST /api/transfers/

Request Body:
{
  "student_id": "uuid-of-student",
  "transfer_type": "intra_org",
  "destination_school_id": "uuid-of-abc-high-school",
  "destination_class_id": "uuid-of-class-9a",
  "reason": "Student completed primary education, moving to high school",
  "effective_date": "2025-04-01",
  "supporting_documents": [...]
}

Response:
{
  "id": "transfer-uuid",
  "status": "draft",
  "message": "Transfer request created. Please review and submit."
}
```

#### Step 2: Parent Submits Request
```python
POST /api/transfers/{id}/submit/

Response:
{
  "status": "pending_source",
  "message": "Transfer request submitted. Awaiting ABC Primary School approval."
}

# Notification sent to:
- ABC Primary School Admin
- Student's class teacher
```

#### Step 3: Source School Reviews
```python
GET /api/transfers/pending-approvals/

# ABC Primary School Admin sees:
{
  "pending_transfers": [
    {
      "id": "transfer-uuid",
      "student": "John Doe",
      "destination": "ABC High School",
      "reason": "...",
      "parent_request": true,
      "documents": [...]
    }
  ]
}
```

**Checks Performed by Source School**:
- ✅ Outstanding fees cleared?
- ✅ Library books returned?
- ✅ Disciplinary record clean?
- ✅ Transfer certificate prepared?
- ✅ Academic records complete?

#### Step 4: Source School Approves
```python
POST /api/transfers/{id}/approve-source/

Request Body:
{
  "approval_notes": "All clearances obtained. Student in good standing.",
  "dues_cleared": true,
  "documents": [
    {
      "type": "transfer_certificate",
      "url": "https://...",
      "issued_date": "2025-03-15"
    },
    {
      "type": "academic_transcript",
      "url": "https://..."
    }
  ]
}

Response:
{
  "status": "pending_destination",
  "message": "Transfer approved by source school. Forwarded to ABC High School."
}

# Notification sent to:
- ABC High School Admin
- Parent (email + app notification)
```

#### Step 5: Destination School Reviews
```python
GET /api/transfers/incoming-requests/

# ABC High School Admin sees:
{
  "incoming_transfers": [
    {
      "id": "transfer-uuid",
      "student": "John Doe",
      "from_school": "ABC Primary",
      "requested_class": "9-A",
      "source_approved": true,
      "documents": [...],
      "academic_history": {...}
    }
  ]
}
```

**Checks Performed by Destination School**:
- ✅ Class capacity available?
- ✅ Academic requirements met?
- ✅ Required documents submitted?
- ✅ Age eligibility verified?

#### Step 6: Destination School Accepts
```python
POST /api/transfers/{id}/accept/

Request Body:
{
  "acceptance_notes": "Seat available in Class 9-A. Admission approved.",
  "assigned_class_id": "uuid-of-class-9a",
  "admission_number": "ABC-HS-2025-1234",
  "admission_date": "2025-04-01"
}

Response:
{
  "status": "accepted",
  "message": "Transfer accepted. Awaiting final completion."
}

# Notification sent to:
- Parent (with admission details)
- ABC Primary (confirmation)
- Org Admin (for records)
```

#### Step 7: Transfer Completion (Automated on Effective Date)
```python
# Automated job runs on effective_date
POST /api/transfers/{id}/complete/

Actions Performed:
1. Update Student record:
   - student.school = destination_school
   - student.current_class = destination_class
   - student.admission_number = new_admission_number
   - student.status = 'active'

2. Update Source School:
   - Remove from active students
   - Mark as 'transferred' in records
   - Archive student data

3. Update Destination School:
   - Add to active students
   - Create new academic records
   - Enroll in classes

4. Create Audit Log:
   - Record transfer completion
   - Link all documents
   - Timestamp all actions

5. Notify all parties:
   - Parent: "Transfer complete"
   - Source School: "Student transferred out"
   - Destination School: "New student enrolled"

Response:
{
  "status": "completed",
  "message": "Transfer completed successfully",
  "student": {
    "current_school": "ABC High School",
    "current_class": "9-A",
    "admission_number": "ABC-HS-2025-1234"
  }
}
```

---

### Scenario 2: School Admin-Initiated Inter-Org Transfer

**Example**: ABC School Admin transfers student to XYZ School (different org)

#### Step 1: Admin Creates Outgoing Transfer
```python
POST /api/transfers/

Request Body:
{
  "student_id": "uuid",
  "transfer_type": "inter_org_outgoing",
  "destination_organization_name": "XYZ Education Group",
  "destination_school_name": "XYZ International School",
  "reason": "Parent relocation to different city",
  "effective_date": "2025-05-01",
  "parent_consent": true,
  "parent_consent_document": "https://..."
}

# Status: pending_source (skips draft, directly to approval)
```

#### Step 2: Org Admin Reviews (Inter-Org Requires Org Approval)
```python
POST /api/transfers/{id}/approve-org/

# Org Admin checks:
- Financial clearance
- Inter-organization transfer rules
- Documentation completeness

Response:
{
  "status": "approved_source",
  "message": "Student cleared for transfer. Destination organization must accept."
}
```

#### Step 3: Generate Transfer Documents
```python
GET /api/transfers/{id}/documents/

# System generates:
- Transfer Certificate (TC)
- Academic Transcript
- Character Certificate
- Health Records
- No Objection Certificate (NOC)

# Parent receives downloadable package
```

#### Step 4: Destination Org Receives Notification
```
# Email sent to XYZ International School:
Subject: Incoming Transfer Request - John Doe

A transfer request has been initiated for student John Doe from ABC School.
Please review and process at: [Link to portal]

Documents attached:
- Transfer Certificate
- Academic Records
- Parent Consent
```

#### Step 5: Destination School Creates Incoming Transfer
```python
POST /api/transfers/incoming/

Request Body:
{
  "transfer_type": "inter_org_incoming",
  "student_details": {
    "name": "John Doe",
    "previous_school": "ABC School",
    "documents": [...]
  },
  "admission_class": "10-A",
  "admission_date": "2025-05-01"
}

# Status: pending_destination
```

#### Step 6: Destination Accepts & Enrolls
```python
POST /api/transfers/{id}/accept-and-enroll/

# Creates new student record in XYZ School
# Issues new admission number
# Original transfer at ABC marked as 'completed'
```

---

## Permission Matrix for Transfers

| Action | Parent | Student | School Staff | School Admin | Org Staff | Org Admin | Platform Admin |
|--------|--------|---------|--------------|--------------|-----------|-----------|----------------|
| **Initiate Intra-Org** | ✅ | ❌ | 📝 (Class only) | ✅ | ✅ | ✅ | ✅ |
| **Initiate Inter-Org** | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Approve Source** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ (override) | ✅ |
| **Approve Destination** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ (override) | ✅ |
| **Reject Transfer** | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| **Cancel Transfer** | ✅ (before approval) | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| **View Own Transfers** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **View School Transfers** | ❌ | ❌ | 👁️ | ✅ | ❌ | ❌ | ❌ |
| **View Org Transfers** | ❌ | ❌ | ❌ | ❌ | 👁️ | ✅ | ❌ |
| **View All Transfers** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Business Rules

### Rule 1: Financial Clearance
```python
def can_approve_transfer(student):
    """Source school must verify financial clearance"""
    outstanding_fees = student.get_outstanding_fees()
    if outstanding_fees > 0:
        return False, "Outstanding fees must be cleared before transfer"
    return True, None
```

### Rule 2: Capacity Check
```python
def can_accept_transfer(destination_class):
    """Destination class must have available capacity"""
    current_strength = destination_class.students.count()
    if current_strength >= destination_class.capacity:
        return False, "Class at full capacity"
    return True, None
```

### Rule 3: Academic Year Constraint
```python
def validate_transfer_date(effective_date, academic_year):
    """Transfers typically allowed only during specific periods"""
    allowed_periods = academic_year.get_transfer_windows()
    # Example: April-May (academic year end)
    #          November-December (mid-year with approval)

    if effective_date not in allowed_periods:
        return False, "Transfer date outside allowed window"
    return True, None
```

### Rule 4: Parent Consent (for Minor Students)
```python
def requires_parent_consent(student):
    """Students under 18 require parent consent"""
    if student.age < 18:
        return True
    return False
```

### Rule 5: Documentation Requirements
```python
REQUIRED_DOCUMENTS = {
    'intra_org': [
        'parent_consent',  # if applicable
        'previous_report_cards'
    ],
    'inter_org_outgoing': [
        'transfer_certificate',
        'academic_transcript',
        'character_certificate',
        'parent_consent',
        'noc_from_school'
    ],
    'inter_org_incoming': [
        'transfer_certificate',
        'academic_transcript',
        'birth_certificate',
        'address_proof',
        'previous_school_leaving_certificate'
    ]
}
```

---

## API Endpoints

### Student Transfer APIs

```python
# Create transfer request
POST /api/transfers/
{
  "student_id": "uuid",
  "transfer_type": "intra_org",
  "destination_school_id": "uuid",
  "reason": "..."
}

# Submit draft transfer
POST /api/transfers/{id}/submit/

# Approve by source school
POST /api/transfers/{id}/approve-source/
{
  "approval_notes": "...",
  "dues_cleared": true
}

# Accept by destination school
POST /api/transfers/{id}/accept/
{
  "acceptance_notes": "...",
  "assigned_class_id": "uuid"
}

# Reject transfer
POST /api/transfers/{id}/reject/
{
  "rejection_reason": "capacity_full",
  "rejection_notes": "..."
}

# Cancel transfer
POST /api/transfers/{id}/cancel/

# Complete transfer (admin only)
POST /api/transfers/{id}/complete/

# List transfers
GET /api/transfers/?status=pending&student_id=uuid

# Get transfer details
GET /api/transfers/{id}/

# Upload documents
POST /api/transfers/{id}/documents/
FormData: { document_type, file }

# Download transfer certificate
GET /api/transfers/{id}/transfer-certificate/
```

---

## Notifications & Alerts

### Email Notifications

1. **Transfer Initiated**: → Parent, Source School Admin
2. **Pending Source Approval**: → Source School Admin
3. **Source Approved**: → Parent, Destination School Admin
4. **Pending Destination Approval**: → Destination School Admin
5. **Transfer Accepted**: → Parent, Source School Admin
6. **Transfer Completed**: → All parties
7. **Transfer Rejected**: → Parent, Initiator
8. **Transfer Cancelled**: → All involved parties

### In-App Notifications

Dashboard widgets for:
- **School Admin**: Pending approval count badge
- **Parent**: Transfer status tracker
- **Org Admin**: Organization-wide transfer analytics

---

## Data Migration & History

### When Transfer Completes

**Source School**:
```python
# Student record marked as transferred
student.status = 'transferred'
student.transfer_date = effective_date
student.transferred_to_school_id = destination_school_id

# Historical data retained (read-only)
# Attendance, grades, achievements archived
```

**Destination School**:
```python
# New student record created (or existing updated)
student.school = destination_school
student.current_class = destination_class
student.admission_date = effective_date
student.admission_number = new_admission_number
student.status = 'active'

# Historical data linked (if intra-org)
student.previous_school_id = source_school_id
```

### Data Retention
- Source school retains read-only access for 7 years (compliance)
- Academic records linked via `StudentAcademicHistory` model
- Transfer documents stored permanently

---

## Security Considerations

1. **Multi-Tenancy**: Strict organization/school isolation
2. **Document Encryption**: All uploaded documents encrypted at rest
3. **Audit Trail**: Every action logged with timestamp and user
4. **Parent Verification**: OTP verification for parent-initiated transfers
5. **Financial Verification**: Integration with fees module
6. **Approval Chain**: Cannot skip approval stages (enforced by state machine)

---

## UI/UX Considerations

### Parent Portal - Transfer Request Flow

```
Step 1: Select Student
  ↓
Step 2: Choose Transfer Type
  ↓
Step 3: Select Destination School
  ↓
Step 4: Provide Reason & Documents
  ↓
Step 5: Review & Submit
  ↓
Step 6: Track Status (Real-time updates)
```

### School Admin Dashboard

```
┌─────────────────────────────────────┐
│  Pending Transfer Approvals: 5      │
│                                     │
│  ◉ John Doe → ABC High School       │
│    Review | Approve | Reject        │
│                                     │
│  ◉ Jane Smith → XYZ School          │
│    Review | Approve | Reject        │
└─────────────────────────────────────┘
```

---

## Best Practices

### 1. Clear Communication
- Status updates at every stage
- Reasons for rejection clearly stated
- Expected timelines communicated upfront

### 2. Documentation
- Maintain digital copies of all documents
- Auto-generate transfer certificates
- Provide document checklists to parents

### 3. Flexibility
- Allow admin override with justification
- Support bulk transfers for special cases
- Emergency transfer provisions

### 4. Analytics
- Track transfer trends (which schools, why)
- Identify capacity issues early
- Monitor rejection reasons

---

## Implementation Checklist

- [ ] Create `StudentTransfer` model
- [ ] Create API endpoints for transfer workflow
- [ ] Implement state machine for status transitions
- [ ] Build permission checks for each role
- [ ] Create transfer request form (Frontend)
- [ ] Build approval dashboard for admins
- [ ] Implement document upload/download
- [ ] Set up email notifications
- [ ] Create transfer certificate generation
- [ ] Build analytics dashboard
- [ ] Write unit tests for all workflows
- [ ] Document API for frontend integration

---

**Document Version**: 1.0
**Last Updated**: 2025-10-02
**Status**: Design Complete - Ready for Implementation
