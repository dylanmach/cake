import remove from 'lodash.remove'
import { Preferences, AssignedSlice, UnassignedSlice } from '../../types'
import { findCutLineByValue, findCutLineByPercent } from './getValue'
import { cutSlice, sortSlicesDescending, removeBestSlice } from './sliceUtils'
import { makePercentage } from '../../utils/formatUtils'
import { Step, makeStep } from './types'

// Note that this is written with a 0-based index, but descriptions of the
// Selfridge-Conway method use a 1-based index because that's, you know, normal.
export const barbanelBrams = (
  preferences: Preferences,
  cakeSize: number
): { solution: AssignedSlice[]; steps: Step[] } => {
  if (preferences.length !== 3) {
    throw new Error('Selfridge-Conway only works with three agents')
  }
  const steps: Step[] = []
  let p0BestSlice = null
  let p1BestSlice = null
  let p2BestSlice = null
  let slices = []

  const [p0Prefs, p1Prefs] = preferences

  // P0 cuts
  const firstCut = findCutLineByPercent(p0Prefs, 1 / 3)
  const secondCut = findCutLineByPercent(p0Prefs, 2 / 3)

  // These slices are not final, they may get trimmed
  const tempSlices = [
    cutSlice(preferences, 0, firstCut, 1),
    cutSlice(preferences, firstCut, secondCut, 2),
    cutSlice(preferences, secondCut, cakeSize, 3),
  ]
  steps.push(
    makeStep(
      0,
      `divides the resource into thirds at ${makePercentage(
        firstCut / cakeSize,
        3
      )} and ${makePercentage(secondCut / cakeSize, 3)}`,
      tempSlices
    )
  )
  console.log('Slices are ', tempSlices)

  // First, sort the slices from largest to smallest based on P1's preferences
  slices = sortSlicesDescending(1, tempSlices)
  // Then, find the values of the two largest (the first two in the array)
  const p1LargestValue = slices[0].values[1]
  const p1SecondLargestValue = slices[1].values[1]

  // Then, P1 decides if the two largest are equal (allowing for tiny floating point differences)
  if (Math.abs(p1LargestValue - p1SecondLargestValue) < 0.0000000000001) {
    // The two are equal, no trimming needed. Easy path!
    steps.push(
      makeStep(1, `decides the two largest pieces are equal so doesn't trim them`, [
        slices[0],
        slices[1],
      ])
    )
    console.log(
      '2nd person considers two largest slices as equal, splitting the easy way.'
    )
    ;[p2BestSlice, slices] = removeBestSlice(2, slices) // P2 picks slice
    ;[p1BestSlice, slices] = removeBestSlice(1, slices) // P1 picks slice
    p0BestSlice = slices[0] // P0 picks last slice

    steps.push(makeStep(2, `chooses piece ${p2BestSlice.id}`, [p2BestSlice], true))
    steps.push(makeStep(1, `chooses piece ${p1BestSlice.id}`, [p1BestSlice], true))
    steps.push(makeStep(0, `chooses remaining piece`, [p0BestSlice], true))
    return {
      solution: [p2BestSlice.assign(2), p1BestSlice.assign(1), p0BestSlice.assign(0)],
      steps,
    }
  }

  // P1 trims largest slice so two largest slices are equal, trimmings set aside
  console.log('Trimming piece', slices[0])
  const cutLine = findCutLineByValue(p1Prefs, p1LargestValue - p1SecondLargestValue, {
    startBound: slices[0].start,
    endBound: slices[0].end,
  })

  const trimming = cutSlice(preferences, slices[0].start, cutLine, 4, 'trimming')
  const trimmedPiece = cutSlice(
    preferences,
    cutLine,
    slices[0].end,
    slices[0].id,
    'trimmed'
  )
  steps.push(
    makeStep(
      1,
      `trims off part of piece ${trimmedPiece.id} to make it the same value as piece ${slices[1].id}. The trimmings are set aside`,
      [trimming, trimmedPiece]
    )
  )
  slices[0] = trimmedPiece

  console.log('Picking slices')
  // P2 picks a slice
  ;[p2BestSlice, slices] = removeBestSlice(2, slices)
  steps.push(makeStep(2, `chooses piece ${p2BestSlice.id}`, [p2BestSlice], true))

  // Keep track of who picked the trimmed piece. It's always P1 or P2.
  let trimmedPicker = null
  if (p2BestSlice === trimmedPiece) {
    trimmedPicker = 2
    // Trimmed piece already taken so P1 picks their favorite slice
    ;[p1BestSlice, slices] = removeBestSlice(1, slices)

    steps.push(makeStep(1, `chooses piece ${p1BestSlice.id}`, [p1BestSlice], true))
  } else {
    // Trimmed piece still available so P1 must pick it
    trimmedPicker = 1
    p1BestSlice = trimmedPiece
    remove(slices, trimmedPiece)

    steps.push(
      makeStep(
        1,
        `trimmed piece ${p1BestSlice.id} earlier and because it still remains they must choose it now`,
        [p1BestSlice],
        true
      )
    )
  }

  // P0 takes last slice
  p0BestSlice = slices.pop()

  steps.push(makeStep(0, `chooses remaining piece`, [p0BestSlice], true))

  // Assign slices to their agents
  let results = [p2BestSlice.assign(2), p1BestSlice.assign(1), p0BestSlice.assign(0)]

  // Assign trimmings and return results
  const trimmingsAssigned = assignTrimmings(
    trimming,
    trimmedPicker,
    preferences,
    steps,
    cakeSize
  )
  return {
    solution: [...results, ...trimmingsAssigned],
    steps,
  }
}

const assignTrimmings = (
  trimming: UnassignedSlice,
  trimmedPicker: number,
  preferences: Preferences,
  steps: Step[],
  cakeSize: number
): AssignedSlice[] => {
  console.log('Dividing trimming', trimming)
  const nonTrimmedPicker = trimmedPicker === 1 ? 2 : 1
  const cutterPrefs = preferences[nonTrimmedPicker]
  steps.push(
    makeStep(
      nonTrimmedPicker,
      `did not choose the trimmed piece earlier so gets to divide the trimmings`,
      [trimming]
    )
  )
  // Non-trimmed picker (P1 or P2) cuts trimming into three pieces
  const cut1 = findCutLineByPercent(cutterPrefs, 1 / 3, {
    startBound: trimming.start,
    endBound: trimming.end,
  })
  const cut2 = findCutLineByPercent(cutterPrefs, 2 / 3, {
    startBound: trimming.start,
    endBound: trimming.end,
  })
  const piece1 = cutSlice(preferences, trimming.start, cut1, 1, 'trimming')
  const piece2 = cutSlice(preferences, cut1, cut2, 2, 'trimming')
  const piece3 = cutSlice(preferences, cut2, trimming.end, 3, 'trimming')
  const trimmings = [piece1, piece2, piece3]

  steps.push(
    makeStep(
      nonTrimmedPicker,
      `divides the trimmings into thirds at ${makePercentage(
        cut1 / cakeSize,
        3
      )} and ${makePercentage(cut2 / cakeSize, 3)}`,
      trimmings
    )
  )

  console.log('Trimming divided into', trimmings)

  // Trimmed picker (P1 or P2) takes a slice
  const [trimmedPickerSlice, remainingSlices1] = removeBestSlice(trimmedPicker, trimmings)

  steps.push(
    makeStep(
      trimmedPicker,
      `chooses trimming ${trimmedPickerSlice.id}`,
      [trimmedPickerSlice],
      true
    )
  )

  // P0 takes a slice
  const [p0Slice, remainingSlices2] = removeBestSlice(0, remainingSlices1)

  steps.push(makeStep(0, `chooses trimming ${p0Slice.id}`, [p0Slice], true))

  // Non-trimmed picker takes a slice
  const nonTrimmedPickerSlice = remainingSlices2[0]

  steps.push(
    makeStep(
      nonTrimmedPicker,
      `chooses remaining trimming`,
      [nonTrimmedPickerSlice],
      true
    )
  )

  return [
    trimmedPickerSlice.assign(trimmedPicker),
    nonTrimmedPickerSlice.assign(nonTrimmedPicker),
    p0Slice.assign(0),
  ]
}
