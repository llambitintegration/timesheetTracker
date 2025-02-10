async function fetchWithRetry(url: string, options: RequestInit, retries = 3): Promise<Response> {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: "include",
      headers: {
        ...options.headers,
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
    })
    if (!response.ok) {
      if (retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before retrying
        return fetchWithRetry(url, options, retries - 1);
      } else {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    }
    return response;
  } catch (error) {
    console.error("Fetch error:", error);
    throw error; // Re-throw the error to be handled by the caller
  }
}