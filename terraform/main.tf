# 1. Fetch available Availability Zones in the region (e.g., us-east-1a, us-east-1b)
data "aws_availability_zones" "available" {
  state = "available"
}

# 2. Create the Virtual Private Cloud (VPC) - Your Isolated Cloud Network
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# 3. Create Public Subnets (For Load Balancer/Public Entry Points)
resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index}/24" # 10.0.0.0/24 and 10.0.1.0/24
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
  }
}

# 4. Create Private Subnets (For App Container & Managed Database)
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}/24" # 10.0.10.0/24 and 10.0.11.0/24
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
  }
}

# 5. Create an Internet Gateway (Allows Public Subnets to touch the internet)
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# 6. Create a Public Route Table (Directs public traffic through the Internet Gateway)
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

# 7. Associate Public Subnets with Public Route Table
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# ==========================================
# 8. SECURITY GROUPS (Digital Firewalls)
# ==========================================

# Firewall for the public Application Load Balancer
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Allow public inbound HTTP traffic to the Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Allow public HTTP traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Open to the world
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

# Firewall for the FastAPI Application Containers
resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-tasks-sg"
  description = "Isolate application container traffic"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Allow traffic ONLY from the Application Load Balancer"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id] # 🛡️ Security Group Chaining
  }

  egress {
    description = "Allow containers to reach out to the internet for dependencies/updates"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-tasks-sg"
  }
}

# Firewall for the MySQL Database
resource "aws_security_group" "db" {
  name        = "${var.project_name}-db-sg"
  description = "Protect database instances from public access"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Allow MySQL traffic ONLY from the FastAPI app containers"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id] # 🛡️ Deep Isolation
  }

  egress {
    description = "Allow database tracking outbound networks"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-db-sg"
  }
}

# ==========================================
# 9. AMAZON RDS MANAGE DATABASE LAYER
# ==========================================

# Group our private subnets together to tell AWS where the DB can be placed
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = [aws_subnet.private[0].id, aws_subnet.private[1].id]

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# Generate the actual MySQL database instance inside AWS RDS
resource "aws_db_instance" "mysql" {
  identifier             = "${var.project_name}-rds"
  allocated_storage      = 20 # 20 GB standard storage size (Free Tier compliant)
  max_allocated_storage  = 100 # Allows autoscaling if database space fills up
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t4g.micro" # AWS Graviton instance (Free Tier eligible)
  db_name                = var.db_name
  username               = "root"
  password               = "securecloudpassword123" # In production, pull this dynamically from AWS Secrets Manager
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = true # Allows quick tear downs during development tests
  publicly_accessible    = false # Hard restriction blocking external internet discovery

  tags = {
    Name = "${var.project_name}-mysql-rds"
  }
}
