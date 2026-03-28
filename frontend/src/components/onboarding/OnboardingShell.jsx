import { useState } from 'react'
import { Outlet, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { submitOnboarding } from '../../api/profile'
import { calculateFootprint } from '../../api/footprint'

export default function OnboardingShell() {
  const navigate = useNavigate()
  const [data, setData] = useState({
    zip_code: '',
    transport_mode: 'transit',
    commute_days_per_week: undefined,
    diet_type: 'meat_weekly',
    home_type: '',
    home_size_sqm: 70,
    has_pets: undefined,
    pet_type: null,
    pet_count: 0,
  })

  const mutation = useMutation({
    mutationFn: async (profile) => {
      await submitOnboarding(profile)
      const { data: footprint } = await calculateFootprint()
      return footprint
    },
    onSuccess: () => navigate('/home'),
  })

  const updateData = (partial) => setData((prev) => ({ ...prev, ...partial }))

  const handleFinish = () => {
    mutation.mutate({
      zip_code: data.zip_code,
      transport_mode: data.transport_mode,
      commute_days_per_week: data.commute_days_per_week ?? 5,
      diet_type: data.diet_type,
      home_type: data.home_type || 'apartment',
      home_size_sqm: data.home_size_sqm,
      has_pets: data.has_pets ?? false,
      pet_type: data.pet_type,
      pet_count: data.pet_count,
    })
  }

  return (
    <div className="min-h-screen bg-surface max-w-md mx-auto flex flex-col">
      <header className="flex items-center justify-between px-4 py-3">
        <button onClick={() => navigate(-1)} className="text-on-surface/60">
          <span className="material-symbols-outlined">close</span>
        </button>
        <span className="text-primary font-extrabold text-lg italic">Green Buddy</span>
        <div className="w-6" />
      </header>
      <div className="flex-1 px-4 pb-8">
        <Outlet context={{ data, updateData, handleFinish, submitting: mutation.isPending, error: mutation.error }} />
      </div>
    </div>
  )
}
