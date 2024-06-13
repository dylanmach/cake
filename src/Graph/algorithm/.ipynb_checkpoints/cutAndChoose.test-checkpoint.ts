import { cutAndChoose } from './cutAndChoose'
import {
  genFlatSeg,
  genSlopedSeg,
  testIfEnvyFree,
  halfwayPointOfTriangleArea,
  genRandomSegs,
} from './testUtil'

const cakeSize = 100

test('splits a uniform flat value graph evenly in half', () => {
  const person1 = [genFlatSeg(0, 100, 10)] // 1000
  const person2 = [genFlatSeg(0, 100, 10)] // 1000
  const result = cutAndChoose([person1, person2], cakeSize).solution
  expect(result).toHaveLength(2)
  // Each agent values the cake uniformly for a total of 1000 value.
  // The results should be an even 500/500 split.
  // Actual order doesn't matter but it's difficult to test that.
  expect(result[0]).toMatchObject({ owner: 1, start: 0, end: 50, values: [500, 500] })
  expect(result[1]).toMatchObject({ owner: 0, start: 50, end: 100, values: [500, 500] })
  testIfEnvyFree(2, result)
})

test('splits a seesaw-like graph in an envy-free way', () => {
  const person1 = [genFlatSeg(0, 50, 10), genFlatSeg(50, 100, 5)] // 750, halfway point is 37.5%
  const person2 = [genFlatSeg(0, 50, 5), genFlatSeg(50, 100, 10)] // 750, halfway point is 67.5%
  const result = cutAndChoose([person1, person2], cakeSize).solution
  expect(result).toHaveLength(2)
  // The slices should be 375 value on both sides for person 0,
  // but the second slice is better for person 1.
  expect(result[0]).toMatchObject({ owner: 0, start: 0, end: 37.5 })
  expect(result[1]).toMatchObject({
    owner: 1,
    start: 37.5,
    end: 100,
  })
  testIfEnvyFree(2, result)
})

test('splits a seesaw-like sloped graph in an envy-free way', () => {
  const person1 = [genSlopedSeg(0, 100, 10, 0)] // 500, halfway point is ~30%
  const person2 = [genSlopedSeg(0, 100, 0, 10)] // 500, halfway point is ~70%
  const result = cutAndChoose([person1, person2], cakeSize).solution
  expect(result).toHaveLength(2)
  // We get a weird `TypeError: val.toAsymmetricMatcher is not a function` bug when testing
  // with `toMatchObject` and `expect.closeTo` so doing things the verbose way.
  expect(result[0].owner).toBe(0)
  expect(result[0].end).toBeCloseTo(100 - halfwayPointOfTriangleArea)
  expect(result[0].values[0]).toBeCloseTo(250)

  expect(result[1].owner).toBe(1)
  testIfEnvyFree(2, result)
})

// This case fails if we only slice on whole numbers
test('splits a tricky case in an envy-free way', () => {
  const person1 = [genFlatSeg(0, 40, 1), genFlatSeg(40, 65, 8.3), genFlatSeg(65, 100, 1)]
  const person2 = [
    genFlatSeg(0, 30, 4),
    genFlatSeg(30, 50, 8),
    genFlatSeg(50, 70, 6),
    genFlatSeg(70, 90, 8),
    genFlatSeg(90, 100, 0),
  ]
  const result = cutAndChoose([person1, person2], cakeSize).solution
  expect(result).toHaveLength(2)
  testIfEnvyFree(2, result)
})

// This case fails if we only slice on whole numbers
test('splits a tricky sloped case in an envy-free way', () => {
  const person1 = [genFlatSeg(0, 45, 3.5), genSlopedSeg(45, 100, 7.5, 6.5)]
  const person2 = [genSlopedSeg(0, 60, 8, 9.5), genSlopedSeg(60, 100, 2.5, 5.5)]
  const result = cutAndChoose([person1, person2], cakeSize).solution
  expect(result).toHaveLength(2)
  testIfEnvyFree(2, result)
})

test('splits randomly generated preferences fairly', () => {
  const segs = [genRandomSegs(cakeSize), genRandomSegs(cakeSize)]
  const result = cutAndChoose(segs, cakeSize).solution
  testIfEnvyFree(2, result)
})

test('splits randomly generated preferences fairly on a smaller cake size', () => {
  const smallCake = 3
  const segs = [genRandomSegs(smallCake), genRandomSegs(smallCake)]
  const result = cutAndChoose(segs, smallCake).solution
  testIfEnvyFree(2, result)
})
