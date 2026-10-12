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
key_vault_name = config.require("keyVaultName")
client = azure_native.authorization.get_client_config()

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

azure_native_vault_resource = azure_native.keyvault.Vault("azure-nativeVaultResource",
    properties={
        "sku": {
            "family": "A",
            "name": azure_native.keyvault.SkuName.STANDARD,
        },
        "tenant_id": client.tenant_id,
        "enable_rbac_authorization": True,
        "enabled_for_template_deployment": False,
        },


    resource_group_name=resource_group_resource.name,
    location=resource_group_resource.location,
    tags=common_tags,
    vault_name=key_vault_name)

secrets_officer_role_id = f"/subscriptions/{client.subscription_id}/providers/Microsoft.Authorization/roleDefinitions/b86a8fe4-44ce-4948-aee5-eccb2c155cd7"

kv_role = azure_native.authorization.RoleAssignment("kvSecretsOfficer",
    scope=azure_native_vault_resource.id,
    principal_id=client.object_id,
    principal_type="User",
    role_definition_id=secrets_officer_role_id)

kv_secret = azure_native.keyvault.Secret("demoSecret",
    secret_name="demo-Secret",
    vault_name=azure_native_vault_resource.name,
    resource_group_name=resource_group_resource.name,
    properties={
        "value": demo_secret,
    })

pulumi.export("resource_group_name", resource_group_resource.name)
pulumi.export("storage_account_name", storage_account.name)
pulumi.export("blob_container_name", blob_container.name)
pulumi.export("blob_endpoint", storage_account.primary_endpoints.blob)
pulumi.export("virtual_network_name", virtual_network.name)
pulumi.export("virtual_network_id", virtual_network.id)
pulumi.export("subnet_ids", {name: s.id for name, s in created_subnets.items()})
pulumi.export("key_vault_name", azure_native_vault_resource.name)
pulumi.export("key_vault_uri", azure_native_vault_resource.properties.vault_uri)
pulumi.export("secret_uri", pulumi.Output.concat(azure_native_vault_resource.properties.vault_uri, "secrets/", kv_secret.name))
pulumi.export("kv_summary",
               pulumi.Output.all(azure_native_vault_resource.name, azure_native_vault_resource.properties.vault_uri, kv_secret.name).apply
                    (lambda args: f"Key Vault Name: {args[0]}, Key Vault URI: {args[1]}, Secret Name: {args[2]}"))