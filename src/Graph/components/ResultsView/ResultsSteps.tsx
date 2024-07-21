import { AlgoName, Algorithms, Result } from '../../algorithm/types'
import { useContext } from 'react'
import { GraphContext } from '../../GraphContext'
import { getAgentColor } from '../../../colors'
import { Slice } from '../../../types'
import { ResultsContainer } from './ResultsContainer'

interface ResultsStepsProps {
  algoUsed: AlgoName
  result: Result
}

// This should be more centrally located and less fragile
const getText = (piece: Slice) => {
  if (piece.note === 'trimming' && piece.id === 4) {
    return 'T'
  }
  return piece.id
}

export const ResultsSteps = ({ algoUsed, result }: ResultsStepsProps) => {
  const { width, height, xScale, names = [null, null, null, null, "The Algorithm"] } = useContext(GraphContext)
console.log('results',result)
  return (
    <ResultsContainer title="Algorithm Steps" id="steps">
      <h3>{Algorithms[algoUsed].name + ' Steps'}</h3>
      <ol style={{ fontSize: 18, margin: 0 }}>
        {result.steps.map(({ actor, action, pieces, assign }) => (
          <li key={action}>
            <div>
              <strong>{names?.[actor] ?? `Person ${actor + 1}`}:</strong> {action}.
            </div>

            {pieces ? (
              <svg width={width} height={height}>
                {pieces.map((piece) => {
                  const { start, end } = piece
                  const x = xScale(start)
                  const width = xScale(end) - xScale(start)
                  return (
                    <g key={x}>
                      <rect
                        x={x}
                        width={width}
                        y={0}
                        height={height}
                        fill={assign ? getAgentColor(actor) : '#ddd'}
                        strokeWidth={1}
                        stroke="#555"
                      />
                      <text
                        textAnchor="middle"
                        dominantBaseline="central"
                        x={x + width / 2}
                        y="50%"
                      >
                        {getText(piece)}
                      </text>
                    </g>
                  )
                })}
                <rect
                  x={0.5}
                  y={0.5}
                  width={width - 1}
                  height={height - 1}
                  stroke="#555"
                  fill="none"
                  strokeWidth={1}
                />
              </svg>
            ) : null}
          </li>
        ))}
      </ol>
    </ResultsContainer>
  )
}
