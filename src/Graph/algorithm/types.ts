import { Portion, Slice } from "../../types";

export type AlgoName = 'cutAndChoose' | 'selfridgeConway' | 'barbanelBrams' ;

export interface Algorithm {
  key: AlgoName
  name: string
  numAgentsText: string
  minAgents: number
  maxAgents: number
  shortDescription: string
  link: string
}

export type Result = { solution: Portion[], steps: Step[]}

// The form of a step is [agent number (0-indexed), action taken]
export interface Step {
  actor: number
  action: string
  pieces: Slice[]
  assign: boolean
}
export const makeStep = (actor: number, action: string, pieces: Slice[] = [], assign = false): Step => ({
  actor,
  action,
  pieces,
  assign,
})


export const Algorithms: Record<AlgoName, Algorithm> = {
  cutAndChoose: {
    key: 'cutAndChoose',
    name: 'Cut and Choose',
    numAgentsText: '2 people',
    minAgents: 2,
    maxAgents: 2,
    shortDescription:
      'A simple method for envy-free division between two people. One cuts, the other chooses.',
    link: '/learn/7',
  },
  selfridgeConway: {
    key: 'selfridgeConway',
    name: 'Selfridge-Conway',
    numAgentsText: '3 people',
    minAgents: 3,
    maxAgents: 3,
    shortDescription:
      'A method for envy-free division between three people. Maximum of five cuts.',
    link: '/learn/13',
  },
  barbanelBrams: {
    key: 'barbanelBrams',
    name: 'Barbanel-Brams',
    numAgentsText: '3 people',
    minAgents: 3,
    maxAgents: 3,
    shortDescription:
      'A method for envy-free division between three people. Maximum of two cuts.',
    link: '/TBD',
  },
}
