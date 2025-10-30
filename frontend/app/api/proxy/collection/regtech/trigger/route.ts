import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://blacklist-app:2542';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({})); // Get request body or empty object
    const url = `${BACKEND_URL}/api/collection/regtech/trigger`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body), // Pass body to backend
    });

    const data = await response.json();

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Collection trigger POST proxy error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to trigger collection' },
      { status: 500 }
    );
  }
}
