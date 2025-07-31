import { type NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization")
    const { searchParams } = new URL(request.url)

    let url = `${process.env.NEXT_PUBLIC_API_URL}/admin/tickets`

    const statusFilter = searchParams.get("status_filter")
    if (statusFilter && statusFilter !== "all") {
      url += `?status_filter=${statusFilter}`
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
