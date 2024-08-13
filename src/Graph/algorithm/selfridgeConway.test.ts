import { selfridgeConway } from './selfridgeConway'
import { genFlatSeg, testIfEnvyFree, genRandomSegs, genUniformRandomFlatSegs} from './testUtil'
import { writeFileSync, appendFileSync } from 'fs';


test('splits a "no trimming needed" uniform evaluation cake into even (almost) thirds', () => {
  // Use a cake size of 90 so it's evenly divisible into thirds.
  const person0 = [genFlatSeg(0, 90, 10)] // 900
  const person1 = [genFlatSeg(0, 90, 10)] // 900
  const person2 = [genFlatSeg(0, 90, 10)] // 900
  const result = selfridgeConway([person0, person1, person2], 90).solution

  expect(result).toHaveLength(3)
  // not checking owner because order doesn't matter
  expect(result).toContainEqual(
    expect.objectContaining({ start: 0, end: 30, values: [300, 300, 300] })
  )
  expect(result).toContainEqual(
    expect.objectContaining({ start: 30, end: 60, values: [300, 300, 300]  })
  )
  expect(result).toContainEqual(
    expect.objectContaining({ start: 60, end: 90, values: [300, 300, 300]  })
  )
  testIfEnvyFree(3, result)
})

test('splits a "no trimming needed" asymmetrical evaluation cake fairly', () => {
  // Person 0 has no preference so will divide evenly
  const person0 = [genFlatSeg(0, 90, 10)] // 900
  // Person 1 will have a tie for largest so won't trim
  const person1 = [genFlatSeg(0, 30, 5), genFlatSeg(30, 90, 10)] // 750
  // Person 2 prefers the last third
  const person2 = [genFlatSeg(0, 60, 5), genFlatSeg(60, 90, 10)] // 600
  const result = selfridgeConway([person0, person1, person2], 90).solution

  expect(result).toHaveLength(3)
  expect(result).toContainEqual(
    expect.objectContaining({ start: 0, end: 30, owner: 0, values: [300, 150, 150]  })
  )
  expect(result).toContainEqual(
    expect.objectContaining({ start: 30, end: 60, owner: 1, values: [300, 300, 150]  })
  )
  expect(result).toContainEqual(
    expect.objectContaining({ start: 60, end: 90, owner: 2, values: [300, 300, 300]  })
  )
  testIfEnvyFree(3, result)
})

test('splits a simple "trimming needed" cake fairly', () => {
  const person0 = [genFlatSeg(0, 30, 10), genFlatSeg(30, 60, 5), genFlatSeg(60, 90, 10)]
  const person1 = [genFlatSeg(0, 90, 10)]
  const person2 = [genFlatSeg(0, 60, 5), genFlatSeg(60, 90, 10)]
  const result = selfridgeConway([person0, person1, person2], 90).solution

  testIfEnvyFree(3, result)
})

/* Walkthrough of above example. There are a lot of ties in this example
  so feel free to make a better one.

  initial cut, post-sorting by P1
  [
    { end: 65, start: 25, values: [250, 400, 225] },
    { end: 25, start: 0,  values: [250, 250, 125] },
    { end: 90, start: 65, values: [250, 250, 250] }
  ]

  P1 post trimming (slice 0 trimmed down, see the hole from 25-40)
  [
    { end: 65, start: 40, values: [150, 250, 150] },
    { end: 25, start: 0, values: [250, 250, 125] },
  ]

  P2 chooses { end: 90, start: 65, values: [250, 250, 250] },
  leaves the following
  [
    { end: 65, start: 40, values: [150, 250, 150] },
    { end: 25, start: 0, values: [250, 250, 125] }
  ]

  P1 must choose the piece they trimmed,
  so takes { end: 65, start: 40, values: [150, 250, 150] },
  and leaves the following
  [{ end: 65, start: 40, values: [150, 250, 150] }]

  P0 takes the last piece

  then the trimmings are split by P2 (the non-trimmed piece picker)
  [
    { end: 30, start: 25, values: [50, 50, 25] },
    { end: 35, start: 30, values: [25, 50, 25] },
    { end: 40, start: 35, values: [25, 50, 25] }
  ]

  P1 takes a slice
  { start: 25, end: 30, values: [50, 50, 25]}
  
  Then P0
  { start: 30, end: 35, values: [25, 50, 25] }
  
  P2 gets the remaining
  { end: 40, start: 35, values: [25, 50, 25] }
*/

// The zero-value segment issue stumped me for a long time.
// The solution is that you are allow to have 0-width, "empty" slices
// even though they have zero value
test('splits a cake containing 0 value evaluations', () => {
  const person0 = [genFlatSeg(0, 60, 10), genFlatSeg(60, 90, 0)]
  const person1 = [genFlatSeg(0, 60, 0), genFlatSeg(60, 90, 10)]
  const person2 = [genFlatSeg(0, 90, 10)]
  const result = selfridgeConway([person0, person1, person2], 90).solution

  testIfEnvyFree(3, result)
})

test('splits an almost valueless cake', () => {
  const person0 = [genFlatSeg(0, 5, 10), genFlatSeg(5, 90, 0)]
  const person1 = [genFlatSeg(0, 89, 0), genFlatSeg(89, 90, 10)]
  const person2 = [genFlatSeg(0, 50, 0), genFlatSeg(50, 51, 1), genFlatSeg(51, 90, 0)]
  const result = selfridgeConway([person0, person1, person2], 90).solution

  testIfEnvyFree(3, result)
})

// This test is non-deterministic so run it many times
// to ensure edge cases are (probably) covered.
test('splits randomly generated preferences fairly', () => {
  const segs = [genRandomSegs(100), genRandomSegs(100), genRandomSegs(100)]
  const result = selfridgeConway(segs, 100).solution
  testIfEnvyFree(3, result)
})

test('splits randomly generated preferences fairly', () => {
  const csvFile = 'selfridge_conway_runtime_results.csv';

  // Write the header of the CSV file
  //writeFileSync(csvFile, 'cake size,Execution Time (s)\n');

  for (let i = 1; i <= 20; i++) { // Example loop for 10 tests
      const cakeSize = 320000

      const segs = [genUniformRandomFlatSegs(cakeSize), genUniformRandomFlatSegs(cakeSize), 
                    genUniformRandomFlatSegs(cakeSize)]
      
      const startTime = performance.now();
      // Simulate some test or process
      selfridgeConway(segs, cakeSize);

      const endTime = performance.now();
      const duration = (endTime - startTime) / 1000; // Convert milliseconds to seconds

      // Write the result to the CSV file
      appendFileSync(csvFile, `${cakeSize},${duration}\n`);

      // Optional: Print to console for verification
      console.log(`Test ${i}: ${duration} s`);
  }
})
