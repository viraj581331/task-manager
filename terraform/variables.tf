variable "aws_region" {
  type        = string
  description = "The target AWS geographic deployment region"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "The global naming prefix for resource tracking labels"
  default     = "task-manager"
}

variable "db_name" {
  type        = string
  description = "The initial database schema name generated inside MySQL"
  default     = "task_manager"
}
