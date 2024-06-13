import { Preferences, AssignedSlice } from '../../types'
import { makePercentage } from '../../utils/formatUtils'
import { findCutLineByPercent, getTotalValue } from './getValue'
import { cutSlice } from './sliceUtils'
import { Step, makeStep } from './types'

export const cutAndChoose = (
  preferences: Preferences,
  cakeSize: number
): { solution: AssignedSlice[]; steps: Step[] } => {
  if (preferences.length !== 2) {
    throw new Error('Cut and choose only works with two agents')
  }
  const steps: Step[] = []

  // agent 0 cuts
  const cutPoint = findCutLineByPercent(preferences[0], 0.5)
  steps.push(
    makeStep(
      0,
      `judges the middle of the resource to be ${makePercentage(cutPoint / cakeSize, 3)}`
    )
  )

  const slice1 = cutSlice(preferences, 0, cutPoint, 1)
  const slice2 = cutSlice(preferences, cutPoint, cakeSize, 2)
  steps.push(
    makeStep(
      0,
      `cut the resource into two pieces at ${makePercentage(cutPoint / cakeSize, 3)}`, [slice1, slice2]
    )
  )

  // agent 1 chooses
  const agent1TotalValue = getTotalValue(preferences[1])
  if (slice1.values[1] >= slice2.values[1]) {
    steps.push(
      makeStep(
        1,
        `chooses piece 1 because it is worth ${makePercentage(
          slice1.values[1] / agent1TotalValue,
          3
        )} of the resource to them`,
        [slice1],
        true
      )
    )
    steps.push(makeStep(0, 'takes remaining piece', [slice2], true))

    return { solution: [slice1.assign(1), slice2.assign(0)], steps }
  } else {
    steps.push(
      makeStep(
        1,
        `chooses piece 2 because it is worth ${makePercentage(
          slice2.values[1] / agent1TotalValue,
          3
        )} of the resource to them`,
        [slice2],
        true
      )
    )
    steps.push(makeStep(0, 'takes remaining piece', [slice1], true))

    return { solution: [slice1.assign(0), slice2.assign(1)], steps }
  }
}
