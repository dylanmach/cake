import { Segment, AssignedSlice } from '../../types'

export const halfwayPointOfTriangleArea = 70.710678

let id = 0
export const genFlatSeg = (
  start: number,
  end: number,
  value: number
): Segment => {
  return {
    id: ++id,
    start,
    end,
    startValue: value,
    endValue: value,
  }
}

export const genSlopedSeg = (
  start: number,
  end: number,
  startValue: number,
  endValue: number
): Segment => {
  return {
    id: ++id,
    start,
    end,
    startValue,
    endValue,
  }
}

/**
 * Generates pseudo-random whole numbers between 0 and `max`
 */
const rand = (max: number) => Math.floor(Math.random() * (max + 1))

/**
 * Generates a set of continuous, random segments fitting a `cakeSize` cake. 
 * This can represent the preferences for one person.
 */
export const genRandomSegs = (cakeSize: number) => {
  const segs = []
  const numToGen = 1 + rand(4)
  const segWidth = cakeSize / numToGen // make an even split now

  let lastEnd = 0
  for (let curr = 1; curr <= numToGen; curr++) {
    if (rand(1) === 1) {
      segs.push(genFlatSeg(lastEnd, lastEnd + segWidth, rand(10)))
    } else {
      segs.push(genSlopedSeg(lastEnd, lastEnd + segWidth, rand(10), rand(10)))
    }
    lastEnd += segWidth
  }
  return segs
}

export const genUniformRandomFlatSegs = (cakeSize: number) => {
  const segs = []
  const segWidth = 1 // make an even split now

  let lastEnd = 0
  for (let curr = 1; curr <= cakeSize; curr++) {
    segs.push(genFlatSeg(lastEnd, lastEnd + segWidth, Math.random() * 10))
    lastEnd += segWidth
  }
  return segs
}

export const testIfEnvyFree = (numPeople: number, result: AssignedSlice[]) => {
  for (let a = 0; a < numPeople; a++) {
    // Using agent `a`'s evaluations, collect each person's slice values into an array.
    // This does collect an agent's own slices but that's fine.
    const totalValues = result.reduce((acc, slice) => {
      acc[slice.owner] += slice.values[a]
      return acc
    }, new Array(numPeople).fill(0))

    // The value of `a`'s slices
    const obtainedValue = totalValues[a]

    // We can't get to 100% accuracy when using floating point math
    // but 12 decimal places is still very good
    const fudgeFactor = 1e-12
    // Assert that all other agents slice total value
    // is worth less (to person `a`) than their own slice.
    totalValues.forEach((value, i) => {
      expect(
        value - fudgeFactor,
        `Person ${a} envies person ${i}'s slices`
      ).toBeLessThanOrEqual(obtainedValue)
    })
  }
}
