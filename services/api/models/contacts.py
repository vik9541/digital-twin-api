from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class EmailAddress(BaseModel):
    """Email address model"""
    address: EmailStr
    name: Optional[str] = None

class PhoneNumber(BaseModel):
    """Phone number model"""
    number: str
    type: str = "mobile"  # mobile, home, business, other

class Address(BaseModel):
    """Physical address model"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

class ContactCreate(BaseModel):
    """Model for creating a contact"""
    given_name: str = Field(..., description="First name")
    surname: Optional[str] = Field(None, description="Last name")
    display_name: Optional[str] = None
    email_addresses: List[EmailAddress] = []
    phone_numbers: List[PhoneNumber] = []
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    addresses: List[Address] = []
    notes: Optional[str] = None

class ContactUpdate(BaseModel):
    """Model for updating a contact"""
    given_name: Optional[str] = None
    surname: Optional[str] = None
    display_name: Optional[str] = None
    email_addresses: Optional[List[EmailAddress]] = None
    phone_numbers: Optional[List[PhoneNumber]] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    addresses: Optional[List[Address]] = None
    notes: Optional[str] = None

class ContactResponse(BaseModel):
    """Contact response model"""
    id: str
    given_name: Optional[str] = None
    surname: Optional[str] = None
    display_name: Optional[str] = None
    email_addresses: List[EmailAddress] = []
    phone_numbers: List[PhoneNumber] = []
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ContactsListResponse(BaseModel):
    """Response for list of contacts"""
    contacts: List[ContactResponse]
    total_count: int
    next_link: Optional[str] = None

class MSGraphTokenResponse(BaseModel):
    """Microsoft Graph token response"""
    access_token: str
    token_type: str
    expires_in: int
