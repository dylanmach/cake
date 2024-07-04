import remove from 'lodash.remove'
import { Preferences, AssignedSlice, UnassignedSlice } from '../../types'
import { findCutLineByValue, findCutLineByPercent } from './getValue'
import { cutSlice, sortSlicesDescending, removeBestSlice } from './sliceUtils'
import { makePercentage } from '../../utils/formatUtils'
import { Step, makeStep } from './types'
import axios from 'axios'

// Note that this is written with a 0-based index, but descriptions of the
// Selfridge-Conway method use a 1-based index because that's, you know, normal.


export const branzeiNisan = async (preferences: Preferences, cakeSize: number): 
Promise<{solution: AssignedSlice[]; steps: Step[]}> => {
  try {
    const response = await axios.post('/api/three_agent', { preferences, cakeSize });
    const steps: Step[] = []
    const division = response.data.division
    const assignment = response.data.assignment
    const slice1 = cutSlice(preferences, 0, division.left, 1)
    const slice2 = cutSlice(preferences, division.left, division.right, 2)
    const slice3 = cutSlice(preferences, division.right, cakeSize, 3)
    return { solution: [slice1.assign(assignment[1]), slice2.assign(assignment[2]),
                        slice3.assign(assignment[3])], steps};
  } catch (error) {
    console.error('Error calling API:', error);
    throw error; // Handle error as needed
  }
};
//export const barbanelBrams = (
  //preferences: Preferences,
//   cakeSize: number
// ): { solution: AssignedSlice[]; steps: Step[] } => {
//   if (preferences.length !== 3) {
//     throw new Error('Barbanel-Brams only works with three agents')
//   }
//   const steps: Step[] = []
//   let p0BestSlice = null
//   let p1BestSlice = null
//   let p2BestSlice = null
//   let slices = []

  
//   return {
//     solution: [...results],
//     steps,
//   }
// }

