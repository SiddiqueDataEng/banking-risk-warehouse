terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  
  tags = var.tags
}

# Storage Account for Data Lake
resource "azurerm_storage_account" "datalake" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "GRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true
  
  blob_properties {
    versioning_enabled = true
    
    delete_retention_policy {
      days = 30
    }
  }
  
  tags = var.tags
}

# Data Lake Containers
resource "azurerm_storage_data_lake_gen2_filesystem" "raw" {
  name               = "raw"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "staging" {
  name               = "staging"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "curated" {
  name               = "curated"
  storage_account_id = azurerm_storage_account.datalake.id
}

# Azure Synapse Workspace
resource "azurerm_synapse_workspace" "synapse" {
  name                                 = var.synapse_workspace_name
  resource_group_name                  = azurerm_resource_group.rg.name
  location                             = azurerm_resource_group.rg.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.raw.id
  sql_administrator_login              = var.sql_admin_username
  sql_administrator_login_password     = var.sql_admin_password
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Synapse SQL Pool (Dedicated)
resource "azurerm_synapse_sql_pool" "risk_pool" {
  name                 = "RiskAnalyticsPool"
  synapse_workspace_id = azurerm_synapse_workspace.synapse.id
  sku_name             = var.synapse_sql_pool_sku
  create_mode          = "Default"
  
  tags = var.tags
}

# Synapse Spark Pool
resource "azurerm_synapse_spark_pool" "spark" {
  name                 = "risksparkpool"
  synapse_workspace_id = azurerm_synapse_workspace.synapse.id
  node_size_family     = "MemoryOptimized"
  node_size            = "Small"
  
  auto_scale {
    max_node_count = 10
    min_node_count = 3
  }
  
  auto_pause {
    delay_in_minutes = 15
  }
  
  tags = var.tags
}

# Key Vault for Secrets
resource "azurerm_key_vault" "kv" {
  name                       = var.key_vault_name
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id
    
    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge"
    ]
  }
  
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_synapse_workspace.synapse.identity[0].principal_id
    
    secret_permissions = [
      "Get", "List"
    ]
  }
  
  tags = var.tags
}

# Store SQL Admin Password in Key Vault
resource "azurerm_key_vault_secret" "sql_password" {
  name         = "sql-admin-password"
  value        = var.sql_admin_password
  key_vault_id = azurerm_key_vault.kv.id
}

# Data Factory
resource "azurerm_data_factory" "adf" {
  name                = var.data_factory_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Linked Service: Synapse
resource "azurerm_data_factory_linked_service_synapse" "synapse_link" {
  name              = "SynapseLinkedService"
  data_factory_id   = azurerm_data_factory.adf.id
  connection_string = "Integrated Security=False;Encrypt=True;Connection Timeout=30;Data Source=${azurerm_synapse_workspace.synapse.name}.sql.azuresynapse.net;Initial Catalog=${azurerm_synapse_sql_pool.risk_pool.name}"
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "logs" {
  name                = var.log_analytics_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  
  tags = var.tags
}

# Application Insights
resource "azurerm_application_insights" "appinsights" {
  name                = var.app_insights_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.logs.id
  application_type    = "web"
  
  tags = var.tags
}

# Container Registry for API Docker Images
resource "azurerm_container_registry" "acr" {
  name                = var.container_registry_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Standard"
  admin_enabled       = true
  
  tags = var.tags
}

# App Service Plan for API
resource "azurerm_service_plan" "api_plan" {
  name                = "${var.project_name}-api-plan"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "B2"
  
  tags = var.tags
}

# App Service for Risk API
resource "azurerm_linux_web_app" "risk_api" {
  name                = var.api_app_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.api_plan.id
  
  site_config {
    always_on = true
    
    application_stack {
      python_version = "3.9"
    }
  }
  
  app_settings = {
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "DOCKER_REGISTRY_SERVER_URL"          = "https://${azurerm_container_registry.acr.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME"     = azurerm_container_registry.acr.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD"     = azurerm_container_registry.acr.admin_password
    "APPINSIGHTS_INSTRUMENTATIONKEY"      = azurerm_application_insights.appinsights.instrumentation_key
    "SYNAPSE_CONNECTION_STRING"           = "Server=${azurerm_synapse_workspace.synapse.name}.sql.azuresynapse.net;Database=${azurerm_synapse_sql_pool.risk_pool.name};User Id=${var.sql_admin_username};Password=${var.sql_admin_password}"
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = var.tags
}

# Role Assignment: Storage Blob Data Contributor for Synapse
resource "azurerm_role_assignment" "synapse_storage" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_synapse_workspace.synapse.identity[0].principal_id
}

# Role Assignment: Storage Blob Data Contributor for ADF
resource "azurerm_role_assignment" "adf_storage" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.adf.identity[0].principal_id
}

# Data source for current client config
data "azurerm_client_config" "current" {}

# Outputs
output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "synapse_workspace_name" {
  value = azurerm_synapse_workspace.synapse.name
}

output "synapse_sql_endpoint" {
  value = "${azurerm_synapse_workspace.synapse.name}.sql.azuresynapse.net"
}

output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "key_vault_name" {
  value = azurerm_key_vault.kv.name
}

output "api_url" {
  value = "https://${azurerm_linux_web_app.risk_api.default_hostname}"
}

output "container_registry_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "application_insights_key" {
  value     = azurerm_application_insights.appinsights.instrumentation_key
  sensitive = true
}
