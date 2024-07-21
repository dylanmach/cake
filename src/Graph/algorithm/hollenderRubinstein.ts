import remove from 'lodash.remove'
import { Preferences, AssignedSlice, UnassignedSlice } from '../../types'
import { findCutLineByValue, findCutLineByPercent } from './getValue'
import { cutSlice, sortSlicesDescending, removeBestSlice } from './sliceUtils'
import { makePercentage } from '../../utils/formatUtils'
import { Step, makeStep } from './types'
import axios from 'axios'

// Note that this is written with a 0-based index, but descriptions of the
// Selfridge-Conway method use a 1-based index because that's, you know, normal.


export const hollenderRubinstein = async (preferences: Preferences, cakeSize: number): 
Promise<{solution: AssignedSlice[]; steps: Step[]}> => {
  try {
    const response = await axios.post('/api/four_agent', { preferences, cakeSize });
    const steps: Step[] = []
    const division = response.data.division
    const assignment = response.data.assignment
    const equipartition = response.data.equipartition
    const condition = response.data.condition 
    const slices = response.data.slices                
    const indifferent_agent = response.data.indifferent_agent 


    const tempSlice1 = cutSlice(preferences, 0, equipartition.left, 1)
    const tempSlice2 = cutSlice(preferences, equipartition.left, equipartition.middle, 2)
    const tempSlice3 = cutSlice(preferences, equipartition.middle, equipartition.right, 3)
    const tempSlice4 = cutSlice(preferences, equipartition.right, cakeSize, 4)
    const tempSlices = [tempSlice1, tempSlice2, tempSlice3, tempSlice4]
    if (condition[0] === 0){
      steps.push(
        makeStep(
          0,
          `divides the resource into quarters at ${makePercentage(
            equipartition.left / cakeSize,
            3
          )}, ${makePercentage(equipartition.middle / cakeSize, 3)}, and 
          ${makePercentage(equipartition.right / cakeSize, 3)}. This is an 
          approximately envy-free division, so the algorithm terminates here`,
          tempSlices
        )
      )

      steps.push(makeStep(assignment[1], `is assigned piece ${tempSlice1.id}`, [tempSlice1], true))
      steps.push(makeStep(assignment[2], `is assigned piece ${tempSlice2.id}`, [tempSlice2], true))
      steps.push(makeStep(assignment[3], `is assigned piece ${tempSlice3.id}`, [tempSlice3], true))
      steps.push(makeStep(assignment[4], `is assigned piece ${tempSlice4.id}`, [tempSlice4], true))
      return { solution: [tempSlice1.assign(assignment[1]), tempSlice2.assign(assignment[2]),
                        tempSlice3.assign(assignment[3]), tempSlice4.assign(assignment[4])], steps};
    }
    else{
      steps.push(
        makeStep(
          0,
          `divides the resource into quarters at ${makePercentage(
            equipartition.left / cakeSize,
            3
          )}, ${makePercentage(equipartition.middle / cakeSize, 3)}, and 
          ${makePercentage(equipartition.right / cakeSize, 3)}`,
          tempSlices
        )
      )
      const allSlices: number[] = [1, 2, 3, 4]
      const remainingSlices: number[] = allSlices.filter(item => !slices.includes(item));
      const slice1 = cutSlice(preferences, 0, division.left, 1)
      const slice2 = cutSlice(preferences, division.left, division.middle, 2)
      const slice3 = cutSlice(preferences, division.middle, division.right, 3)
      const slice4 = cutSlice(preferences, division.right, cakeSize, 4)
      const finalSlices = [slice1, slice2, slice3, slice4]
      if (condition[0] === 1){
        steps.push(
          makeStep(
            0,
            `The algorithm terminates at the approximately envy-free division at slices ${makePercentage(
              division.left / cakeSize,
              3
            )}, ${makePercentage(division.middle / cakeSize, 3)}, and 
            ${makePercentage(division.right / cakeSize, 3)}. This division satisfies condition A`,
            finalSlices
          )
        )
        steps.push(
          makeStep(
            0,
            `is indifferent between slices ${remainingSlices[0]}, ${remainingSlices[1]}, and 
            ${remainingSlices[2]}`,
            [finalSlices[remainingSlices[0]-1], finalSlices[remainingSlices[1]-1],
            finalSlices[remainingSlices[2]-1]]
          )
        )
        steps.push(
          makeStep(
            0,
            `At least two agents weakly prefer slice ${slices[0]}`,
            [finalSlices[slices[0]-1]]
          )
        )
        steps.push(makeStep(assignment[1], `is assigned piece ${slice1.id}`, [slice1], true))
        steps.push(makeStep(assignment[2], `is assigned piece ${slice2.id}`, [slice2], true))
        steps.push(makeStep(assignment[3], `is assigned piece ${slice3.id}`, [slice3], true))
        steps.push(makeStep(assignment[4], `is assigned piece ${slice4.id}`, [slice4], true))
        return { solution: [slice1.assign(assignment[1]), slice2.assign(assignment[2]),
                            slice3.assign(assignment[3]), slice4.assign(assignment[4])], steps};
      }
      if (condition[0] === 2){
        steps.push(
          makeStep(
            4,
            `The algorithm terminates at the approximately envy-free division at slices ${makePercentage(
              division.left / cakeSize,
              3
            )}, ${makePercentage(division.middle / cakeSize, 3)}, and 
            ${makePercentage(division.right / cakeSize, 3)}. This division satisfies condition B`,
            finalSlices
          )
        )
        steps.push(
          makeStep(
            0,
            `is indifferent between slices ${remainingSlices[0]} and ${remainingSlices[1]}`,
            [finalSlices[remainingSlices[0]-1], finalSlices[remainingSlices[1]-1]]
          )
        )
        steps.push(
          makeStep(
            indifferent_agent[0],
            `is indifferent between slices ${slices[0]} and ${slices[1]}. These
            slices are each weakly preferred by at least one other agent`,
            [finalSlices[slices[0]-1], finalSlices[slices[1]-1]]
          )
        )
        steps.push(makeStep(assignment[1], `is assigned piece ${slice1.id}`, [slice1], true))
        steps.push(makeStep(assignment[2], `is assigned piece ${slice2.id}`, [slice2], true))
        steps.push(makeStep(assignment[3], `is assigned piece ${slice3.id}`, [slice3], true))
        steps.push(makeStep(assignment[4], `is assigned piece ${slice4.id}`, [slice4], true))
        return { solution: [slice1.assign(assignment[1]), slice2.assign(assignment[2]),
                            slice3.assign(assignment[3]), slice4.assign(assignment[4])], steps};
      }
    }
  } catch (error) {
    console.error('Error calling API:', error);
    throw error; // Handle error as needed
  }
};