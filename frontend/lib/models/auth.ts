export interface SignUpData {
    full_name: string
    email: string
    password: string
    organization: string
    county?: string
    phone?: string
  }
  
export interface LoginData {
    email: string
    password: string
}

export interface User {
    id: string
    email: string
    full_name?: string
    organization?: string
    county?: string
    phone?: string
}
  