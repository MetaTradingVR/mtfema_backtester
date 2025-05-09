import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
    
    const body = await request.json();
    console.log('Testing indicator:', body.definition_id);
    
    const response = await fetch(`${API_BASE_URL}/indicators/standard/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });
    
    if (!response.ok) {
      console.error('Error response from API:', response.status, response.statusText);
      let errorText;
      try {
        errorText = await response.text();
      } catch (e) {
        errorText = 'Unable to read error details';
      }
      return NextResponse.json({ 
        success: false, 
        message: `API error: ${response.status} - ${errorText}`
      }, { status: response.status });
    }
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in API route:', error);
    return NextResponse.json({ 
      success: false, 
      message: String(error)
    }, { status: 500 });
  }
} 