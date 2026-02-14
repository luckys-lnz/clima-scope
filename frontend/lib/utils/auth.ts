/**
 * JWT token utilities
 */

// Check if token is expired
export function isTokenExpired(token: string): boolean {
    try {
      // JWT tokens are in format: header.payload.signature
      const payload = JSON.parse(atob(token.split('.')[1]))
      // exp is in seconds, Date.now() is in milliseconds
      return payload.exp * 1000 < Date.now()
    } catch {
      return true // If can't parse, consider expired
    }
  }
  
  // Handle token expiration
  export function handleTokenExpired(): never {
    // Clear storage
    localStorage.removeItem("access_token")
    localStorage.removeItem("user")
    
    // Redirect to login page if in browser
    if (typeof window !== "undefined") {
      window.location.href = "/login"
    }
    
    throw new Error("Session expired. Please login again.")
  }
  
  // Get auth headers with token validation
  export function getAuthHeaders(token: string): HeadersInit {
    if (!token || isTokenExpired(token)) {
      handleTokenExpired()
    }
    
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    }
  }