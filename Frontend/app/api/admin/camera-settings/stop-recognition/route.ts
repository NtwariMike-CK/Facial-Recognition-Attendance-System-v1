import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization")

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/camera-settings/stop-recognition`, {
      method: "POST",
      headers: {
        Authorization: authHeader || "",
      },
    })

    if (response.ok) {
      const data = await response.text()
      return NextResponse.json({ message: data })
    } else {
      const data = await response.json()
      return NextResponse.json(data, { status: response.status })
    }
  } catch (error) {
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 })
  }
}
