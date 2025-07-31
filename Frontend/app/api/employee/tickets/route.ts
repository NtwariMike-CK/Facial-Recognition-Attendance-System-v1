import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization")

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/employee/tickets`, {
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

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/employee/tickets`, {
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
