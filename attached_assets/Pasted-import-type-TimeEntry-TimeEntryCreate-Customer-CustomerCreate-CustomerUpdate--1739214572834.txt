import type {
  TimeEntry,
  TimeEntryCreate,
  Customer,
  CustomerCreate,
  CustomerUpdate,
  Project,
  ProjectCreate,
  ProjectBase,
  ProjectManager,
  ProjectManagerCreate,
  ProjectManagerUpdate,
  TimeSummary,
  WeeklyReport,
  MonthlyReport,
} from "@/types/schemas"
import { toast } from "@/components/ui/use-toast"

const API_BASE_URL = "https://6ed7ce35-85b3-498b-9e9b-4d63631ed8e3-00-2owzgyvztotfg.worf.replit.dev"

const API_PATHS = {
  timeEntries: "/time-entries",
  timeEntriesByMonth: "/time-entries/by-month",
  timeEntriesByWeek: "/time-entries/by-week",
  timeEntriesByDate: "/time-entries/by-date",
  timeEntriesUpload: "/time-entries/upload",
  customers: "/customers",
  projectManagers: "/project-managers",
  projects: "/projects",
  reports: {
    weekly: "/reports/weekly",
    monthly: "/reports/monthly",
  },
  initDb: "/init-db",
} as const

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: any,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

async function checkNetworkStatus(): Promise<boolean> {
  return navigator.onLine
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorBody = await response.text()
    console.error(
      `
HTTP
error
response: `,
      {
        status: response.status,
        statusText: response.statusText,
        body: errorBody,
      },
    )
    try {
      const errorJson = JSON.parse(errorBody)
      throw new ApiError(
        response.status,
        errorJson.detail ||
          `
HTTP
error!
status: $
{
  response.status
}
;`,
        errorJson,
      )
    } catch (e) {
      throw new ApiError(
        response.status,
        `
HTTP
error!
status: $
{
  response.status
}
;`,
        errorBody,
      )
    }
  }
  const responseData = await response.json()
  console.log(
    `
API
response
data: `,
    JSON.stringify(responseData, null, 2),
  )
  return responseData
}

async function fetchWithRetry(url: string, options: RequestInit, maxRetries = 3): Promise<Response> {
  let retries = 0
  while (retries < maxRetries) {
    try {
      const isOnline = await checkNetworkStatus()
      if (!isOnline) {
        console.error("Network is offline. Retrying in 5 seconds...")
        await new Promise((resolve) => setTimeout(resolve, 5000))
        continue
      }

      console.log(
        `
Attempting
fetch
to
$
{
  url
}
;`,
        { options, retryCount: retries },
      )
      const response = await fetch(url, {
        ...options,
        credentials: "include",
        headers: {
          ...options.headers,
          "Content-Type": "application/json",
          Accept: "application/json",
        },
      })

      console.log(`
Fetch
response
status: $
{
  response.status
}
;`)
      console.log(
        `
Fetch
response
headers: `,
        Object.fromEntries(response.headers.entries()),
      )

      if (!response.ok) {
        const errorBody = await response.text()
        console.error(
          `
Fetch
error
response
body: `,
          errorBody,
        )
        throw new Error(`
HTTP
error!
status: $
{
  response.status
}
, body: $
{
  errorBody
}
;`)
      }

      return response
    } catch (error) {
      console.error(
        `
Fetch
error (attempt ${retries + 1}/${maxRetries})
:`,
        error,
      )
      console.error("Fetch error stack:", error.stack)
      console.error("Request URL:", url)
      console.error("Request options:", JSON.stringify(options, null, 2))

      if (error instanceof TypeError && error.message === "Failed to fetch") {
        console.error("This error often indicates a network issue or CORS problem.")
      }

      retries++
      if (retries >= maxRetries) {
        throw error
      }
      await new Promise((resolve) => setTimeout(resolve, Math.pow(2, retries) * 1000))
    }
  }
  throw new Error("Max retries reached")
}

async function checkApiStatus(): Promise<{ isAvailable: boolean; message: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: "GET",
      headers: { Accept: "application/json" },
      credentials: "include",
    })

    if (response.ok) {
      const data = await response.json()
      return { isAvailable: true, message: data.status }
    } else {
      return { isAvailable: false, message: `API returned status ${response.status}` }
    }
  } catch (error) {
    console.error("Error checking API status:", error)
    return { isAvailable: false, message: `Error checking API status: ${error.message}` }
  }
}

export const apiClient = {
  // Time Entries
  async createTimeEntry(entry: TimeEntryCreate): Promise<TimeEntry> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.timeEntries}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async getTimeEntries(skip = 0, limit = 100): Promise<{ data: TimeEntry[]; total: number }> {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() })
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.timeEntries}?${params}`, {
      credentials: "include",
    })
    const data = await handleResponse<TimeEntry[]>(response)
    const total = Number.parseInt(response.headers.get("X-Total-Count") || "0", 10)
    return { data, total }
  },

  async getTimeEntry(id: number): Promise<TimeEntry> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.timeEntries}/${id}`, {
      credentials: "include",
    })
    return handleResponse(response)
  },

  async updateTimeEntry(id: number, entry: Partial<TimeEntryCreate>): Promise<TimeEntry> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.timeEntries}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async deleteTimeEntry(id: number): Promise<void> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.timeEntries}/${id}`, {
      method: "DELETE",
      credentials: "include",
    })
    return handleResponse(response)
  },

  // Time Summaries
  async getTimeSummaries(
    startDate: string,
    endDate: string,
    projectId?: string,
    customerName?: string,
  ): Promise<TimeSummary> {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
    })
    if (projectId) params.append("project_id", projectId)
    if (customerName) params.append("customer_name", customerName)

    console.log(`Fetching time summaries with params:`, Object.fromEntries(params))

    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/time-summaries/?${params}`, {
        method: "GET",
      })

      const data = await response.json()
      console.log(`Time summaries API response:`, JSON.stringify(data, null, 2))

      if (!data || !data.entries || data.entries.length === 0) {
        console.warn(`No data available for the selected period:`, { startDate, endDate })
        throw new Error("No data available for the selected period")
      }

      return data
    } catch (error) {
      console.error("Error in getTimeSummaries:", error)
      console.error("Error stack:", error.stack)
      if (error instanceof ApiError) {
        throw error
      } else if (error instanceof Error) {
        throw new ApiError(500, error.message, { originalError: error })
      } else {
        throw new ApiError(500, "An unknown error occurred", { originalError: error })
      }
    }
  },

  async getTimeEntriesByMonth(month: string, year: number, projectId?: string): Promise<TimeSummary> {
    // Validate month format
    const capitalizedMonth = month
      .split(" ")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ")
    const validMonths = [
      "January",
      "February",
      "March",
      "April",
      "May",
      "June",
      "July",
      "August",
      "September",
      "October",
      "November",
      "December",
    ]

    if (!validMonths.includes(capitalizedMonth)) {
      throw new ApiError(422, `Invalid month. Must be one of: ${validMonths.join(", ")}`)
    }

    // Construct query parameters
    const params = new URLSearchParams({
      year: year.toString(), // Required parameter
    })

    // Optional project_id parameter
    if (projectId) {
      params.append("project_id", projectId)
    }

    console.log(`Fetching time entries for month: ${capitalizedMonth}, year: ${year}`)

    try {
      const response = await fetchWithRetry(
        `${API_BASE_URL}${API_PATHS.timeEntriesByMonth}/${capitalizedMonth}?${params}`,
        {
          method: "GET",
          credentials: "include",
        },
      )

      const data = await handleResponse<TimeSummary>(response)
      console.log(`Time entries API response:`, JSON.stringify(data, null, 2))

      return data
    } catch (error) {
      console.error("Error in getTimeEntriesByMonth:", error)
      console.error("Error stack:", error.stack)

      if (error instanceof ApiError) {
        throw error
      } else if (error instanceof Error) {
        throw new ApiError(500, error.message, { originalError: error })
      } else {
        throw new ApiError(500, "An unknown error occurred", { originalError: error })
      }
    }
  },

  // Reports
  async getWeeklyReport(date?: string, projectId?: string): Promise<WeeklyReport> {
    const params = new URLSearchParams()
    if (date) params.append("date", date)
    if (projectId) params.append("project_id", projectId)
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.reports.weekly}?${params}`, {
      credentials: "include",
    })
    return handleResponse(response)
  },

  async getMonthlyReport(year: number, month: number, projectId?: string): Promise<MonthlyReport> {
    const params = new URLSearchParams({
      year: year.toString(),
      month: month.toString(),
    })
    if (projectId) params.append("project_id", projectId)
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.reports.monthly}?${params}`, {
      credentials: "include",
    })
    return handleResponse(response)
  },

  // Customers
  async getCustomers(skip = 0, limit = 100): Promise<{ data: Customer[]; total: number }> {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() })
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.customers}?${params}`, {
      credentials: "include",
    })
    const data = await handleResponse<Customer[]>(response)
    const total = Number.parseInt(response.headers.get("X-Total-Count") || "0", 10)
    return { data, total }
  },

  async getCustomer(id: number): Promise<Customer> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.customers}/${id}`, {
      credentials: "include",
    })
    return handleResponse(response)
  },

  async createCustomer(customer: CustomerCreate): Promise<Customer> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.customers}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(customer),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async updateCustomer(id: number, update: CustomerUpdate): Promise<Customer> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.customers}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async deleteCustomer(id: number): Promise<void> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.customers}/${id}`, {
      method: "DELETE",
      credentials: "include",
    })
    return handleResponse(response)
  },

  // Project Managers
  async getProjectManagers(skip = 0, limit = 100): Promise<{ data: ProjectManager[]; total: number }> {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() })
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projectManagers}?${params}`, {
      credentials: "include",
    })
    const data = await handleResponse<ProjectManager[]>(response)
    const total = Number.parseInt(response.headers.get("X-Total-Count") || "0", 10)
    return { data, total }
  },

  async getProjectManager(id: number): Promise<ProjectManager> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projectManagers}/${id}`, {
      credentials: "include",
    })
    return handleResponse(response)
  },

  async createProjectManager(manager: ProjectManagerCreate): Promise<ProjectManager> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projectManagers}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(manager),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async updateProjectManager(id: number, update: ProjectManagerUpdate): Promise<ProjectManager> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projectManagers}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async deleteProjectManager(id: number): Promise<void> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projectManagers}/${id}`, {
      method: "DELETE",
      credentials: "include",
    })
    return handleResponse(response)
  },

  // Projects
  async getProjects(skip = 0, limit = 100): Promise<{ data: Project[]; total: number }> {
    const params = new URLSearchParams({ skip: skip.toString(), limit: limit.toString() })
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projects}?${params}`, {
      credentials: "include",
    })
    const data = await handleResponse<Project[]>(response)
    const total = Number.parseInt(response.headers.get("X-Total-Count") || "0", 10)
    return { data, total }
  },

  async getProject(id: number): Promise<Project> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projects}/${id}`, {
      credentials: "include",
    })
    return handleResponse(response)
  },

  async createProject(project: ProjectCreate): Promise<Project> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projects}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(project),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async updateProject(id: number, update: ProjectBase): Promise<Project> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projects}/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(update),
      credentials: "include",
    })
    return handleResponse(response)
  },

  async deleteProject(id: number): Promise<void> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.projects}/${id}`, {
      method: "DELETE",
      credentials: "include",
    })
    return handleResponse(response)
  },

  // Database
  async initializeDatabase(force = false): Promise<void> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.initDb}?force=${force}`, {
      method: "POST",
      credentials: "include",
    })
    return handleResponse(response)
  },

  async getDatabaseStatus(): Promise<void> {
    const response = await fetchWithRetry(`${API_BASE_URL}${API_PATHS.initDb}`, {
      credentials: "include",
    })
    return handleResponse(response)
  },

  // Add a new method to test API connection
  async testConnection(): Promise<boolean> {
    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/health`, {
        method: "GET",
      })
      return response.ok
    } catch (error) {
      console.error("API connection test failed:", error)
      return false
    }
  },

  // New method to check API status
  async checkApiStatus(): Promise<{ isAvailable: boolean; message: string }> {
    return checkApiStatus()
  },
}

// Error handling wrapper
export async function withErrorHandling<T>(operation: () => Promise<T>): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    if (error instanceof ApiError) {
      toast({
        title: "API Error",
        description: `Status ${error.status}: ${error.message}`,
        variant: "destructive",
      })
    } else {
      toast({
        title: "Unexpected Error",
        description: error instanceof Error ? error.message : "An unknown error occurred",
        variant: "destructive",
      })
    }
    throw error
  }
}

