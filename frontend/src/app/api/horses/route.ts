import { prisma } from '@/lib/db'
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const horses = await prisma.horse.findMany({
      orderBy: {
        createdAt: 'desc',
      },
    })
    return NextResponse.json(horses)
  } catch (error) {
    console.error('Error fetching horses:', error)
    return new NextResponse('Internal Error', { status: 500 })
  }
}
