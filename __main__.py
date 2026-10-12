import pulumi
import pulumi_azure_native as azure_native

config = pulumi.Config("pulumi-lab")
owner = config.require("owner")
environment = config.require("environment")
cost_center = config.require("costCenter")
storage_account_name = config.require("storageAccountName")
project = config.get("project") or "my-project"
demo_secret = config.require_secret("demoSecret")
pulumi.export("demo_secret", demo_secret)

common_tags = {
    "environment": environment,
    "project": project,
    "owner": owner,
    "cost-center": cost_center,
}

resource_group_resource = azure_native.resources.ResourceGroup("resourceGroupResource",
    resource_group_name=f"rg-pulumi-lab-{environment}",
    tags=(common_tags))

storage_account = azure_native.storage.StorageAccount("storageAccount",
    account_name=storage_account_name,
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

subnets = [
    {"name": "snet-app",  "prefix": "10.10.1.0/24"},
    {"name": "snet-data", "prefix": "10.10.2.0/24"},
    {"name": "snet-aks",  "prefix": "10.10.4.0/22"},
    {"name": "snet-mgmt", "prefix": "10.10.3.0/24"},
]

virtual_network = azure_native.network.VirtualNetwork("virtualNetwork",
    address_space={
        "address_prefixes": ["10.10.0.0/16"],
    },
    location=resource_group_resource.location,
    resource_group_name=resource_group_resource.name,
    tags=(common_tags),
    virtual_network_name=f"vnet-pulumi-lab-{environment}")

created_subnets = {}

for subnet in subnets:
    created_subnets[subnet["name"]] = azure_native.network.Subnet(
        f"subnet-{subnet['name']}",
        subnet_name=subnet["name"],
        address_prefix=subnet["prefix"],
        resource_group_name=resource_group_resource.name,
        virtual_network_name=virtual_network.name) 

pulumi.export("resource_group_name", resource_group_resource.name)
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("blob_container_name", blob_container.name)
pulumi.export("blob_endpoint", storage_account.primary_endpoints.blob)
pulumi.export("virtual_network_name", virtual_network.name)
pulumi.export("virtual_network_id", virtual_network.id)
pulumi.export("subnet_ids", {name: s.id for name, s in created_subnets.items()})