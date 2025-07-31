import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization")
    const { searchParams } = new URL(request.url)

    let url = `${process.env.NEXT_PUBLIC_API_URL}/admin/employees`

    // Add query parameters if they exist
    const params = new URLSearchParams()
    if (searchParams.get("employee_id")) params.append("employee_id", searchParams.get("employee_id")!)
    if (searchParams.get("department")) params.append("department", searchParams.get("department")!)

    if (params.toString()) {
      url += `?${params.toString()}`
    }

    const response = await fetch(url, {
      headers: {
        Authorization: authHeader || "",
      },
    })

    const data = await response.json()

    if (response.ok) {
      return NextResponse.json(data)
    } else {
      return NextResponse.json(data, { status: response.status })
    }
  } catch (error) {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization")
    const body = await request.json()

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader || "",
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    if (response.ok) {
      return NextResponse.json(data)
    } else {
      return NextResponse.json(data, { status: response.status })
    }
  } catch (error) {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 })
  }
}
