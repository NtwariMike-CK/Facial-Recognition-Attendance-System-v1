import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("authorization")
    const { searchParams } = new URL(request.url)
    const showPreview = searchParams.get("show_preview")

    let url = `${process.env.NEXT_PUBLIC_API_URL}/admin/camera-settings/start-recognition`
    if (showPreview) {
      url += `?show_preview=${showPreview}`
    }

    const response = await fetch(url, {
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
