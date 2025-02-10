# Timesheet Management API Documentation

## High Level Overview
The Timesheet Management API is a FastAPI-based backend service designed for comprehensive time tracking and project management. It provides endpoints for managing time entries, projects, customers, and project managers, along with detailed reporting capabilities.

## Expected Functionality

### Core Features
1. **Time Entry Management**
   - Create individual and bulk time entries
   - Upload timesheet data via CSV/Excel files
   - Query time entries by date, week, and month

2. **Project Management**
   - Create and manage projects
   - Associate projects with customers and project managers
   - Track project status and details

3. **Customer Management**
   - Create and maintain customer records
   - Track customer details including contact information
   - Associate customers with projects

4. **Project Manager Management**
   - Manage project manager information
   - Associate managers with projects
   - Track manager responsibilities

5. **Reporting**
   - Generate weekly and monthly reports
   - Filter reports by project, customer, or date range
   - Calculate time summaries and analytics

## Error Handling

The API implements a consistent error handling approach across all endpoints:

### Common HTTP Status Codes
- `200`: Successful operation
- `400`: Bad Request (invalid input data)
- `404`: Resource Not Found
- `500`: Internal Server Error

### Error Response Format
```json
{
    "detail": "Error message describing the issue"
}
```

### CORS Configuration
- All origins are allowed (`"*"`)
- All standard HTTP methods supported
- Custom headers allowed
- Credentials handling disabled
- Preflight requests handled automatically

## API Endpoints Documentation

### Root Endpoint
```
GET /
```
Health check endpoint that returns API status and documentation links.

#### Response
```json
{
    "status": "healthy",
    "message": "Timesheet Management API is running",
    "documentation": "/docs",
    "redoc": "/redoc"
}
```

### Time Entries

#### Create Time Entry
```
POST /time-entries/
```
Creates a single time entry.

**Request Body**: TimeEntryCreate schema
```json
{
    "date": "2025-02-05",
    "hours": 8,
    "project": "PROJECT_ID",
    "description": "Work description"
}
```

#### Upload Multiple Time Entries
```
POST /time-entries/upload
```
Bulk upload of time entries.

**Request Body**: Array of TimeEntryCreate objects

#### Upload Timesheet File
```
POST /upload/
```
Upload timesheet data via CSV or Excel file.

**Form Data**:
- `file`: CSV or Excel file containing timesheet data

#### Get Time Entries by Date
```
GET /time-entries/by-date/{date}
```
Retrieves time entries for a specific date.

#### Get Time Entries by Week
```
GET /time-entries/by-week/{week_number}
```
Retrieves time entries for a specific week number.

Parameters:
- `week_number`: Week number (1-53)
- `year`: Year (e.g., 2025)
- `project_id`: Optional project filter

#### Get Time Entries by Month
```
GET /time-entries/by-month/{month}
```
Retrieves time entries for a specific month.

Parameters:
- `month`: Month name (e.g., "January")
- `year`: Year (e.g., 2025)
- `project_id`: Optional project filter

### Customers

#### Create Customer
```
POST /customers/
```
Creates a new customer record.

**Request Body**:
```json
{
    "name": "Customer Name",
    "contact_email": "email@example.com",
    "industry": "Industry",
    "status": "active",
    "address": "Customer Address",
    "phone": "1234567890"
}
```

#### Get All Customers
```
GET /customers/
```
Retrieves all customers with pagination.

Parameters:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

#### Get Customer by Name
```
GET /customers/{name}
```
Retrieves a specific customer by name.

#### Update Customer
```
PATCH /customers/{name}
```
Updates customer information.

### Project Managers

#### Create Project Manager
```
POST /project-managers/
```
Creates a new project manager record.

#### Get All Project Managers
```
GET /project-managers/
```
Retrieves all project managers with pagination.

#### Get Project Manager by Email
```
GET /project-managers/{email}
```
Retrieves a specific project manager by email.

#### Update Project Manager
```
PATCH /project-managers/{email}
```
Updates project manager information.

### Projects

#### Create Project
```
POST /projects/
```
Creates a new project.

#### Get All Projects
```
GET /projects/
```
Retrieves all projects with optional filtering.

Parameters:
- `customer_name`: Filter by customer
- `project_manager_name`: Filter by project manager
- `skip`: Pagination offset
- `limit`: Pagination limit

#### Get Project by ID
```
GET /projects/{project_id}
```
Retrieves a specific project by ID.

#### Update Project
```
PATCH /projects/{project_id}
```
Updates project information.

#### Delete Project
```
DELETE /projects/{project_id}
```
Deletes a project.

### Reports

#### Weekly Report
```
GET /reports/weekly
```
Generates a weekly time report.

Parameters:
- `date`: Report date (optional, defaults to current date)
- `project_id`: Optional project filter

#### Monthly Report
```
GET /reports/monthly
```
Generates a monthly time report.

Parameters:
- `year`: Report year
- `month`: Report month
- `project_id`: Optional project filter

## Integration Guidelines

1. **Authentication**
   - Currently, the API doesn't require authentication
   - CORS is configured to allow all origins for development

2. **Date Handling**
   - All dates should be in ISO format (YYYY-MM-DD)
   - Time entries use local dates without time zones

3. **Error Handling**
   - Implement try-catch blocks for all API calls
   - Handle both HTTP errors and validation errors
   - Check response status codes and error messages

4. **Data Validation**
   - Validate input data before sending to API
   - Ensure required fields are provided
   - Follow the schema specifications for each endpoint

5. **Performance Considerations**
   - Use pagination for large data sets
   - Implement appropriate error retry mechanisms
   - Cache frequently accessed data where appropriate
