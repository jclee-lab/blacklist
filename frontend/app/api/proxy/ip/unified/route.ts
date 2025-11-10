import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://blacklist-app:2542';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const url = `${BACKEND_URL}/api/ip/unified?${searchParams.toString()}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = await response.json();

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('IP unified proxy error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch unified IP list' },
      { status: 500 }
    );
  }
}
