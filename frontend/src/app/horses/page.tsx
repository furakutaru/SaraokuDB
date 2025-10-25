'use client'

import { useEffect, useState } from 'react'

interface Horse {
  id: number
  name: string
  sex?: string
  age?: number
  // 他の必要なフィールドを追加
}

export default function HorsesPage() {
  const [horses, setHorses] = useState<Horse[]>([])

  useEffect(() => {
    const fetchHorses = async () => {
      const response = await fetch('/api/horses')
      const data = await response.json()
      setHorses(data)
    }
    fetchHorses()
  }, [])

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">馬一覧</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {horses.map((horse) => (
          <div key={horse.id} className="border p-4 rounded-lg shadow">
            <h2 className="text-xl font-semibold">{horse.name}</h2>
            <p>性別: {horse.sex || '不明'}</p>
            <p>年齢: {horse.age || '不明'}歳</p>
            {/* 他のフィールドを表示 */}
          </div>
        ))}
      </div>
    </div>
  )
}
