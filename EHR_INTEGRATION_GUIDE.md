# EHR Integration Guide - Athena Health

This guide explains how to integrate with Athena Health EHR system for patient lookup and appointment scheduling.

## ⚠️ IMPORTANT: Compliance Requirements

**BEFORE you enable EHR integration, you MUST:**

### 1. Legal & Compliance
- [ ] **Business Associate Agreement (BAA)** signed with Athena Health
- [ ] **HIPAA compliance audit** completed for your organization
- [ ] **Security risk assessment** performed
- [ ] **Incident response plan** in place
- [ ] **Privacy policy** updated to cover AI handling of PHI
- [ ] **Staff training** on HIPAA compliance completed

### 2. Technical Security
- [ ] **End-to-end encryption** for all PHI data in transit and at rest
- [ ] **PHI audit logging** for all access (who, what, when)
- [ ] **Data retention policies** implemented
- [ ] **Secure credential storage** (HSM or secrets manager)
- [ ] **Access controls** and role-based permissions
- [ ] **Penetration testing** completed

### 3. Athena Health Requirements
- [ ] **Production API access** granted by Athena
- [ ] **OAuth 2.0 credentials** obtained
- [ ] **Practice ID** and **Department IDs** confirmed
- [ ] **Appointment Type IDs** documented
- [ ] **API rate limits** understood and implemented

**If ANY of the above is not complete, DO NOT enable EHR integration!**

---

## Current Status: Skeleton Implementation

The current `AthenaClient` is a **stub/skeleton**. It provides:
- ✅ Data models (PatientInfo, EHRAppointment)
- ✅ Method signatures for all operations
- ✅ Type hints and documentation
- ❌ No actual API calls (returns empty/None)
- ❌ No OAuth2 implementation
- ❌ No PHI encryption

This allows you to:
1. Design your conversation flows
2. Test without real patient data
3. Understand the integration points
4. Implement when ready for production

---

## How to Enable EHR Integration

### Step 1: Get Athena Credentials

1. **Contact Athena Health Sales**
   - Request production API access
   - Sign BAA agreement
   - Complete onboarding

2. **Obtain OAuth Credentials**
   ```
   Client ID: your_client_id
   Client Secret: your_client_secret
   Practice ID: your_practice_id
   ```

3. **Get Configuration Details**
   - Department IDs (e.g., "123" for primary care)
   - Appointment Type IDs (e.g., "5" for new patient visit)
   - Provider IDs

### Step 2: Configure Environment

Edit `.env`:
```env
# Enable EHR integration
FEATURE_EHR_ATHENA=true

# Athena credentials
ATHENA_CLIENT_ID=your_client_id_here
ATHENA_CLIENT_SECRET=your_secret_here
ATHENA_PRACTICE_ID=123456
ATHENA_BASE_URL=https://api.athenahealth.com/v1

# Optional: specific department/provider
ATHENA_DEFAULT_DEPARTMENT_ID=123
ATHENA_DEFAULT_PROVIDER_ID=456
```

### Step 3: Implement OAuth2 Authentication

Replace the stub in `server/ehr/athena_client.py`:

```python
import httpx
from datetime import datetime, timedelta

class AthenaClient:
    async def authenticate(self) -> bool:
        """Authenticate with Athena Health API using OAuth2."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/oauth2/token",
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data["access_token"]
                    self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"])
                    logger.info("Athena authentication successful")
                    return True
                else:
                    logger.error(f"Athena auth failed: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.error(f"Athena authentication error: {e}")
            return False
```

### Step 4: Implement Patient Search

```python
async def find_patient(
    self,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    date_of_birth: Optional[datetime] = None,
) -> List[PatientInfo]:
    """Search for patients in EHR."""
    if not self.access_token:
        await self.authenticate()
    
    try:
        # Build search parameters
        params = {
            "firstname": first_name,
            "lastname": last_name,
            "homephone": phone,
        }
        if date_of_birth:
            params["dob"] = date_of_birth.strftime("%m/%d/%Y")
        
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{self.practice_id}/patients",
                params=params,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            
            if response.status_code == 200:
                data = response.json()
                patients = []
                
                for p in data.get("patients", []):
                    patients.append(PatientInfo(
                        patient_id=p["patientid"],
                        first_name=p["firstname"],
                        last_name=p["lastname"],
                        phone=p.get("homephone"),
                        email=p.get("email"),
                        date_of_birth=datetime.strptime(p["dob"], "%m/%d/%Y") if p.get("dob") else None,
                    ))
                
                # PHI AUDIT LOG
                logger.info(
                    "PHI_ACCESS",
                    extra={
                        "action": "patient_search",
                        "patient_count": len(patients),
                        "search_params": {k: "***" if k != "firstname" else v for k, v in params.items()}
                    }
                )
                
                return patients
            
            else:
                logger.error(f"Patient search failed: {response.status_code}")
                return []
    
    except Exception as e:
        logger.error(f"Patient search error: {e}")
        return []
```

### Step 5: Implement Appointment Scheduling

```python
async def get_open_slots(
    self,
    department_id: str,
    start_date: datetime,
    end_date: datetime,
    appointment_type_id: str,
) -> List[datetime]:
    """Get open appointment slots."""
    if not self.access_token:
        await self.authenticate()
    
    try:
        params = {
            "departmentid": department_id,
            "appointmenttypeid": appointment_type_id,
            "startdate": start_date.strftime("%m/%d/%Y"),
            "enddate": end_date.strftime("%m/%d/%Y"),
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/{self.practice_id}/appointments/open",
                params=params,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            
            if response.status_code == 200:
                data = response.json()
                slots = []
                
                for appointment in data.get("appointments", []):
                    slot_time = datetime.strptime(
                        f"{appointment['date']} {appointment['starttime']}",
                        "%m/%d/%Y %H:%M"
                    )
                    slots.append(slot_time)
                
                return slots
            
            else:
                logger.error(f"Get open slots failed: {response.status_code}")
                return []
    
    except Exception as e:
        logger.error(f"Get open slots error: {e}")
        return []


async def create_appointment(
    self,
    patient_id: str,
    department_id: str,
    appointment_type_id: str,
    start_time: datetime,
    reason: Optional[str] = None,
) -> Optional[EHRAppointment]:
    """Create a new appointment."""
    if not self.access_token:
        await self.authenticate()
    
    try:
        data = {
            "appointmenttypeid": appointment_type_id,
            "departmentid": department_id,
            "patientid": patient_id,
            "appointmentdate": start_time.strftime("%m/%d/%Y"),
            "appointmenttime": start_time.strftime("%H:%M"),
        }
        
        if reason:
            data["appointmentnote"] = reason
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{self.practice_id}/appointments",
                data=data,
                headers={"Authorization": f"Bearer {self.access_token}"},
            )
            
            if response.status_code == 200:
                result = response.json()
                appointment_id = result.get("appointmentid")
                
                # PHI AUDIT LOG
                logger.info(
                    "PHI_ACCESS",
                    extra={
                        "action": "appointment_created",
                        "appointment_id": appointment_id,
                        "patient_id": patient_id,
                    }
                )
                
                return EHRAppointment(
                    appointment_id=appointment_id,
                    patient_id=patient_id,
                    provider_id="",
                    start_time=start_time,
                    duration_minutes=30,
                    appointment_type=appointment_type_id,
                    status="scheduled",
                )
            
            else:
                logger.error(f"Create appointment failed: {response.status_code}")
                return None
    
    except Exception as e:
        logger.error(f"Create appointment error: {e}")
        return None
```

### Step 6: Add EHR Actions to Conversation

Update `server/llm/openai_gpt4o.py` to add EHR-specific functions:

```python
{
    "name": "lookup_patient",
    "description": "Look up patient in EHR system to verify identity or find records",
    "parameters": {
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "date_of_birth": {"type": "string", "description": "MM/DD/YYYY format"},
        },
        "required": ["last_name"]
    }
},
{
    "name": "check_ehr_availability",
    "description": "Check appointment availability in EHR for specific appointment type",
    "parameters": {
        "type": "object",
        "properties": {
            "appointment_type": {"type": "string", "enum": ["new_patient", "follow_up", "physical"]},
            "preferred_date": {"type": "string"},
        }
    }
}
```

---

## Security Best Practices

### 1. PHI Encryption

```python
from cryptography.fernet import Fernet

class PHIEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_phi(self, data: str) -> str:
        """Encrypt PHI data before storage."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_phi(self, encrypted: str) -> str:
        """Decrypt PHI data for use."""
        return self.cipher.decrypt(encrypted.encode()).decode()
```

### 2. Audit Logging

```python
async def log_phi_access(
    session: AsyncSession,
    action: str,
    patient_id: Optional[str],
    user_id: str,
    details: dict
):
    """Log all PHI access for HIPAA compliance."""
    log = AuditLog(
        event_type=f"PHI_{action}",
        event_data={
            "patient_id": patient_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": "...",
            **details
        },
        severity="critical"  # All PHI access is critical
    )
    await AuditLogRepository.create(session, log)
```

### 3. Minimum Necessary Rule

Only request PHI that's absolutely necessary:

```python
# BAD: Request full patient record
patient = await athena.get_patient(patient_id)

# GOOD: Request only what's needed for scheduling
slots = await athena.get_open_slots(department_id, start_date, end_date)
```

---

## Testing EHR Integration

### 1. Use Athena Sandbox

Athena provides a sandbox environment:
```env
ATHENA_BASE_URL=https://api.preview.platform.athenahealth.com/v1
```

### 2. Mock Patient Data

For development without real PHI:

```python
class MockAthenaClient(AthenaClient):
    async def find_patient(self, **kwargs):
        return [
            PatientInfo(
                patient_id="12345",
                first_name="Test",
                last_name="Patient",
                phone="+15551234567",
                email="test@example.com",
                date_of_birth=datetime(1990, 1, 1)
            )
        ]
```

### 3. Compliance Testing

- [ ] Test audit logging captures all PHI access
- [ ] Verify encryption at rest and in transit
- [ ] Test session timeout and auto-logout
- [ ] Verify minimum necessary access
- [ ] Test unauthorized access prevention

---

## Integration Architecture

```
Caller
  ↓
AI Receptionist
  ↓
Conversation Router recognizes patient scheduling
  ↓
LLM Function Call: "lookup_patient"
  ↓
AthenaClient.find_patient(name, dob)
  ↓
Athena Health API (OAuth2 authenticated)
  ↓
Returns: PatientInfo
  ↓
Store encrypted in database with audit log
  ↓
LLM Function Call: "get_ehr_slots"
  ↓
AthenaClient.get_open_slots(...)
  ↓
Present options to caller
  ↓
LLM Function Call: "create_ehr_appointment"
  ↓
AthenaClient.create_appointment(...)
  ↓
Confirm to caller + send SMS reminder
```

---

## Cost Considerations

**Athena Health API Pricing** (varies by contract):
- Patient lookup: ~$0.01 per search
- Slot availability: ~$0.02 per query
- Appointment creation: ~$0.05 per booking
- Appointment modification: ~$0.03 per change

**Typical call cost with EHR**:
- Base AI call: $0.07
- EHR operations: $0.08
- **Total: ~$0.15 per call with patient lookup and scheduling**

---

## Next Steps

1. **Contact Athena Health** to start onboarding
2. **Complete HIPAA compliance** assessment
3. **Sign BAA** with Athena and any cloud providers
4. **Implement OAuth2** authentication
5. **Implement patient search** and slot lookup
6. **Add PHI encryption** and audit logging
7. **Test in sandbox** environment
8. **Security audit** before production
9. **Staff training** on new system
10. **Gradual rollout** with monitoring

---

## Resources

- **Athena Health Developer Portal**: https://developer.athenahealth.com/
- **HIPAA Compliance Guide**: https://www.hhs.gov/hipaa/
- **Python HIPAA Library**: https://github.com/daticahealth/python-catalyze
- **OAuth 2.0 Guide**: https://oauth.net/2/

---

## Support

For EHR integration questions:
- **Athena Health Support**: apisupport@athenahealth.com
- **HIPAA Compliance**: Consult your organization's compliance officer
- **Technical Issues**: See project README for contact info

**Remember: EHR integration involves Protected Health Information (PHI). Take security and compliance seriously!**

