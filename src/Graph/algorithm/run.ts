import { AlgoName, Result, Step } from './types'
import { Preferences, AssignedSlice, Portion } from '../../types'
import { validateSegments } from './validation'
import { cutAndChoose } from './cutAndChoose'
import { selfridgeConway } from './selfridgeConway'
import { barbanelBrams } from './barbanelBrams'
import { getTotalValue } from './getValue'

export const runDivisionAlgorithm = async (
  preferences: Preferences,
  algo: AlgoName,
  cakeSize
): Promise<Result> => {
  const numPeople = preferences.length
  console.log(`Running ${algo}...`)
  console.log('Cake size:', cakeSize)
  console.log('Preferences:', preferences)

  // simple error checking
  validateSegments(preferences, cakeSize)

  // may want to add more checks here.
  // The UI validates enough but if people upload their own data,
  // who knows what could happen...

  let result: null | { solution: AssignedSlice[]; steps: Step[] } = null
  switch (algo) {
    case 'cutAndChoose':
      result = cutAndChoose(preferences, cakeSize)
      break
    case 'selfridgeConway':
      result = selfridgeConway(preferences, cakeSize)
      break
    //case 'barbanelBrams':
    //  result = barbanelBrams(preferences, cakeSize)
    //  break
    // NOTE FOR FUTURE DEVS
    // If server-side methods are implemented,
    // be sure to `await` the asynchronous response as shown here:
    //
    // case 'some server-side method':
    //   result = await method(preferences, cakeSize)
    //   break
    default:
      throw new Error(`Algorithm not implemented: ${algo}`)
  }
  console.log('results', result)

  // Combine all slices assigned to each user into one "Portion"
  const totalValues = preferences.map(getTotalValue)

  const portions = result.solution.reduce((acc, slice) => {
    const owner = slice.owner
    if (!acc[owner]) {
      acc[owner] = { owner, percentValues: Array(numPeople).fill(0), edges: [] }
    }
    acc[owner].edges.push([slice.start, slice.end])
    acc[owner].percentValues = slice.values.map(
      (val, i) => acc[owner].percentValues[i] + val / totalValues[i]
    )
    return acc
  }, Array<Portion>(numPeople))

  // Sort edges by start
  portions.forEach((portion) => portion.edges.sort((a, b) => a[0] - b[0]))
  console.log('Portions', portions)
  return { solution: portions, steps: result.steps }
}
