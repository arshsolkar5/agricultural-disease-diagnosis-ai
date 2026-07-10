import { create } from 'zustand'
import type { DiagnosisResponse } from '@/types'

interface DiagnosisStore {
  selectedCropType: string
  farmerId: string | null
  location: string | null
  additionalContext: string | null
  latestDiagnosis: DiagnosisResponse | null
  setCropType: (crop: string) => void
  setFarmerId: (id: string | null) => void
  setLocation: (loc: string | null) => void
  setAdditionalContext: (context: string | null) => void
  setLatestDiagnosis: (diagnosis: DiagnosisResponse | null) => void
  reset: () => void
}

export const useDiagnosisStore = create<DiagnosisStore>((set) => ({
  selectedCropType: 'auto_detect',
  farmerId: null,
  location: null,
  additionalContext: null,
  latestDiagnosis: null,
  setCropType: (crop) => set({ selectedCropType: crop }),
  setFarmerId: (id) => set({ farmerId: id }),
  setLocation: (loc) => set({ location: loc }),
  setAdditionalContext: (context) => set({ additionalContext: context }),
  setLatestDiagnosis: (diagnosis) => set({ latestDiagnosis: diagnosis }),
  reset: () =>
    set({
      selectedCropType: 'auto_detect',
      farmerId: null,
      location: null,
      additionalContext: null,
    }),
}))
