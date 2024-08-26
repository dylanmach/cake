import remove from 'lodash.remove'
import { Preferences, AssignedSlice, UnassignedSlice } from '../../types'
import { findCutLineByValue, findCutLineByPercent } from './getValue'
import { cutSlice, sortSlicesDescending, removeBestSlice } from './sliceUtils'
import { makePercentage } from '../../utils/formatUtils'
import { Step, makeStep } from './types'
import axios from 'axios'

// Note that this is written with a 0-based index, but descriptions of the
// Selfridge-Conway method use a 1-based index because that's, you know, normal.


export const piecewiseConstant = async (preferences: Preferences, cakeSize: number): 
Promise<{solution: AssignedSlice[]; steps: Step[]}> => {
  try {
    const response = await axios.post('//localhost:5000/api/piecewise_constant', { preferences, cakeSize })
    const division = response.data.division
    const assignment = response.data.assignment
    const segments =  response.data.segments
    const cutPositions =  response.data.cut_positions
    const agentsNumber = response.data.agents_number
    const steps: Step[] = []
    
    // const tempSlices = [
    //   cutSlice(preferences, 0, equipartition.left, 1),
    //   cutSlice(preferences, equipartition.left, equipartition.right, 2),
    //   cutSlice(preferences, equipartition.right, cakeSize, 3),
    // ]
    const segmentCuts = []
    const length = Object.keys(segments[0]).length
    for (let i = 0; i < length; i++){
        segmentCuts.push(cutSlice(preferences, segments[0][i].start, segments[0][i].end, i))
    } 

    steps.push(
      makeStep(
        4,
        `first divides the resource into segments`,
        segmentCuts
      )
    )

    if (agentsNumber === 3){ 
        const cutPositionOne = segments[0][cutPositions[0]]
        const cutPositionTwo = segments[0][cutPositions[1]]
        const cutSegmentOne = cutSlice(preferences, cutPositionOne.start, cutPositionOne.end, cutPositions[0])
        const cutSegmentTwo = cutSlice(preferences, cutPositionTwo.start, cutPositionTwo.end, cutPositions[1])
        const cutSegments = [cutSegmentOne, cutSegmentTwo]
        steps.push(
            makeStep(
                4,
                `identifies the segment containing the first cut as ${cutSegmentOne.id} and 
                the segment containing the second cut as ${cutSegmentTwo.id}`,
                cutSegments
            )
            )
        const slice1 = cutSlice(preferences, 0, division.left, 1)
        const slice2 = cutSlice(preferences, division.left, division.right, 2)
        const slice3 = cutSlice(preferences, division.right, cakeSize, 3)
        const finalSlices = [slice1, slice2, slice3]

        steps.push(
            makeStep(
              4,
              `finds an approximately envy-free division at slices ${makePercentage(
                division.left / cakeSize,3)} and ${makePercentage(division.right / cakeSize, 3)}`,
              finalSlices
            )
          )
        steps.push(makeStep(assignment[1], `is assigned piece ${slice1.id}`, [slice1], true))
        steps.push(makeStep(assignment[2], `is assigned piece ${slice2.id}`, [slice2], true))
        steps.push(makeStep(assignment[3], `is assigned piece ${slice3.id}`, [slice3], true))

        return { solution: [slice1.assign(assignment[1]), slice2.assign(assignment[2]),
                slice3.assign(assignment[3])], steps};

        
    }

    if (agentsNumber === 4){ 
        const cutPositionOne = segments[0][cutPositions[0]]
        const cutPositionTwo = segments[0][cutPositions[1]]
        const cutPositionThree = segments[0][cutPositions[2]]
        const cutSegmentOne = cutSlice(preferences, cutPositionOne.start, cutPositionOne.end, cutPositions[0])
        const cutSegmentTwo = cutSlice(preferences, cutPositionTwo.start, cutPositionTwo.end, cutPositions[1])
        const cutSegmentThree = cutSlice(preferences, cutPositionThree.start, cutPositionThree.end, cutPositions[2])
        const cutSegments = [cutSegmentOne, cutSegmentTwo, cutSegmentThree]
        steps.push(
            makeStep(
                4,
                `identifies the segment containing the first cut as ${cutSegmentOne.id},
                the segment containing the second cut as ${cutSegmentTwo.id}, and the segment
                containing the third cut as ${cutSegmentThree.id}`,
                cutSegments
            )
            )
        const slice1 = cutSlice(preferences, 0, division.left, 1)
        const slice2 = cutSlice(preferences, division.left, division.middle, 2)
        const slice3 = cutSlice(preferences, division.middle, division.right, 3)
        const slice4 = cutSlice(preferences, division.right, cakeSize, 4)
        const finalSlices = [slice1, slice2, slice3, slice4]

        steps.push(
            makeStep(
              4,
              `finds an approximately envy-free division at slices ${makePercentage(
                division.left / cakeSize,3)}, ${makePercentage(
                division.middle / cakeSize,3)} and ${makePercentage(division.right / cakeSize, 3)}`,
              finalSlices
            )
          )
        steps.push(makeStep(assignment[1], `is assigned piece ${slice1.id}`, [slice1], true))
        steps.push(makeStep(assignment[2], `is assigned piece ${slice2.id}`, [slice2], true))
        steps.push(makeStep(assignment[3], `is assigned piece ${slice3.id}`, [slice3], true))
        steps.push(makeStep(assignment[4], `is assigned piece ${slice4.id}`, [slice4], true))

        return { solution: [slice1.assign(assignment[1]), slice2.assign(assignment[2]),
                slice3.assign(assignment[3]), slice4.assign(assignment[4])], steps};

    }
    
  } catch (error) {
    console.error('Error calling API:', error);
    throw error; // Handle error as needed
  }
};
