import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization")
    const { searchParams } = new URL(request.url)

    let url = `${process.env.NEXT_PUBLIC_API_URL}/employee/attendance`

    const params = new URLSearchParams()
    if (searchParams.get("date_from")) params.append("date_from", searchParams.get("date_from")!)
    if (searchParams.get("date_to")) params.append("date_to", searchParams.get("date_to")!)

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
