variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "banking-risk"
}

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "rg-banking-risk-analytics"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "storage_account_name" {
  description = "Name of the storage account (must be globally unique)"
  type        = string
  default     = "stbankingriskdl"
}

variable "synapse_workspace_name" {
  description = "Name of the Synapse workspace"
  type        = string
  default     = "synapse-banking-risk"
}

variable "synapse_sql_pool_sku" {
  description = "SKU for Synapse SQL Pool"
  type        = string
  default     = "DW100c"
}

variable "sql_admin_username" {
  description = "SQL administrator username"
  type        = string
  default     = "sqladmin"
}

variable "sql_admin_password" {
  description = "SQL administrator password"
  type        = string
  sensitive   = true
}

variable "key_vault_name" {
  description = "Name of the Key Vault"
  type        = string
  default     = "kv-banking-risk"
}

variable "data_factory_name" {
  description = "Name of the Data Factory"
  type        = string
  default     = "adf-banking-risk"
}

variable "log_analytics_name" {
  description = "Name of the Log Analytics workspace"
  type        = string
  default     = "log-banking-risk"
}

variable "app_insights_name" {
  description = "Name of Application Insights"
  type        = string
  default     = "appi-banking-risk"
}

variable "container_registry_name" {
  description = "Name of the Container Registry"
  type        = string
  default     = "acrbankingrisk"
}

variable "api_app_name" {
  description = "Name of the API App Service"
  type        = string
  default     = "app-banking-risk-api"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Environment = "Production"
    Project     = "Banking Risk Analytics"
    ManagedBy   = "Terraform"
    Compliance  = "Basel III"
  }
}

variable "enable_private_endpoints" {
  description = "Enable private endpoints for enhanced security"
  type        = bool
  default     = false
}

variable "allowed_ip_ranges" {
  description = "List of allowed IP ranges for firewall"
  type        = list(string)
  default     = []
}
