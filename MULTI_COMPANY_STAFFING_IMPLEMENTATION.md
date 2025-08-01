# Multi-Company Staffing & Recruitment Implementation Plan

## Overview

This document outlines the implementation plan for extending the existing HR system to support multi-company staffing and recruitment services. The implementation ensures **100% backward compatibility** while adding powerful staffing capabilities.

## Table of Contents

1. [Implementation Phases](#implementation-phases)
2. [Technical Architecture](#technical-architecture)
3. [Database Schema Changes](#database-schema-changes)
4. [Code Changes](#code-changes)
5. [Migration Strategy](#migration-strategy)
6. [Testing Plan](#testing-plan)
7. [Risk Mitigation](#risk-mitigation)
8. [Success Metrics](#success-metrics)

---

## Implementation Phases

### Phase 1: Database Schema Extension (Week 1)

#### Step 1.1: Employee Model Extension

**File**: `employee/models.py`

```python
# Add to EmployeeWorkInformation model
EMPLOYEE_MODE_CHOICES = [
    ('internal', _('Internal Employee')),
    ('direct_staffing', _('Direct Staffing (for other companies)')),
    ('agency_staffing', _('Agency Staffing (through staffing agency)')),
]

employee_mode = models.CharField(
    max_length=20,
    choices=EMPLOYEE_MODE_CHOICES,
    default='internal',  # All existing employees = internal
    verbose_name=_("Employee Mode")
)

# Staffing-specific fields (optional)
staffing_agency_id = models.ForeignKey(
    Company,
    on_delete=models.PROTECT,
    blank=True,
    null=True,
    related_name="agency_staffing_employees",
    verbose_name=_("Staffing Agency")
)
client_company_id = models.ForeignKey(
    Company,
    on_delete=models.PROTECT,
    blank=True,
    null=True,
    related_name="client_staffing_employees",
    verbose_name=_("Client Company")
)
billing_rate = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    null=True, 
    blank=True,
    verbose_name=_("Billing Rate ($/hr)")
)
pay_rate = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    null=True, 
    blank=True,
    verbose_name=_("Pay Rate ($/hr)")
)
contract_start_date = models.DateField(
    null=True, 
    blank=True, 
    verbose_name=_("Contract Start")
)
contract_end_date = models.DateField(
    null=True, 
    blank=True, 
    verbose_name=_("Contract End")
)
```

**Outcome**: All existing employees automatically become "internal" employees with no data loss.

#### Step 1.2: Recruitment Model Extension

**File**: `recruitment/models.py`

```python
# Add to Recruitment model
RECRUITMENT_TYPE_CHOICES = [
    ('internal', _('Internal Recruitment')),
    ('direct_staffing', _('Direct Staffing (for other companies)')),
    ('agency_staffing', _('Agency Staffing (through staffing agency)')),
]

recruitment_type = models.CharField(
    max_length=20,
    choices=RECRUITMENT_TYPE_CHOICES,
    default='internal',  # All existing recruitments = internal
    verbose_name=_("Recruitment Type")
)

# Client company for staffing recruitments
client_company_id = models.ForeignKey(
    Company,
    on_delete=models.PROTECT,
    blank=True,
    null=True,
    related_name="client_recruitments",
    verbose_name=_("Client Company")
)

# Staffing agency for agency recruitments
staffing_agency_id = models.ForeignKey(
    Company,
    on_delete=models.PROTECT,
    blank=True,
    null=True,
    related_name="agency_recruitments",
    verbose_name=_("Staffing Agency")
)

# Contract details for staffing
contract_start_date = models.DateField(
    null=True, 
    blank=True, 
    verbose_name=_("Contract Start Date")
)
contract_end_date = models.DateField(
    null=True, 
    blank=True, 
    verbose_name=_("Contract End Date")
)
billing_rate = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    null=True, 
    blank=True,
    verbose_name=_("Billing Rate ($/hr)")
)
pay_rate = models.DecimalField(
    max_digits=10, 
    decimal_places=2, 
    null=True, 
    blank=True,
    verbose_name=_("Pay Rate ($/hr)")
)
```

**Outcome**: All existing recruitments automatically become "internal" recruitments.

#### Step 1.3: Company Model Extension

**File**: `base/models.py`

```python
# Add to Company model
is_staffing_agency = models.BooleanField(
    default=False, 
    verbose_name=_("Staffing Agency")
)
is_client_company = models.BooleanField(
    default=False, 
    verbose_name=_("Client Company")
)
primary_contact_name = models.CharField(
    max_length=100, 
    blank=True, 
    null=True
)
primary_contact_email = models.EmailField(
    blank=True, 
    null=True
)
primary_contact_phone = models.CharField(
    max_length=20, 
    blank=True, 
    null=True
)
contract_terms = models.TextField(
    blank=True, 
    null=True
)
```

**Outcome**: Companies can be marked as staffing agencies or client companies.

---

### Phase 2: Filter & View Extensions (Week 2)

#### Step 2.1: Employee Filter Extension

**File**: `employee/filters.py`

```python
# Extend existing EmployeeFilter class
class EmployeeFilter(HorillaFilterSet):
    # ... existing filters stay exactly the same ...
    
    # ADD employee mode filter
    employee_mode = django_filters.ChoiceFilter(
        field_name="employee_work_info__employee_mode",
        label="Employee Type",
        choices=[
            ('internal', 'Internal Employee'),
            ('direct_staffing', 'Direct Staffing'),
            ('agency_staffing', 'Agency Staffing'),
        ],
    )
    
    # Staffing-specific filters
    client_company = django_filters.CharFilter(
        field_name="employee_work_info__client_company_id__company",
        lookup_expr="icontains",
        label="Client Company"
    )
    
    staffing_agency = django_filters.CharFilter(
        field_name="employee_work_info__staffing_agency_id__company",
        lookup_expr="icontains", 
        label="Staffing Agency"
    )
    
    # Contract date filters
    contract_start_from = django_filters.DateFilter(
        field_name="employee_work_info__contract_start_date",
        lookup_expr="gte",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    contract_end_to = django_filters.DateFilter(
        field_name="employee_work_info__contract_end_date", 
        lookup_expr="lte",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
```

**Outcome**: Users can filter employees by staffing type and client companies.

#### Step 2.2: Recruitment Filter Extension

**File**: `recruitment/filters.py`

```python
# Extend existing RecruitmentFilter class
class RecruitmentFilter(HorillaFilterSet):
    # ... existing filters stay exactly the same ...
    
    # ADD recruitment type filter
    recruitment_type = django_filters.ChoiceFilter(
        field_name="recruitment_type",
        label="Recruitment Type",
        choices=[
            ('internal', 'Internal Recruitment'),
            ('direct_staffing', 'Direct Staffing'),
            ('agency_staffing', 'Agency Staffing'),
        ],
    )
    
    # Client company filter
    client_company = django_filters.CharFilter(
        field_name="client_company_id__company",
        lookup_expr="icontains",
        label="Client Company"
    )
    
    # Staffing agency filter
    staffing_agency = django_filters.CharFilter(
        field_name="staffing_agency_id__company",
        lookup_expr="icontains",
        label="Staffing Agency"
    )
```

**Outcome**: Users can filter recruitments by type and client companies.

#### Step 2.3: View Extensions

**File**: `employee/views.py`

```python
# Extend existing employee_view
@login_required
def employee_view(request):
    # ... existing code stays exactly the same ...
    
    # ADD employee mode filtering
    employee_mode = request.GET.get('employee_mode')
    if employee_mode:
        queryset = queryset.filter(employee_work_info__employee_mode=employee_mode)
    
    # ADD staffing-specific filters
    client_company = request.GET.get('client_company')
    if client_company:
        queryset = queryset.filter(
            employee_work_info__client_company_id__company__icontains=client_company
        )
    
    staffing_agency = request.GET.get('staffing_agency')
    if staffing_agency:
        queryset = queryset.filter(
            employee_work_info__staffing_agency_id__company__icontains=staffing_agency
        )
    
    # ... rest of existing code unchanged ...
```

**File**: `recruitment/views.py`

```python
# Extend existing recruitment_view
@login_required
def recruitment_view(request):
    # ... existing code stays exactly the same ...
    
    # ADD recruitment type filtering
    recruitment_type = request.GET.get('recruitment_type')
    if recruitment_type:
        queryset = queryset.filter(recruitment_type=recruitment_type)
    
    # ADD client company filtering
    client_company = request.GET.get('client_company')
    if client_company:
        queryset = queryset.filter(
            client_company_id__company__icontains=client_company
        )
    
    # ADD staffing agency filtering
    staffing_agency = request.GET.get('staffing_agency')
    if staffing_agency:
        queryset = queryset.filter(
            staffing_agency_id__company__icontains=staffing_agency
        )
    
    # ... rest of existing code unchanged ...
```

**Outcome**: Existing views work exactly the same, with optional staffing filters.

---

### Phase 3: Form Extensions (Week 3)

#### Step 3.1: Employee Form Extension

**File**: `employee/forms.py`

```python
# Extend existing EmployeeWorkInformationForm
class EmployeeWorkInformationForm(forms.ModelForm):
    # ... existing fields stay exactly the same ...
    
    # ADD employee mode field
    employee_mode = forms.ChoiceField(
        choices=EmployeeWorkInformation.EMPLOYEE_MODE_CHOICES,
        initial='internal',
        label="Employee Type"
    )
    
    # Conditional staffing fields
    staffing_agency_id = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_staffing_agency=True),
        required=False,
        label="Staffing Agency"
    )
    client_company_id = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_client_company=True),
        required=False,
        label="Client Company"
    )
    billing_rate = forms.DecimalField(
        required=False,
        label="Billing Rate ($/hr)"
    )
    pay_rate = forms.DecimalField(
        required=False,
        label="Pay Rate ($/hr)"
    )
    contract_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Contract Start Date"
    )
    contract_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Contract End Date"
    )
    
    class Meta:
        model = EmployeeWorkInformation
        fields = [
            # ... existing fields ...
            'employee_mode',
            'staffing_agency_id',
            'client_company_id', 
            'billing_rate',
            'pay_rate',
            'contract_start_date',
            'contract_end_date'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show staffing fields only when needed
        if self.instance and self.instance.pk:
            if self.instance.employee_mode == 'internal':
                self.fields['staffing_agency_id'].widget = forms.HiddenInput()
                self.fields['client_company_id'].widget = forms.HiddenInput()
                self.fields['billing_rate'].widget = forms.HiddenInput()
                self.fields['pay_rate'].widget = forms.HiddenInput()
```

**Outcome**: Forms dynamically show relevant fields based on employee type.

#### Step 3.2: Recruitment Form Extension

**File**: `recruitment/forms.py`

```python
# Extend existing RecruitmentForm
class RecruitmentForm(forms.ModelForm):
    # ... existing fields stay exactly the same ...
    
    # ADD recruitment type field
    recruitment_type = forms.ChoiceField(
        choices=Recruitment.RECRUITMENT_TYPE_CHOICES,
        initial='internal',
        label="Recruitment Type"
    )
    
    # Conditional staffing fields
    client_company_id = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_client_company=True),
        required=False,
        label="Client Company"
    )
    staffing_agency_id = forms.ModelChoiceField(
        queryset=Company.objects.filter(is_staffing_agency=True),
        required=False,
        label="Staffing Agency"
    )
    billing_rate = forms.DecimalField(
        required=False,
        label="Billing Rate ($/hr)"
    )
    pay_rate = forms.DecimalField(
        required=False,
        label="Pay Rate ($/hr)"
    )
    contract_start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Contract Start Date"
    )
    contract_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Contract End Date"
    )
    
    class Meta:
        model = Recruitment
        fields = [
            # ... existing fields ...
            'recruitment_type',
            'client_company_id',
            'staffing_agency_id',
            'billing_rate',
            'pay_rate',
            'contract_start_date',
            'contract_end_date'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show staffing fields only when needed
        if self.instance and self.instance.pk:
            if self.instance.recruitment_type == 'internal':
                self.fields['client_company_id'].widget = forms.HiddenInput()
                self.fields['staffing_agency_id'].widget = forms.HiddenInput()
                self.fields['billing_rate'].widget = forms.HiddenInput()
                self.fields['pay_rate'].widget = forms.HiddenInput()
```

**Outcome**: Forms dynamically show relevant fields based on recruitment type.

---

### Phase 4: Template Extensions (Week 4)

#### Step 4.1: Employee Template Extension

**File**: `employee/templates/employee/employee_view.html`

```html
<!-- Existing employee info stays exactly the same -->

<!-- ADD conditional staffing section -->
{% if employee.employee_work_info.employee_mode != 'internal' %}
<div class="oh-card">
    <div class="oh-card__header">
        <h5 class="oh-card__title">
            {% if employee.employee_work_info.employee_mode == 'direct_staffing' %}
                Direct Staffing Information
            {% else %}
                Agency Staffing Information
            {% endif %}
        </h5>
    </div>
    <div class="oh-card__body">
        <div class="row">
            {% if employee.employee_work_info.employee_mode == 'agency_staffing' %}
            <div class="col-md-6">
                <label>Staffing Agency:</label>
                <p>{{ employee.employee_work_info.staffing_agency_id.company }}</p>
            </div>
            {% endif %}
            <div class="col-md-6">
                <label>Client Company:</label>
                <p>{{ employee.employee_work_info.client_company_id.company }}</p>
            </div>
            <div class="col-md-6">
                <label>Billing Rate:</label>
                <p>${{ employee.employee_work_info.billing_rate }}/hr</p>
            </div>
            <div class="col-md-6">
                <label>Pay Rate:</label>
                <p>${{ employee.employee_work_info.pay_rate }}/hr</p>
            </div>
            <div class="col-md-6">
                <label>Contract Period:</label>
                <p>{{ employee.employee_work_info.contract_start_date }} - {{ employee.employee_work_info.contract_end_date|default:"Ongoing" }}</p>
            </div>
        </div>
    </div>
</div>
{% endif %}
```

**Outcome**: Employee profiles show staffing info only when relevant.

#### Step 4.2: Recruitment Template Extension

**File**: `recruitment/templates/recruitment/recruitment_view.html`

```html
<!-- Existing recruitment info stays exactly the same -->

<!-- ADD conditional staffing section -->
{% if recruitment.recruitment_type != 'internal' %}
<div class="oh-card">
    <div class="oh-card__header">
        <h5 class="oh-card__title">
            {% if recruitment.recruitment_type == 'direct_staffing' %}
                Direct Staffing Information
            {% else %}
                Agency Staffing Information
            {% endif %}
        </h5>
    </div>
    <div class="oh-card__body">
        <div class="row">
            {% if recruitment.recruitment_type == 'agency_staffing' %}
            <div class="col-md-6">
                <label>Staffing Agency:</label>
                <p>{{ recruitment.staffing_agency_id.company }}</p>
            </div>
            {% endif %}
            <div class="col-md-6">
                <label>Client Company:</label>
                <p>{{ recruitment.client_company_id.company }}</p>
            </div>
            <div class="col-md-6">
                <label>Billing Rate:</label>
                <p>${{ recruitment.billing_rate }}/hr</p>
            </div>
            <div class="col-md-6">
                <label>Pay Rate:</label>
                <p>${{ recruitment.pay_rate }}/hr</p>
            </div>
            <div class="col-md-6">
                <label>Contract Period:</label>
                <p>{{ recruitment.contract_start_date }} - {{ recruitment.contract_end_date|default:"Ongoing" }}</p>
            </div>
        </div>
    </div>
</div>
{% endif %}
```

**Outcome**: Recruitment details show staffing info only when relevant.

#### Step 4.3: Filter Template Extension

**File**: `employee/templates/employee_filters.html`

```html
<!-- ADD to existing filters -->
<div class="oh-input-group">
    <label class="oh-label">Employee Type</label>
    <select name="employee_mode" class="oh-input oh-input__icon">
        <option value="">All Types</option>
        <option value="internal">Internal Employee</option>
        <option value="direct_staffing">Direct Staffing</option>
        <option value="agency_staffing">Agency Staffing</option>
    </select>
</div>

<!-- Existing filters stay exactly the same -->
```

**File**: `recruitment/templates/recruitment_filters.html`

```html
<!-- ADD to existing filters -->
<div class="oh-input-group">
    <label class="oh-label">Recruitment Type</label>
    <select name="recruitment_type" class="oh-input oh-input__icon">
        <option value="">All Types</option>
        <option value="internal">Internal Recruitment</option>
        <option value="direct_staffing">Direct Staffing</option>
        <option value="agency_staffing">Agency Staffing</option>
    </select>
</div>

<!-- Existing filters stay exactly the same -->
```

**Outcome**: Users can filter by employee/recruitment type.

---

### Phase 5: Database Migration (Week 5)

#### Step 5.1: Safe Migration Strategy

**File**: `employee/migrations/XXXX_add_employee_modes.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('employee', 'previous_migration'),
    ]
    
    operations = [
        # ADD employee mode field (all existing employees = internal)
        migrations.AddField(
            model_name='employeeworkinformation',
            name='employee_mode',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('internal', 'Internal Employee'),
                    ('direct_staffing', 'Direct Staffing (for other companies)'),
                    ('agency_staffing', 'Agency Staffing (through staffing agency)'),
                ],
                default='internal',  # All existing employees become internal
            ),
        ),
        
        # ADD staffing fields (all optional)
        migrations.AddField(
            model_name='employeeworkinformation',
            name='staffing_agency_id',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name='agency_staffing_employees',
                to='base.company',
            ),
        ),
        migrations.AddField(
            model_name='employeeworkinformation',
            name='client_company_id',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name='client_staffing_employees',
                to='base.company',
            ),
        ),
        migrations.AddField(
            model_name='employeeworkinformation',
            name='billing_rate',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='employeeworkinformation',
            name='pay_rate',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='employeeworkinformation',
            name='contract_start_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='employeeworkinformation',
            name='contract_end_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
```

**File**: `recruitment/migrations/XXXX_add_recruitment_types.py`

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('recruitment', 'previous_migration'),
    ]
    
    operations = [
        # ADD recruitment type field (all existing recruitments = internal)
        migrations.AddField(
            model_name='recruitment',
            name='recruitment_type',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('internal', 'Internal Recruitment'),
                    ('direct_staffing', 'Direct Staffing (for other companies)'),
                    ('agency_staffing', 'Agency Staffing (through staffing agency)'),
                ],
                default='internal',  # All existing recruitments become internal
            ),
        ),
        
        # ADD staffing fields (all optional)
        migrations.AddField(
            model_name='recruitment',
            name='client_company_id',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name='client_recruitments',
                to='base.company',
            ),
        ),
        migrations.AddField(
            model_name='recruitment',
            name='staffing_agency_id',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name='agency_recruitments',
                to='base.company',
            ),
        ),
        migrations.AddField(
            model_name='recruitment',
            name='contract_start_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recruitment',
            name='contract_end_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='recruitment',
            name='billing_rate',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name='recruitment',
            name='pay_rate',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
            ),
        ),
    ]
```

**Outcome**: Zero downtime migration with full backward compatibility.

#### Step 5.2: Data Validation

```python
# Post-migration validation script
def validate_migration():
    # Verify all existing employees are internal
    internal_count = EmployeeWorkInformation.objects.filter(employee_mode='internal').count()
    total_count = EmployeeWorkInformation.objects.count()
    assert internal_count == total_count, "All employees should be internal"
    
    # Verify all existing recruitments are internal
    internal_recruitment_count = Recruitment.objects.filter(recruitment_type='internal').count()
    total_recruitment_count = Recruitment.objects.count()
    assert internal_recruitment_count == total_recruitment_count, "All recruitments should be internal"
    
    print("✅ Migration validation successful")
```

**Outcome**: Confirmed data integrity and system stability.

---

### Phase 6: Testing & Validation (Week 6)

#### Step 6.1: Backward Compatibility Testing

**Test Scenarios**:

```python
# Test existing functionality unchanged
def test_backward_compatibility():
    # 1. All existing employee views work unchanged
    response = client.get('/employee/')
    assert response.status_code == 200
    
    # 2. All existing recruitment views work unchanged
    response = client.get('/recruitment/')
    assert response.status_code == 200
    
    # 3. All existing filters work unchanged
    response = client.get('/employee/?department=IT')
    assert response.status_code == 200
    
    # 4. All existing forms work unchanged
    response = client.get('/employee/create/')
    assert response.status_code == 200
```

**Outcome**: 100% backward compatibility confirmed.

#### Step 6.2: New Functionality Testing

**Test Scenarios**:

```python
# Test new staffing scenarios
def test_staffing_functionality():
    # 1. Internal employees (existing functionality)
    internal_employee = EmployeeWorkInformation.objects.create(
        employee_mode='internal',
        employee_id=employee
    )
    assert internal_employee.employee_mode == 'internal'
    
    # 2. Direct staffing employees
    direct_staffing = EmployeeWorkInformation.objects.create(
        employee_mode='direct_staffing',
        employee_id=employee,
        client_company_id=client_company,
        billing_rate=75.00,
        pay_rate=50.00
    )
    assert direct_staffing.employee_mode == 'direct_staffing'
    
    # 3. Agency staffing employees
    agency_staffing = EmployeeWorkInformation.objects.create(
        employee_mode='agency_staffing',
        employee_id=employee,
        staffing_agency_id=staffing_agency,
        client_company_id=client_company,
        billing_rate=80.00,
        pay_rate=45.00
    )
    assert agency_staffing.employee_mode == 'agency_staffing'
    
    # 4. Internal recruitments
    internal_recruitment = Recruitment.objects.create(
        recruitment_type='internal',
        title="Internal Position"
    )
    assert internal_recruitment.recruitment_type == 'internal'
    
    # 5. Direct staffing recruitments
    direct_recruitment = Recruitment.objects.create(
        recruitment_type='direct_staffing',
        title="Client Position",
        client_company_id=client_company,
        billing_rate=75.00,
        pay_rate=50.00
    )
    assert direct_recruitment.recruitment_type == 'direct_staffing'
    
    # 6. Agency staffing recruitments
    agency_recruitment = Recruitment.objects.create(
        recruitment_type='agency_staffing',
        title="Agency Position",
        staffing_agency_id=staffing_agency,
        client_company_id=client_company,
        billing_rate=80.00,
        pay_rate=45.00
    )
    assert agency_recruitment.recruitment_type == 'agency_staffing'
```

**Outcome**: All new staffing features work correctly.

---

### Phase 7: Documentation & Training (Week 7)

#### Step 7.1: User Documentation

**File**: `docs/STAFFING_USER_GUIDE.md`

```markdown
# Staffing User Guide

## Overview
This guide explains how to use the new staffing features in the HR system.

## Employee Types

### Internal Employees
- Standard employees working directly for your company
- No additional configuration needed

### Direct Staffing Employees
- Employees working directly for client companies
- Requires client company configuration
- Track billing rates vs pay rates

### Agency Staffing Employees
- Employees working through staffing agencies
- Requires staffing agency and client company configuration
- Track agency fees and client billing

## Creating Staffing Employees

1. Go to Employee Management
2. Click "Add Employee"
3. Select employee mode (Internal/Direct Staffing/Agency Staffing)
4. Fill in staffing-specific fields if applicable
5. Save employee

## Creating Staffing Recruitments

1. Go to Recruitment Management
2. Click "Add Recruitment"
3. Select recruitment type (Internal/Direct Staffing/Agency Staffing)
4. Fill in staffing-specific fields if applicable
5. Save recruitment

## Filtering and Reporting

- Use employee type filter to view specific employee types
- Use recruitment type filter to view specific recruitment types
- Generate staffing-specific reports
- Track profitability with billing vs pay rates
```

**Outcome**: Users understand how to use new staffing features.

#### Step 7.2: Admin Training

**File**: `docs/STAFFING_ADMIN_GUIDE.md`

```markdown
# Staffing Admin Guide

## Company Configuration

### Setting Up Client Companies
1. Go to Company Management
2. Create or edit company
3. Check "Client Company" checkbox
4. Add contact information
5. Save company

### Setting Up Staffing Agencies
1. Go to Company Management
2. Create or edit company
3. Check "Staffing Agency" checkbox
4. Add contact information
5. Save company

## Managing Staffing Relationships

### Direct Staffing
- Employee works directly for client company
- Your company bills client directly
- Track billing rate vs employee pay rate

### Agency Staffing
- Employee works through staffing agency
- Agency bills client, pays your company
- Track agency fees and client billing

## Contract Management

### Contract Periods
- Set contract start and end dates
- Monitor contract renewals
- Track contract profitability

### Billing Management
- Set billing rates for clients
- Set pay rates for employees
- Calculate profit margins
- Generate billing reports
```

**Outcome**: Administrators can effectively manage staffing operations.

---

## Technical Architecture

### Database Schema

```
Company (base)
├── is_staffing_agency (Boolean)
├── is_client_company (Boolean)
├── primary_contact_name (CharField)
├── primary_contact_email (EmailField)
├── primary_contact_phone (CharField)
└── contract_terms (TextField)

EmployeeWorkInformation (employee)
├── employee_mode (CharField)
├── staffing_agency_id (FK to Company)
├── client_company_id (FK to Company)
├── billing_rate (Decimal)
├── pay_rate (Decimal)
├── contract_start_date (Date)
└── contract_end_date (Date)

Recruitment (recruitment)
├── recruitment_type (CharField)
├── client_company_id (FK to Company)
├── staffing_agency_id (FK to Company)
├── contract_start_date (Date)
├── contract_end_date (Date)
├── billing_rate (Decimal)
└── pay_rate (Decimal)
```

### Code Structure

```
employee/
├── models.py (extended with staffing fields)
├── filters.py (extended with staffing filters)
├── forms.py (extended with staffing forms)
├── views.py (extended with staffing logic)
└── templates/ (extended with staffing sections)

recruitment/
├── models.py (extended with staffing fields)
├── filters.py (extended with staffing filters)
├── forms.py (extended with staffing forms)
├── views.py (extended with staffing logic)
└── templates/ (extended with staffing sections)

base/
└── models.py (extended with company types)
```

---

## Migration Strategy

### Safe Migration Principles

1. **Zero Data Loss**: All existing data preserved
2. **Backward Compatibility**: All existing functionality unchanged
3. **Optional Features**: New features are opt-in
4. **Gradual Rollout**: Features can be enabled gradually
5. **Rollback Plan**: Can disable new features if needed

### Migration Steps

1. **Add Fields**: Add new fields with safe defaults
2. **Update Code**: Extend existing code with new functionality
3. **Test Thoroughly**: Validate all existing and new functionality
4. **Deploy**: Deploy with new features disabled by default
5. **Enable Features**: Gradually enable new features as needed

---

## Testing Plan

### Backward Compatibility Tests

- [ ] All existing employee views work unchanged
- [ ] All existing recruitment views work unchanged
- [ ] All existing filters work unchanged
- [ ] All existing forms work unchanged
- [ ] All existing templates render correctly
- [ ] All existing API endpoints work unchanged

### New Functionality Tests

- [ ] Internal employees work as before
- [ ] Direct staffing employees work correctly
- [ ] Agency staffing employees work correctly
- [ ] Internal recruitments work as before
- [ ] Direct staffing recruitments work correctly
- [ ] Agency staffing recruitments work correctly
- [ ] Staffing filters work correctly
- [ ] Staffing forms work correctly
- [ ] Staffing templates render correctly

### Integration Tests

- [ ] Company hierarchy works with staffing
- [ ] Department hierarchy works with staffing
- [ ] Job position hierarchy works with staffing
- [ ] Billing calculations work correctly
- [ ] Contract management works correctly
- [ ] Reporting works with staffing data

---

## Risk Mitigation

### Data Safety

- **Safe Defaults**: All new fields have safe default values
- **Optional Fields**: All new fields are optional (null=True)
- **Migration Testing**: Thorough testing of migration scripts
- **Backup Strategy**: Full database backup before migration

### Backward Compatibility

- **Additive Changes**: Only add new code, don't modify existing
- **Optional Features**: New features are opt-in
- **Default Behavior**: Existing behavior unchanged by default
- **Feature Flags**: Can disable new features if needed

### Gradual Adoption

- **Phase Rollout**: Implement in phases
- **User Training**: Comprehensive user training
- **Documentation**: Complete documentation
- **Support**: Dedicated support for new features

### Rollback Plan

- **Database Rollback**: Migration scripts are reversible
- **Code Rollback**: Can revert code changes
- **Feature Disable**: Can disable new features
- **Data Recovery**: Can recover from backup if needed

---

## Success Metrics

### Technical Metrics

- [ ] Zero data loss during migration
- [ ] 100% backward compatibility maintained
- [ ] All existing functionality preserved
- [ ] New staffing features working correctly
- [ ] Performance impact < 5%
- [ ] Zero downtime during deployment

### Business Metrics

- [ ] Ability to handle multiple client companies
- [ ] Ability to track staffing profitability
- [ ] Enhanced reporting capabilities
- [ ] Improved operational efficiency
- [ ] Reduced manual tracking of staffing relationships

### User Adoption Metrics

- [ ] Existing users continue working unchanged
- [ ] New staffing features adopted gradually
- [ ] Positive user feedback on new capabilities
- [ ] Reduced manual tracking of staffing relationships
- [ ] Increased user satisfaction scores

---

## Implementation Timeline

| Week | Phase | Description | Deliverables |
|------|-------|-------------|--------------|
| 1 | Database Schema | Add staffing fields to models | Updated models, migrations |
| 2 | Filter & Views | Extend existing filters and views | Updated filters, views |
| 3 | Forms | Extend existing forms | Updated forms |
| 4 | Templates | Extend existing templates | Updated templates |
| 5 | Migration | Deploy database changes | Migration scripts, validation |
| 6 | Testing | Comprehensive testing | Test results, bug fixes |
| 7 | Documentation | User and admin guides | Documentation, training materials |

---

## Conclusion

This implementation plan ensures **zero disruption** to current operations while adding powerful multi-company staffing capabilities. The approach prioritizes:

1. **Backward Compatibility**: All existing functionality preserved
2. **Data Safety**: Zero data loss during migration
3. **Gradual Adoption**: New features are opt-in
4. **Comprehensive Testing**: Thorough validation of all changes
5. **User Training**: Complete documentation and training

The result is a robust, scalable staffing and recruitment system that supports internal operations while enabling multi-company staffing services. 