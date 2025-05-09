import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
    
    console.log('Fetching indicators from:', `${API_BASE_URL}/indicators/standard-catalog`);
    
    const response = await fetch(`${API_BASE_URL}/indicators/standard-catalog`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });
    
    if (!response.ok) {
      console.error('Error response from API:', response.status, response.statusText);
      return NextResponse.json({ error: `API returned ${response.status}` }, { status: response.status });
    }
    
    const data = await response.json();
    console.log('Received indicators:', data.length, 'categories');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in API route:', error);
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
} 