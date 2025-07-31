import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const authHeader = request.headers.get("authorization")
    const formData = await request.formData()

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/admin/employees/${params.id}/upload-image`, {
      method: "POST",
      headers: {
        Authorization: authHeader || "",
      },
      body: formData,
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
