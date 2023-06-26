import React, { useContext } from 'react'
import { GraphContext } from '../../GraphContext'
import { Segment } from '../../../types'
import { Bracket } from './Bracket'

interface BracketContainerProps {
  focused: boolean
  segment: Segment
  children?: React.ReactNode
}

export const BracketContainer = ({
  focused,
  segment: { start, end },
  children,
}: BracketContainerProps) => {
  const { xScale } = useContext(GraphContext)
  const slicesize = end - start

  return (
    <div
      style={{
        left: xScale(start),
        width: 'min-content',
        position: 'absolute',
        zIndex: focused ? 10 : 0,
      }}
    >
      <Bracket width={xScale(slicesize)} />
      {children}
    </div>
  )
}
