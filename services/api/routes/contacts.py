from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
import httpx
import os

from api.models.contacts import (
    ContactCreate,
    ContactUpdate,
    ContactResponse,
    ContactsListResponse,
    EmailAddress,
    PhoneNumber
)

router = APIRouter(prefix="/contacts", tags=["contacts"])

# Microsoft Graph API endpoints
GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


class MSGraphClient:
    """Microsoft Graph API client"""
    
    def __init__(self):
        self.client_id = os.environ.get("MS_CLIENT_ID")
        self.client_secret = os.environ.get("MS_CLIENT_SECRET")
        self.tenant_id = os.environ.get("MS_TENANT_ID")
        self.access_token = os.environ.get("MS_ACCESS_TOKEN")  # User token (delegated)
        
    def _check_config(self):
        """Check if MS Graph is configured"""
        if not self.access_token:
            if not all([self.client_id, self.client_secret, self.tenant_id]):
                raise HTTPException(
                    status_code=500, 
                    detail="Microsoft Graph API not configured. Set MS_ACCESS_TOKEN or MS_CLIENT_ID/MS_CLIENT_SECRET/MS_TENANT_ID"
                )
    
    async def get_headers(self) -> dict:
        """Get authorization headers"""
        self._check_config()
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _parse_contact(self, data: dict) -> ContactResponse:
        """Parse Graph API contact to ContactResponse"""
        email_addresses = []
        for email in data.get("emailAddresses", []):
            email_addresses.append(EmailAddress(
                address=email.get("address", ""),
                name=email.get("name")
            ))
        
        phone_numbers = []
        for phone_type in ["mobilePhone", "businessPhones", "homePhones"]:
            phones = data.get(phone_type)
            if phones:
                if isinstance(phones, str):
                    phone_numbers.append(PhoneNumber(number=phones, type="mobile"))
                elif isinstance(phones, list):
                    for p in phones:
                        phone_numbers.append(PhoneNumber(number=p, type=phone_type.replace("Phones", "")))
        
        return ContactResponse(
            id=data.get("id", ""),
            given_name=data.get("givenName"),
            surname=data.get("surname"),
            display_name=data.get("displayName"),
            email_addresses=email_addresses,
            phone_numbers=phone_numbers,
            company_name=data.get("companyName"),
            job_title=data.get("jobTitle"),
            created_at=data.get("createdDateTime"),
            updated_at=data.get("lastModifiedDateTime")
        )


def get_graph_client() -> MSGraphClient:
    """Dependency to get MS Graph client"""
    return MSGraphClient()


@router.get("/", response_model=ContactsListResponse)
async def list_contacts(
    top: int = Query(50, le=100, description="Number of contacts to return"),
    skip: int = Query(0, description="Number of contacts to skip"),
    search: Optional[str] = Query(None, description="Search query"),
    client: MSGraphClient = Depends(get_graph_client)
):
    """
    List contacts from Microsoft 365 / Outlook
    
    Requires: MS_ACCESS_TOKEN environment variable with delegated permissions
    """
    headers = await client.get_headers()
    
    params = {
        "$top": top,
        "$skip": skip,
        "$orderby": "displayName",
        "$select": "id,givenName,surname,displayName,emailAddresses,mobilePhone,businessPhones,homePhones,companyName,jobTitle,createdDateTime,lastModifiedDateTime"
    }
    
    if search:
        params["$search"] = f'"displayName:{search}" OR "emailAddresses/address:{search}"'
        headers["ConsistencyLevel"] = "eventual"
    
    async with httpx.AsyncClient() as http:
        response = await http.get(
            f"{GRAPH_API_BASE}/me/contacts",
            headers=headers,
            params=params
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Graph API error: {response.text}"
            )
        
        data = response.json()
        contacts = [client._parse_contact(c) for c in data.get("value", [])]
        
        return ContactsListResponse(
            contacts=contacts,
            total_count=len(contacts),
            next_link=data.get("@odata.nextLink")
        )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: str,
    client: MSGraphClient = Depends(get_graph_client)
):
    """Get a specific contact by ID"""
    headers = await client.get_headers()
    
    async with httpx.AsyncClient() as http:
        response = await http.get(
            f"{GRAPH_API_BASE}/me/contacts/{contact_id}",
            headers=headers
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Graph API error: {response.text}"
            )
        
        return client._parse_contact(response.json())


@router.post("/", response_model=ContactResponse, status_code=201)
async def create_contact(
    contact: ContactCreate,
    client: MSGraphClient = Depends(get_graph_client)
):
    """Create a new contact in Outlook"""
    headers = await client.get_headers()
    
    # Build Graph API payload
    payload = {
        "givenName": contact.given_name,
        "surname": contact.surname,
        "displayName": contact.display_name or f"{contact.given_name} {contact.surname or ''}".strip(),
        "companyName": contact.company_name,
        "jobTitle": contact.job_title,
        "personalNotes": contact.notes,
        "emailAddresses": [
            {"address": e.address, "name": e.name} for e in contact.email_addresses
        ],
        "businessPhones": [p.number for p in contact.phone_numbers if p.type == "business"],
        "homePhones": [p.number for p in contact.phone_numbers if p.type == "home"],
        "mobilePhone": next((p.number for p in contact.phone_numbers if p.type == "mobile"), None)
    }
    
    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}
    
    async with httpx.AsyncClient() as http:
        response = await http.post(
            f"{GRAPH_API_BASE}/me/contacts",
            headers=headers,
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Graph API error: {response.text}"
            )
        
        return client._parse_contact(response.json())


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact: ContactUpdate,
    client: MSGraphClient = Depends(get_graph_client)
):
    """Update an existing contact"""
    headers = await client.get_headers()
    
    # Build payload with only provided fields
    payload = {}
    
    if contact.given_name is not None:
        payload["givenName"] = contact.given_name
    if contact.surname is not None:
        payload["surname"] = contact.surname
    if contact.display_name is not None:
        payload["displayName"] = contact.display_name
    if contact.company_name is not None:
        payload["companyName"] = contact.company_name
    if contact.job_title is not None:
        payload["jobTitle"] = contact.job_title
    if contact.notes is not None:
        payload["personalNotes"] = contact.notes
    if contact.email_addresses is not None:
        payload["emailAddresses"] = [
            {"address": e.address, "name": e.name} for e in contact.email_addresses
        ]
    if contact.phone_numbers is not None:
        payload["businessPhones"] = [p.number for p in contact.phone_numbers if p.type == "business"]
        payload["homePhones"] = [p.number for p in contact.phone_numbers if p.type == "home"]
        payload["mobilePhone"] = next((p.number for p in contact.phone_numbers if p.type == "mobile"), None)
    
    async with httpx.AsyncClient() as http:
        response = await http.patch(
            f"{GRAPH_API_BASE}/me/contacts/{contact_id}",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Graph API error: {response.text}"
            )
        
        return client._parse_contact(response.json())


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: str,
    client: MSGraphClient = Depends(get_graph_client)
):
    """Delete a contact"""
    headers = await client.get_headers()
    
    async with httpx.AsyncClient() as http:
        response = await http.delete(
            f"{GRAPH_API_BASE}/me/contacts/{contact_id}",
            headers=headers
        )
        
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        if response.status_code not in [200, 204]:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Graph API error: {response.text}"
            )


@router.get("/sync/status")
async def sync_status(client: MSGraphClient = Depends(get_graph_client)):
    """Check Microsoft Graph API connection status"""
    try:
        headers = await client.get_headers()
        
        async with httpx.AsyncClient() as http:
            response = await http.get(
                f"{GRAPH_API_BASE}/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user = response.json()
                return {
                    "status": "connected",
                    "user": user.get("displayName"),
                    "email": user.get("mail") or user.get("userPrincipalName"),
                    "provider": "Microsoft Graph API"
                }
            else:
                return {
                    "status": "error",
                    "error": response.text
                }
    except HTTPException as e:
        return {
            "status": "not_configured",
            "error": e.detail
        }
