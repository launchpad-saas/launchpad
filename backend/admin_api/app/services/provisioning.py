import httpx
from fastapi import HTTPException

class ProvisioningService:
    @staticmethod
    async def provision_tenant_schema(tenant_slug: str):
        """
        Calls the catalog_api internal endpoint to create the schema and run migrations.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://catalog_api:8000/api/v1/internal/provision",
                    json={"slug": tenant_slug},
                    timeout=60.0 # Give it enough time to run migrations
                )
                response.raise_for_status()
                print(f"Provisioning response: {response.json()}")
        except httpx.HTTPStatusError as e:
            print(f"Provisioning failed: {e.response.text}")
            raise HTTPException(status_code=500, detail="Failed to provision tenant database")
        except Exception as e:
            print(f"Connection to catalog_api failed: {str(e)}")
            raise HTTPException(status_code=500, detail="Provisioning service unreachable")