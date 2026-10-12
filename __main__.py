import pulumi
import pulumi_azure_native as azure_native

common_tags = {
    "environment": "dev",
    "project": "my-project",
    "owner": "my-team",
    "cost-center": "demo-project",
}

resource_group_resource = azure_native.resources.ResourceGroup("resourceGroupResource",
    location="centralindia",
    resource_group_name="rg-pulumi-lab-dev",
    tags=(common_tags))

storage_account = azure_native.storage.StorageAccount("storageAccount",
    account_name="stpulumilabthiv01",
    allow_blob_public_access=False,

    kind=azure_native.storage.Kind.STORAGE_V2,
    location=resource_group_resource.location,
    minimum_tls_version=azure_native.storage.MinimumTlsVersion.TLS1_2,
    resource_group_name=resource_group_resource.name,
    sku={
        "name": azure_native.storage.SkuName.STANDARD_LRS,
    },
    tags=(common_tags))

blob_container = azure_native.storage.BlobContainer("blobContainer",
    account_name=storage_account.name,
    container_name="data",
    resource_group_name=resource_group_resource.name,
    public_access=azure_native.storage.PublicAccess.NONE)

pulumi.export("resource_group_name", resource_group_resource.name)
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("blob_container_name", blob_container.name)
pulumi.export("blob_endpoint", storage_account.primary_endpoints.blob)