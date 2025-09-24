import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // In a real app, you would fetch this from your backend API
    // For now, we'll return sample data
    const sampleHorses = [
      {
        id: '1',
        name: 'サンプル馬1',
        sex: '牡',
        age: 3,
        sire: '父サンプル',
        dam: '母サンプル',
        damsire: '母父サンプル',
        sold_price: 1000,
        seller: 'サンプル牧場',
        auction_date: '2023-01-01',
      },
      // Add more sample data as needed
    ];

    return NextResponse.json(sampleHorses);
  } catch (error) {
    console.error('Error fetching horses:', error);
    return new NextResponse(
      JSON.stringify({ error: 'Failed to fetch horses' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
